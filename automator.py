#!/usr/bin/env python3
"""
Automador de Planilha Top 50 Spotify, Redes Sociais & Marcas INPI
"""

import os
import sys
import argparse
import glob
import time
import unicodedata
from datetime import datetime
from collections import Counter

import re
from modules.spotify_service import (
    load_tracks_from_xlsx,
    load_tracks_from_csv,
    load_existing_artist_links,
    get_artist_spotify_info,
    get_artists_from_track_page,
    load_tracks_from_playlist,
    extract_artist_id
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


def normalize_text(text):
    """Normaliza texto para comparações insensíveis a acentos e maiúsculas"""
    if not text:
        return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('ASCII').strip().lower()


def main():
    parser = argparse.ArgumentParser(description="Automação da Planilha Top 50 Spotify com Métricas e Marcas")
    parser.add_argument("target", nargs="?", help="Link da playlist do Spotify ou caminho de arquivo (.xlsx/.csv)")
    parser.add_argument("--file", "-f", help="Caminho do arquivo Excel ou CSV")
    parser.add_argument("--playlist", "-p", help="URL ou ID da playlist pública do Spotify")
    parser.add_argument("--output", "-o", help="Nome ou caminho do arquivo de saída (salvo por padrão na pasta 'output/')")
    parser.add_argument("--skip-live-inpi", action="store_true", help="Ignora a busca ao vivo no site do INPI e utiliza links inteligentes diretos")
    parser.add_argument("--client-id", help="Spotify API Client ID (opcional)")
    parser.add_argument("--client-secret", help="Spotify API Client Secret (opcional)")
    args = parser.parse_args()

    print("=" * 70)
    print("  AUTOMATIZADOR DE PLANILHAS SPOTIFY & PROSPECÇÃO DE MARCAS INPI")
    print("=" * 70)

    # 1. Determinar a fonte de dados (Arquivo ou Playlist)
    file_path = args.file
    playlist_arg = args.playlist

    if args.target:
        if args.target.startswith("http") or "spotify.com/playlist" in args.target:
            playlist_arg = args.target
        elif args.target.endswith(".xlsx") or args.target.endswith(".csv"):
            file_path = args.target

    # Se nada foi informado por argumentos, verifica arquivo ou pergunta ao usuário
    if not file_path and not playlist_arg:
        candidates = [f for f in glob.glob("*.xlsx") + glob.glob("*.csv") if not f.startswith("~$")]
        if sys.stdin.isatty():
            print("\nComo você deseja carregar as músicas?")
            if candidates:
                print(f"  [1] Usar arquivo da pasta raiz: '{candidates[0]}'")
            print("  [2] Colar o link de qualquer playlist do Spotify")
            print()
            try:
                choice = input("Pressione ENTER para [1] ou cole o link da playlist aqui: ").strip()
            except (EOFError, KeyboardInterrupt):
                choice = ""

            if choice.startswith("http") or "spotify.com" in choice:
                playlist_arg = choice
            elif choice == "2":
                playlist_arg = input("Cole a URL da playlist do Spotify: ").strip()
            elif candidates:
                file_path = candidates[0]
                print(f"[*] Usando arquivo da pasta: {file_path}")
            else:
                print("[!] Nenhuma opção selecionada e nenhum arquivo encontrado.")
                sys.exit(1)
        else:
            if candidates:
                file_path = candidates[0]
                print(f"[*] Arquivo de entrada selecionado automaticamente: {file_path}")
            else:
                print("[!] Nenhum arquivo .xlsx/.csv encontrado na pasta raiz.")
                print("    Informe o link da playlist ou um arquivo.")
                sys.exit(1)

    tracks = []
    playlist_title = "Brasil"
    existing_spotify_links = {}

    if file_path:
        print(f"\n[1/5] Lendo faixas do arquivo: {file_path}")
        existing_spotify_links = load_existing_artist_links(file_path)
        if file_path.endswith('.csv'):
            tracks = load_tracks_from_csv(file_path)
        else:
            tracks = load_tracks_from_xlsx(file_path)
            match_title = os.path.basename(file_path).replace('.xlsx', '').replace('.csv', '')
            if match_title:
                playlist_title = match_title
    elif playlist_arg:
        print(f"\n[1/5] Carregando faixas da Playlist: {playlist_arg}")
        try:
            playlist_title, tracks = load_tracks_from_playlist(
                playlist_arg,
                client_id=args.client_id,
                client_secret=args.client_secret,
                interactive=True
            )
        except Exception as e:
            print(f"\n[!] Erro ao carregar playlist: {e}")
            sys.exit(1)

    print(f"  -> {len(tracks)} faixas carregadas com sucesso.")

    # 2. Carregar banco histórico de marcas e redes sociais conhecidas
    print("\n[2/5] Verificando histórico de marcas e redes sociais...")
    known_marcas = {}
    known_socials = {}
    historical_files = [f for f in glob.glob("*.xlsx") + glob.glob("output/*.xlsx") if not os.path.basename(f).startswith("~$")]
    for f in historical_files:
        loaded_m = load_known_marcas_from_excel(f)
        known_marcas.update(loaded_m)
        loaded_s = load_known_socials_from_excel(f)
        for k, v in loaded_s.items():
            if k not in known_socials:
                known_socials[k] = dict(v)
            else:
                for field, val in v.items():
                    if val:
                        # Não sobrescreve contagem real de seguidores por apenas um @handle provisório
                        if field == 'ig_val' and known_socials[k].get('ig_val') and not known_socials[k]['ig_val'].startswith('@') and val.startswith('@'):
                            continue
                        known_socials[k][field] = val
    print(f"  -> {len(known_marcas)} marcas já catalogadas encontradas no histórico local.")
    print(f"  -> {len(known_socials)} artistas com redes sociais registradas no histórico.")

    # 3. Mapear e desmembrar artistas únicos
    print("\n[3/5] Identificando artistas únicos e resolvendo IDs do Spotify...")
    artist_counts = Counter()
    artist_tracks_map = {}
    artist_spotify_ids = {}

    for norm_name, aid in existing_spotify_links.items():
        artist_spotify_ids[norm_name] = aid

    for t in tracks:
        for a in t.get('artists', []):
            name = a['name'].strip()
            norm = normalize_text(name)
            artist_counts[name] += 1
            if norm not in artist_tracks_map and t.get('track_id'):
                artist_tracks_map[norm] = t.get('track_id')
            if a.get('id') and norm not in artist_spotify_ids:
                artist_spotify_ids[norm] = a.get('id')

    unique_artists = sorted(artist_counts.keys(), key=lambda s: normalize_text(s))
    print(f"  -> {len(unique_artists)} artistas únicos identificados.")

    # Resolução de IDs de artistas pelas páginas das faixas (com cache)
    unique_track_ids = list(dict.fromkeys([t.get('track_id') for t in tracks if t.get('track_id')]))
    resolved_track_cache = {}
    
    unresolved_artists = [a for a in unique_artists if normalize_text(a) not in artist_spotify_ids]
    if unresolved_artists:
        print(f"  -> Resolvendo IDs do Spotify para {len(unresolved_artists)} artistas através das faixas...")
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
    print("\n[4/5] Coletando métricas do Spotify, Redes Sociais e checando Marcas...")
    
    inpi_session = None
    if not args.skip_live_inpi:
        inpi_session = init_inpi_session()

    artists_data = {}
    total = len(unique_artists)

    for idx, name in enumerate(unique_artists, 1):
        print(f"  [{idx:02d}/{total:02d}] {name[:26]:<26}", end="", flush=True)
        norm_name = normalize_text(name)

        aid = artist_spotify_ids.get(norm_name)
        if not aid and norm_name in artist_tracks_map:
            tid = artist_tracks_map[norm_name]
            if tid not in resolved_track_cache:
                resolved_track_cache[tid] = get_artists_from_track_page(tid)
            found = resolved_track_cache[tid]
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
        inpi_status_tag = "HISTÓRICO" if inpi_records else ""

        if not inpi_records and not args.skip_live_inpi and inpi_session:
            live_records, status = search_inpi_live(name, session=inpi_session)
            if status == "encontrada" and live_records:
                inpi_records = live_records
                inpi_status_tag = "INPI LIVE"
            elif status == "sem_marca":
                inpi_records = None
                inpi_status_tag = "SEM MARCA"
            elif status == "offline":
                inpi_status_tag = "INPI OFFLINE"

        search_url = build_inpi_direct_url(name)

        count_val = artist_counts[name]
        artists_data[name] = {
            'name': name,
            'count': count_val,
            'count_display': str(count_val) if count_val > 1 else "",
            'monthly_listeners': spotify_info.get('monthly_listeners'),
            'spotify_url': spotify_info.get('spotify_url'),
            'instagram': spotify_info.get('instagram'),
            'ig_display': social_info['ig_display'],
            'ig_url': social_info['ig_url'],
            'tiktok_url': social_info['tiktok_url'],
            'tiktok_display': social_info['tiktok_display'],
            'youtube_url': social_info['youtube_url'],
            'youtube_display': social_info['youtube_display'],
            'inpi_records': inpi_records,
            'inpi_search_url': search_url
        }

        ouvintes_txt = f"{spotify_info.get('monthly_listeners'):,}".replace(',', '.') if spotify_info.get('monthly_listeners') else "N/D"
        marca_txt = f"MARCA ({len(inpi_records)})" if inpi_records else "S/ MARCA"
        ig_txt = social_info['ig_display'] or "N/D"
        yt_txt = social_info['youtube_display'] or "N/D"
        print(f" | Ouvintes: {ouvintes_txt:>12} | IG: {ig_txt[:10]:<10} | YT: {yt_txt[:12]:<12} | {marca_txt:<10}")

        time.sleep(0.1)

    # 5. Geração do Arquivo Excel Final na pasta 'output/'
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    date_str = datetime.now().strftime("%d.%m.%y")
    clean_title = re.sub(r'[\\/*?:"<>|]', "", playlist_title).strip()
    if not clean_title:
        clean_title = "Playlist Spotify"
    default_filename = f"{clean_title} {date_str} - Automatizada.xlsx"

    if args.output:
        if os.path.dirname(args.output):
            output_filename = args.output
        else:
            output_filename = os.path.join(output_dir, args.output)
    else:
        output_filename = os.path.join(output_dir, default_filename)

    print(f"\n[5/5] Construindo planilha Excel com 4 abas estruturadas em: {output_filename}")
    build_final_workbook(output_filename, playlist_title, tracks, artists_data)

    sem_marca_count = sum(1 for a in artists_data.values() if not a.get('inpi_records'))
    com_marca_count = len(artists_data) - sem_marca_count

    print("=" * 70)
    print("  PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
    print(f"  [✔] Arquivo gerado em: {output_filename}")
    print(f"  [📊] Artistas analisados: {len(artists_data)}")
    print(f"  [🎯] Artistas SEM MARCA (Leads de prospecção): {sem_marca_count}")
    print(f"  [🛡] Artistas COM MARCA: {com_marca_count}")
    print("=" * 70)


if __name__ == "__main__":
    main()
