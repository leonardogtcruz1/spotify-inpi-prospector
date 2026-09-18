#!/usr/bin/env python3
"""
Servidor Web FastAPI para Automação de Planilhas Spotify & INPI
"""

import os
import sys
import glob
import json
import time
import uuid
import shutil
import asyncio
import unicodedata
import threading
from datetime import datetime
from collections import Counter
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from modules.spotify_service import (
    load_tracks_from_xlsx,
    load_tracks_from_csv,
    load_existing_artist_links,
    get_artist_spotify_info,
    get_artists_from_track_page,
    load_tracks_from_playlist,
    extract_artist_id,
    load_spotify_credentials,
    save_spotify_credentials
)
from modules.social_service import (
    enrich_artist_social_metrics,
    load_known_socials_from_excel
)
from modules.inpi_service import (
    load_known_marcas_from_excel,
    build_inpi_direct_url,
    init_inpi_session,
    search_inpi_live
)
from modules.excel_builder import build_final_workbook

# Configuração de diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IS_VERCEL = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
OUTPUT_DIR = "/tmp/output" if IS_VERCEL else os.path.join(BASE_DIR, "output")
UPLOAD_DIR = "/tmp/uploads" if IS_VERCEL else os.path.join(BASE_DIR, "uploads")
WEB_DIR = os.path.join(BASE_DIR, "web")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
if not IS_VERCEL:
    os.makedirs(WEB_DIR, exist_ok=True)


app = FastAPI(title="Spotify & INPI Prospector Web API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Armazenamento em memória de jobs e filas de SSE
jobs: Dict[str, Dict[str, Any]] = {}
job_subscribers: Dict[str, List[Any]] = {}
job_lock = threading.Lock()


def normalize_text(text: str) -> str:
    if not text:
        return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('ASCII').strip().lower()


def safe_json_dumps(obj: Any) -> str:
    """Serializa com segurança qualquer objeto/dicionário para JSON, convertendo datetimes e tipos especiais"""
    return json.dumps(obj, default=str, ensure_ascii=False)


def broadcast_event(job_id: str, event_type: str, data: Any):
    """Envia um evento SSE para todos os clientes conectados ao job_id de forma thread-safe"""
    payload = {
        "event": event_type,
        "data": data,
        "timestamp": time.time()
    }
    with job_lock:
        subscribers = job_subscribers.get(job_id, [])
        for item in list(subscribers):
            try:
                if isinstance(item, tuple):
                    loop, q = item
                    if loop.is_running():
                        loop.call_soon_threadsafe(q.put_nowait, payload)
                    else:
                        q.put_nowait(payload)
                else:
                    item.put_nowait(payload)
            except Exception:
                pass


def append_job_log(job: Dict[str, Any], message: str):
    """Adiciona uma linha de log ao job e emite via SSE"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted = f"[{timestamp}] {message}"
    job["logs"].append(formatted)
    broadcast_event(job["id"], "log", {"line": formatted})


def run_pipeline_sync(job_id: str, target_type: str, target_value: str, skip_live_inpi: bool = False):
    """Execução síncrona do pipeline de extração e enriquecimento"""
    job = jobs[job_id]
    job["status"] = "running"
    broadcast_event(job_id, "status", {"status": "running"})

    try:
        append_job_log(job, "Iniciando pipeline de automação...")
        tracks = []
        playlist_title = "Playlist Spotify"
        existing_spotify_links = {}

        # 1. Carregamento das faixas
        job["progress"] = {"step": 1, "step_name": "Carregando músicas e artistas", "percent": 5}
        broadcast_event(job_id, "progress", job["progress"])

        if target_type == "playlist":
            append_job_log(job, f"Conectando à playlist: {target_value}")
            cid, csec = load_spotify_credentials()
            try:
                playlist_title, tracks = load_tracks_from_playlist(
                    target_value,
                    client_id=cid,
                    client_secret=csec,
                    interactive=False
                )
                append_job_log(job, f"Playlist '{playlist_title}' carregada ({len(tracks)} faixas).")
            except Exception as e:
                append_job_log(job, f"Aviso ao carregar playlist: {e}")
                raise e

        elif target_type == "file":
            file_path = target_value
            append_job_log(job, f"Lendo arquivo: {os.path.basename(file_path)}")
            existing_spotify_links = load_existing_artist_links(file_path)
            if file_path.endswith('.csv'):
                tracks = load_tracks_from_csv(file_path)
            else:
                tracks = load_tracks_from_xlsx(file_path)
            base_name = os.path.basename(file_path).replace('.xlsx', '').replace('.csv', '')
            if base_name:
                playlist_title = base_name
            append_job_log(job, f"Arquivo carregado com sucesso: {len(tracks)} faixas.")

        job["playlist_title"] = playlist_title
        job["summary"]["total_tracks"] = len(tracks)

        # 2. Histórico de marcas e redes sociais
        job["progress"] = {"step": 2, "step_name": "Verificando histórico de marcas e redes sociais", "percent": 15}
        broadcast_event(job_id, "progress", job["progress"])
        append_job_log(job, "Consultando histórico em planilhas anteriores...")

        known_marcas = {}
        known_socials = {}
        historical_files = [f for f in glob.glob(os.path.join(BASE_DIR, "*.xlsx")) + glob.glob(os.path.join(OUTPUT_DIR, "*.xlsx")) if not os.path.basename(f).startswith("~$")]
        for f in historical_files:
            loaded_m = load_known_marcas_from_excel(f)
            known_marcas.update(loaded_m)
            loaded_s = load_known_socials_from_excel(f)
            known_socials.update(loaded_s)

        append_job_log(job, f"Histórico: {len(known_marcas)} marcas e {len(known_socials)} redes sociais encontradas.")

        # 3. Identificação de Artistas e Contagem
        job["progress"] = {"step": 3, "step_name": "Mapeando artistas e IDs do Spotify", "percent": 25}
        broadcast_event(job_id, "progress", job["progress"])

        artist_counts = Counter()
        artist_spotify_ids = dict(existing_spotify_links)
        artist_tracks_map = {}

        for t in tracks:
            tid = t.get('track_id')
            for a in t.get('artists', []):
                aname = a.get('name', '').strip()
                if not aname:
                    continue
                artist_counts[aname] += 1
                norm = normalize_text(aname)
                if tid and norm not in artist_tracks_map:
                    artist_tracks_map[norm] = tid
                if a.get('id') and norm not in artist_spotify_ids:
                    artist_spotify_ids[norm] = a.get('id')

        unique_artists = sorted(artist_counts.keys(), key=lambda s: normalize_text(s))
        total_artists = len(unique_artists)
        job["summary"]["total_artists"] = total_artists
        append_job_log(job, f"{total_artists} artistas únicos identificados.")

        # Resolução de IDs de faixas
        unique_track_ids = list(dict.fromkeys([t.get('track_id') for t in tracks if t.get('track_id')]))
        resolved_track_cache = {}
        unresolved_artists = [a for a in unique_artists if normalize_text(a) not in artist_spotify_ids]

        if unresolved_artists:
            append_job_log(job, f"Resolvendo IDs do Spotify de {len(unresolved_artists)} artistas através das faixas...")
            for tid in unique_track_ids:
                if not unresolved_artists:
                    break
                found = get_artists_from_track_page(tid)
                resolved_track_cache[tid] = found
                for f_name, f_id in found.items():
                    f_norm = normalize_text(f_name)
                    artist_spotify_ids[f_norm] = f_id
                unresolved_artists = [a for a in unresolved_artists if normalize_text(a) not in artist_spotify_ids]

        # 4. Enriquecimento de Dados (Spotify + Redes Sociais + INPI)
        job["progress"] = {"step": 4, "step_name": "Coletando métricas e marcas dos artistas", "percent": 30}
        broadcast_event(job_id, "progress", job["progress"])
        append_job_log(job, "Iniciando coleta de ouvintes, redes sociais e marcas...")

        inpi_session = None
        if not skip_live_inpi:
            try:
                inpi_session = init_inpi_session()
            except Exception:
                inpi_session = None

        from concurrent.futures import ThreadPoolExecutor, as_completed

        artists_data = {}
        sem_marca_count = 0
        com_marca_count = 0
        completed_count = 0
        start_time = time.time()
        time_limit = 240 if IS_VERCEL else 1800

        def enrich_single_artist(name):
            norm_name = normalize_text(name)
            aid = artist_spotify_ids.get(norm_name)

            if not aid and norm_name in artist_tracks_map:
                tid = artist_tracks_map[norm_name]
                if tid not in resolved_track_cache:
                    resolved_track_cache[tid] = get_artists_from_track_page(tid)
                found = resolved_track_cache.get(tid, {})
                for f_name, f_id in found.items():
                    if normalize_text(f_name) == norm_name or norm_name in normalize_text(f_name):
                        aid = f_id
                        artist_spotify_ids[norm_name] = aid
                        break

            spotify_info = get_artist_spotify_info(aid) if aid else {
                'spotify_url': None, 'monthly_listeners': None, 'instagram': None,
                'twitter': None, 'facebook': None, 'tiktok': None, 'youtube': None
            }

            social_info = enrich_artist_social_metrics(
                spotify_info,
                known_social=known_socials.get(norm_name),
                artist_name=name
            )

            inpi_records = known_marcas.get(norm_name)
            inpi_status = "HISTÓRICO" if inpi_records else ""

            if not inpi_records and not skip_live_inpi and inpi_session:
                try:
                    live_records, status = search_inpi_live(name, session=inpi_session)
                    if status == "encontrada" and live_records:
                        inpi_records = live_records
                        inpi_status = "INPI LIVE"
                    elif status == "sem_marca":
                        inpi_records = None
                        inpi_status = "SEM MARCA"
                    elif status == "offline":
                        inpi_status = "INPI OFFLINE"
                except Exception:
                    inpi_status = "INPI OFFLINE"

            search_url = build_inpi_direct_url(name)
            count_val = artist_counts[name]
            tem_marca = bool(inpi_records)

            return {
                'name': name,
                'count': count_val,
                'count_display': str(count_val) if count_val > 1 else "",
                'monthly_listeners': spotify_info.get('monthly_listeners'),
                'monthly_listeners_fmt': f"{spotify_info.get('monthly_listeners'):,}".replace(',', '.') if spotify_info.get('monthly_listeners') else "N/D",
                'spotify_url': spotify_info.get('spotify_url'),
                'instagram': spotify_info.get('instagram'),
                'ig_display': social_info['ig_display'] or "N/D",
                'ig_url': social_info['ig_url'],
                'tiktok_url': social_info['tiktok_url'],
                'tiktok_display': social_info['tiktok_display'] or "N/D",
                'youtube_url': social_info['youtube_url'],
                'youtube_display': social_info['youtube_display'] or "N/D",
                'tem_marca': tem_marca,
                'inpi_status': inpi_status or ("COM MARCA" if tem_marca else "SEM MARCA"),
                'inpi_records': inpi_records,
                'inpi_search_url': search_url
            }

        max_workers = 8
        executor = ThreadPoolExecutor(max_workers=max_workers)
        try:
            future_to_artist = {executor.submit(enrich_single_artist, name): name for name in unique_artists}

            for future in as_completed(future_to_artist):
                name = future_to_artist[future]
                completed_count += 1
                try:
                    artist_entry = future.result()
                except Exception as ex:
                    search_url = build_inpi_direct_url(name)
                    count_val = artist_counts[name]
                    artist_entry = {
                        'name': name, 'count': count_val, 'count_display': str(count_val) if count_val > 1 else "",
                        'monthly_listeners': None, 'monthly_listeners_fmt': 'N/D', 'spotify_url': None,
                        'instagram': None, 'ig_display': 'N/D', 'ig_url': None,
                        'tiktok_url': None, 'tiktok_display': 'N/D', 'youtube_url': None, 'youtube_display': 'N/D',
                        'tem_marca': False, 'inpi_status': 'SEM MARCA', 'inpi_records': None,
                        'inpi_search_url': search_url
                    }

                if artist_entry['tem_marca']:
                    com_marca_count += 1
                else:
                    sem_marca_count += 1

                artists_data[name] = artist_entry
                job["artists"].append(artist_entry)
                job["summary"]["sem_marca"] = sem_marca_count
                job["summary"]["com_marca"] = com_marca_count

                pct = 30 + int((completed_count / total_artists) * 60)
                job["progress"] = {
                    "step": 4,
                    "step_name": f"Processando artistas ({completed_count}/{total_artists})",
                    "current_artist_idx": completed_count,
                    "total_artists": total_artists,
                    "percent": pct
                }
                job["current_artist"] = {
                    "name": name,
                    "listeners": artist_entry["monthly_listeners_fmt"],
                    "ig": artist_entry["ig_display"],
                    "yt": artist_entry["youtube_display"],
                    "tiktok": artist_entry["tiktok_display"],
                    "marca": "Com Marca" if artist_entry['tem_marca'] else "Sem Marca"
                }

                broadcast_event(job_id, "artist_done", {
                    "artist": artist_entry,
                    "progress": job["progress"],
                    "summary": job["summary"],
                    "current_artist": job["current_artist"]
                })

                append_job_log(
                    job,
                    f"[{completed_count:02d}/{total_artists:02d}] {name} | Ouvintes: {artist_entry['monthly_listeners_fmt']} | IG: {artist_entry['ig_display']} | YT: {artist_entry['youtube_display']} | {'MARCA' if artist_entry['tem_marca'] else 'S/ MARCA'}"
                )

                if time.time() - start_time > time_limit:
                    append_job_log(job, "[!] Limite de tempo de execução alcançado. Finalizando planilha com os artistas processados...")
                    try:
                        executor.shutdown(wait=False, cancel_futures=True)
                    except Exception:
                        pass
                    break
        finally:
            try:
                executor.shutdown(wait=False)
            except Exception:
                pass

        # Garante que qualquer artista não concluído por timeout tenha registro padrão
        for name in unique_artists:
            if name not in artists_data:
                search_url = build_inpi_direct_url(name)
                count_val = artist_counts[name]
                artists_data[name] = {
                    'name': name, 'count': count_val, 'count_display': str(count_val) if count_val > 1 else "",
                    'monthly_listeners': None, 'monthly_listeners_fmt': 'N/D', 'spotify_url': None,
                    'instagram': None, 'ig_display': 'N/D', 'ig_url': None,
                    'tiktok_url': None, 'tiktok_display': 'N/D', 'youtube_url': None, 'youtube_display': 'N/D',
                    'tem_marca': False, 'inpi_status': 'SEM MARCA', 'inpi_records': None,
                    'inpi_search_url': search_url
                }

        # 5. Geração da Planilha Excel
        job["progress"] = {"step": 5, "step_name": "Construindo planilha Excel final", "percent": 95}
        broadcast_event(job_id, "progress", job["progress"])
        append_job_log(job, "Criando arquivo Excel com formatação oficial e 4 abas...")

        import re
        date_str = datetime.now().strftime("%d.%m.%y")
        clean_title = re.sub(r'[\\/*?:"<>|]', "", playlist_title).strip() or "Playlist Spotify"
        output_filename = f"{clean_title} {date_str} - Automatizada.xlsx"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        build_final_workbook(output_path, playlist_title, tracks, artists_data)

        import base64
        file_b64 = ""
        try:
            with open(output_path, "rb") as f:
                file_b64 = base64.b64encode(f.read()).decode("utf-8")
        except Exception as err:
            append_job_log(job, f"Aviso ao codificar base64: {err}")

        job["output_file"] = output_path
        job["output_filename"] = output_filename
        job["file_base64"] = file_b64
        job["status"] = "completed"
        job["progress"] = {"step": 5, "step_name": "Concluído com sucesso!", "percent": 100}

        append_job_log(job, f"[✔] Planilha gerada com sucesso: {output_filename}")
        append_job_log(job, f"[🎯] Leads sem marca: {sem_marca_count} | Com marca: {com_marca_count}")

        broadcast_event(job_id, "completed", {
            "output_filename": output_filename,
            "download_url": f"/api/download/{job_id}",
            "file_base64": file_b64,
            "summary": job["summary"]
        })

    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)
        append_job_log(job, f"[ERRO] Falha no processamento: {e}")
        broadcast_event(job_id, "error", {"message": str(e)})


# --- ROTAS DA API ---

@app.post("/api/jobs/run-stream")
async def run_job_stream(
    request: Request,
    target_type: str = Form(...),
    playlist_url: Optional[str] = Form(None),
    skip_live_inpi: bool = Form(False),
    file: Optional[UploadFile] = File(None)
):
    """
    Executa o pipeline completo dentro de uma única conexão HTTP com streaming SSE.
    Previne congelamento em ambientes serverless (Vercel) e garante entrega em tempo real.
    """
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    target_value = ""
    if target_type == "playlist":
        if not playlist_url or not playlist_url.strip():
            raise HTTPException(status_code=400, detail="A URL da playlist é obrigatória.")
        target_value = playlist_url.strip()
    elif target_type == "file":
        if not file:
            raise HTTPException(status_code=400, detail="Nenhum arquivo enviado.")
        file_path = os.path.join(UPLOAD_DIR, f"{job_id}_{file.filename}")
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        target_value = file_path
    else:
        raise HTTPException(status_code=400, detail="target_type inválido.")

    job = {
        "id": job_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "target_type": target_type,
        "target_value": target_value,
        "playlist_title": "",
        "skip_live_inpi": skip_live_inpi,
        "progress": {"step": 0, "step_name": "Iniciando...", "percent": 0},
        "current_artist": None,
        "summary": {"total_tracks": 0, "total_artists": 0, "sem_marca": 0, "com_marca": 0},
        "artists": [],
        "output_file": None,
        "output_filename": None,
        "error": None,
        "logs": []
    }

    jobs[job_id] = job
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    with job_lock:
        job_subscribers[job_id] = [(loop, queue)]

    # Inicia o pipeline de extração e enriquecimento em thread ligada à requisição ativa
    asyncio.create_task(
        asyncio.to_thread(run_pipeline_sync, job_id, target_type, target_value, skip_live_inpi)
    )

    async def event_generator():
        try:
            initial_data = {
                "job_id": job_id,
                "status": "running",
                "progress": job["progress"],
                "summary": job["summary"]
            }
            yield f"event: init\ndata: {safe_json_dumps(initial_data)}\n\n"

            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield f"event: {payload['event']}\ndata: {safe_json_dumps(payload['data'])}\n\n"
                    if payload["event"] in ["completed", "error"]:
                        break
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            with job_lock:
                if job_id in job_subscribers:
                    job_subscribers[job_id] = [item for item in job_subscribers[job_id] if (item[1] if isinstance(item, tuple) else item) != queue]

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/api/jobs")
async def create_job(
    background_tasks: BackgroundTasks,
    target_type: str = Form(...),
    playlist_url: Optional[str] = Form(None),
    skip_live_inpi: bool = Form(False),
    file: Optional[UploadFile] = File(None)
):
    """Cria e inicia um novo job de automação"""
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    target_value = ""
    if target_type == "playlist":
        if not playlist_url or not playlist_url.strip():
            raise HTTPException(status_code=400, detail="A URL da playlist é obrigatória.")
        target_value = playlist_url.strip()
    elif target_type == "file":
        if not file:
            raise HTTPException(status_code=400, detail="Nenhum arquivo enviado.")
        file_path = os.path.join(UPLOAD_DIR, f"{job_id}_{file.filename}")
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        target_value = file_path
    else:
        raise HTTPException(status_code=400, detail="target_type inválido.")

    job = {
        "id": job_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "target_type": target_type,
        "target_value": target_value,
        "playlist_title": "",
        "skip_live_inpi": skip_live_inpi,
        "progress": {"step": 0, "step_name": "Iniciando...", "percent": 0},
        "current_artist": None,
        "summary": {"total_tracks": 0, "total_artists": 0, "sem_marca": 0, "com_marca": 0},
        "artists": [],
        "output_file": None,
        "output_filename": None,
        "error": None,
        "logs": []
    }

    jobs[job_id] = job
    job_subscribers[job_id] = []

    # Dispara a execução em background thread
    threading.Thread(
        target=run_pipeline_sync,
        args=(job_id, target_type, target_value, skip_live_inpi),
        daemon=True
    ).start()

    return {"job_id": job_id, "status": "pending"}


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Retorna os dados consolidados do job"""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    return {
        "id": job["id"],
        "status": job["status"],
        "created_at": job["created_at"],
        "playlist_title": job["playlist_title"],
        "progress": job["progress"],
        "current_artist": job.get("current_artist"),
        "summary": job["summary"],
        "output_filename": job["output_filename"],
        "download_url": f"/api/download/{job_id}" if job["output_file"] else None,
        "error": job["error"],
        "artists": job["artists"],
        "logs_count": len(job["logs"])
    }


@app.get("/api/jobs/{job_id}/stream")
async def stream_job_events(job_id: str, request: Request):
    """Server-Sent Events (SSE) com atualizações ao vivo"""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    with job_lock:
        if job_id not in job_subscribers:
            job_subscribers[job_id] = []
        job_subscribers[job_id].append((loop, queue))

    async def event_generator():
        try:
            # Envia estado inicial
            initial_data = {
                "job_id": job_id,
                "status": job["status"],
                "progress": job["progress"],
                "summary": job["summary"],
                "current_artist": job.get("current_artist"),
                "logs": job["logs"][-20:]
            }
            yield f"event: init\ndata: {safe_json_dumps(initial_data)}\n\n"

            # Se o job já estiver finalizado, envia completed imediatamente
            if job["status"] == "completed":
                yield f"event: completed\ndata: {safe_json_dumps({'output_filename': job['output_filename'], 'download_url': f'/api/download/{job_id}', 'file_base64': job.get('file_base64', ''), 'summary': job['summary']})}\n\n"
                return
            elif job["status"] == "error":
                yield f"event: error\ndata: {safe_json_dumps({'message': job['error']})}\n\n"
                return

            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield f"event: {payload['event']}\ndata: {safe_json_dumps(payload['data'])}\n\n"
                    if payload["event"] in ["completed", "error"]:
                        break
                except asyncio.TimeoutError:
                    # Envia ping de keep-alive
                    yield ": keep-alive\n\n"
        finally:
            with job_lock:
                if job_id in job_subscribers:
                    job_subscribers[job_id] = [item for item in job_subscribers[job_id] if (item[1] if isinstance(item, tuple) else item) != queue]

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/api/download/{job_id}")
async def download_job_file(job_id: str):
    """Download do arquivo Excel gerado pelo job"""
    job = jobs.get(job_id)
    if not job or not job.get("output_file") or not os.path.exists(job["output_file"]):
        raise HTTPException(status_code=404, detail="Arquivo gerado não encontrado.")

    return FileResponse(
        path=job["output_file"],
        filename=job.get("output_filename", "planilha.xlsx"),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.get("/api/history")
async def get_history():
    """Lista as planilhas já geradas na pasta output/"""
    files = []
    for fpath in glob.glob(os.path.join(OUTPUT_DIR, "*.xlsx")):
        if os.path.basename(fpath).startswith("~$"):
            continue
        stat = os.stat(fpath)
        fname = os.path.basename(fpath)
        files.append({
            "filename": fname,
            "size_kb": round(stat.st_size / 1024, 1),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M:%S"),
            "download_url": f"/api/history/download/{fname}"
        })
    files.sort(key=lambda x: x["modified_at"], reverse=True)
    return {"files": files}


@app.get("/api/history/download/{filename}")
async def download_history_file(filename: str):
    """Download de qualquer planilha do histórico"""
    clean_name = os.path.basename(filename)
    fpath = os.path.join(OUTPUT_DIR, clean_name)
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
    return FileResponse(
        path=fpath,
        filename=clean_name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.get("/api/config/spotify")
async def get_spotify_config():
    """Informa se as chaves da API do Spotify estão configuradas"""
    cid, csec = load_spotify_credentials()
    return {
        "configured": bool(cid and csec),
        "client_id_preview": f"{cid[:4]}...{cid[-4:]}" if cid else None
    }


@app.post("/api/config/spotify")
async def set_spotify_config(
    client_id: str = Form(...),
    client_secret: str = Form(...)
):
    """Salva as credenciais do Spotify Developer no arquivo local"""
    success = save_spotify_credentials(client_id, client_secret)
    if success:
        return {"success": True, "message": "Credenciais salvas com sucesso!"}
    raise HTTPException(status_code=500, detail="Erro ao salvar credenciais.")


# Servir Frontend Estático
@app.get("/static/style.css")
async def serve_css():
    css_path = os.path.join(WEB_DIR, "style.css")
    if os.path.exists(css_path):
        return FileResponse(css_path, media_type="text/css")
    raise HTTPException(status_code=404, detail="CSS not found")


@app.get("/static/app.js")
async def serve_js():
    js_path = os.path.join(WEB_DIR, "app.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="JS not found")


if os.path.exists(WEB_DIR):
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")



@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Interface web em construção...</h1>")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"\n========================================================")
    print(f"  PAINEL WEB SPOTIFY & INPI PROSPECTOR")
    print(f"  Acesse no navegador: http://localhost:{port}")
    print(f"========================================================\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
