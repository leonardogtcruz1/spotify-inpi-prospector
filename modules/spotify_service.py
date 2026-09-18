import os
import sys
import json
import re
import csv
import time
import urllib.request
import urllib.parse
from collections import Counter
import openpyxl

SPOTIFY_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'
}


def extract_artist_id(url_or_id):
    """Extrai o ID alfanumérico do artista a partir de uma URL ou do próprio ID"""
    if not url_or_id:
        return None
    m = re.search(r'artist/([a-zA-Z0-9]+)', url_or_id)
    if m:
        return m.group(1)
    if re.match(r'^[a-zA-Z0-9]{22}$', url_or_id):
        return url_or_id
    return None


def extract_playlist_id(url_or_id):
    """Extrai o ID da playlist a partir de uma URL ou ID direto"""
    if not url_or_id:
        return None
    m = re.search(r'playlist/([a-zA-Z0-9]+)', url_or_id)
    if m:
        return m.group(1)
    if re.match(r'^[a-zA-Z0-9]{22}$', url_or_id):
        return url_or_id
    return url_or_id


def get_artist_spotify_info(artist_id):
    """
    Acessa a página pública do artista no Spotify e extrai:
    - Ouvintes mensais (ex: 11574456)
    - Redes sociais oficiais linkadas na biografia (Instagram, Twitter, Facebook, TikTok, YouTube)
    """
    clean_id = extract_artist_id(artist_id)
    if not clean_id:
        return {
            'spotify_url': None,
            'monthly_listeners': None,
            'instagram': None,
            'twitter': None,
            'facebook': None,
            'tiktok': None,
            'youtube': None
        }

    url = f"https://open.spotify.com/artist/{clean_id}"
    req = urllib.request.Request(url, headers=SPOTIFY_HEADERS)
    info = {
        'spotify_url': url,
        'monthly_listeners': None,
        'instagram': None,
        'twitter': None,
        'facebook': None,
        'tiktok': None,
        'youtube': None
    }

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

            # 1. Ouvintes Mensais
            # Regex 1: elemento de label com número exato
            m = re.search(r'data-testid=[\"\']monthly-listeners-label[\"\']>([0-9.,]+)\s*monthly listeners', html, re.I)
            if not m:
                # Regex 2: meta tag og:description ou twitter:description
                m = re.search(r'content=[\"\']Artist\s*[·\u00B7]\s*([0-9.,]+[MBK]?)\s*monthly listeners', html, re.I)
            if not m:
                m = re.search(r'>([0-9.,]+)\s*(?:monthly listeners|ouvintes mensais)<', html, re.I)

            if m:
                raw_num = m.group(1).replace(',', '').replace('.', '')
                if raw_num.isdigit():
                    info['monthly_listeners'] = int(raw_num)
                else:
                    info['monthly_listeners'] = m.group(1)

            # 2. Redes sociais na página do artista
            # Instagram
            ig = re.findall(r'href=[\"\'](https?://(?:www\.)?instagram\.com/[a-zA-Z0-9_.@\-]+)/?[\"\']', html)
            if ig:
                valid_ig = [u for u in ig if not any(x in u.lower() for x in ['/p/', '/explore', '/reels', '/stories', '/accounts'])]
                if valid_ig:
                    info['instagram'] = valid_ig[0].rstrip('/')

            # Twitter / X
            tw = re.findall(r'href=[\"\'](https?://(?:www\.)?(?:twitter\.com|x\.com)/[a-zA-Z0-9_.@\-]+)/?[\"\']', html)
            if tw:
                info['twitter'] = tw[0].rstrip('/')

            # Facebook
            fb = re.findall(r'href=[\"\'](https?://(?:www\.)?facebook\.com/[a-zA-Z0-9_.@\-]+)/?[\"\']', html)
            if fb:
                info['facebook'] = fb[0].rstrip('/')

            # TikTok
            tt = re.findall(r'href=[\"\'](https?://(?:www\.)?tiktok\.com/@[a-zA-Z0-9_.@\-]+)/?[\"\']', html)
            if tt:
                info['tiktok'] = tt[0].rstrip('/')

            # YouTube
            yt = re.findall(r'href=[\"\'](https?://(?:www\.)?youtube\.com/(?:channel/|@)[a-zA-Z0-9_.@\-]+)/?[\"\']', html)
            if yt:
                info['youtube'] = yt[0].rstrip('/')

    except Exception as e:
        print(f"    [!] Aviso ao consultar artista {clean_id}: {e}")

    return info


def get_artists_from_track_page(track_id):
    """
    Acessa a página pública da faixa no Spotify e extrai todos os artistas e seus respectivos IDs
    """
    if not track_id:
        return {}
    url = f"https://open.spotify.com/track/{track_id}"
    req = urllib.request.Request(url, headers=SPOTIFY_HEADERS)
    artist_map = {}
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            matches = re.findall(r'href=[\"\'](?:/intl-[a-z]+/|/)artist/([a-zA-Z0-9]+)[\"\'][^>]*>(.*?)</a>', html)
            for aid, text in matches:
                clean_name = re.sub(r'<[^>]+>', '', text).strip()
                clean_name = clean_name.replace('&#x27;', "'").replace('&amp;', '&').replace('&quot;', '"')
                if clean_name and clean_name not in artist_map:
                    artist_map[clean_name] = aid
    except Exception:
        pass
    return artist_map


def load_existing_artist_links(file_path):
    """
    Varre a planilha em busca de hyperlinks existentes para artistas no Spotify
    """
    links_map = {}
    try:
        wb = openpyxl.load_workbook(file_path, data_only=False)
        for sname in ['Artistas sem marca', 'Todos os artistas']:
            if sname in wb.sheetnames:
                ws = wb[sname]
                for r in range(2, ws.max_row + 1):
                    art = ws.cell(r, 2).value
                    if art and str(art).strip():
                        name = str(art).strip()
                        c_cell = ws.cell(r, 3)
                        if c_cell.hyperlink and 'open.spotify.com/artist/' in c_cell.hyperlink.target:
                            links_map[name.lower()] = extract_artist_id(c_cell.hyperlink.target)
    except Exception:
        pass
    return links_map


def load_tracks_from_xlsx(file_path):
    """
    Carrega as faixas de um arquivo Excel (.xlsx).
    Inclui lógica de forward-fill para suportar faixas com múltiplos artistas em linhas mescladas/omitidas.
    """
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb.worksheets[0]
    
    header = [str(cell.value or '').strip().lower() for cell in ws[1]]
    
    col_pos = next((i for i, h in enumerate(header) if any(k in h for k in ['pos', '#', 'rank', 'música', 'musica'])), 0)
    col_song = next((i for i, h in enumerate(header) if any(k in h for k in ['song', 'track', 'nome', 'título', 'titulo'])), 1)
    col_artist = next((i for i, h in enumerate(header) if any(k in h for k in ['artist', 'artista'])), 2)
    col_genres = next((i for i, h in enumerate(header) if any(k in h for k in ['genre', 'gênero', 'genero'])), 3)
    col_album = next((i for i, h in enumerate(header) if 'album' in h or 'álbum' in h), 4)
    col_tid = next((i for i, h in enumerate(header) if any(k in h for k in ['track id', 'spotify track', 'track_id'])), 5)
    col_isrc = next((i for i, h in enumerate(header) if 'isrc' in h), 6)

    tracks_dict = {}
    last_track_meta = {
        'position': '',
        'name': '',
        'genres': '',
        'album': '',
        'track_id': '',
        'isrc': ''
    }
    
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not any(row):
            continue
            
        pos = str(row[col_pos]).strip() if col_pos < len(row) and row[col_pos] is not None else ""
        song = str(row[col_song]).strip() if col_song < len(row) and row[col_song] is not None else ""
        artist = str(row[col_artist]).strip() if col_artist < len(row) and row[col_artist] is not None else ""
        genres = str(row[col_genres]).strip() if col_genres < len(row) and row[col_genres] is not None else ""
        album = str(row[col_album]).strip() if col_album < len(row) and row[col_album] is not None else ""
        track_id = str(row[col_tid]).strip() if col_tid < len(row) and row[col_tid] is not None else ""
        isrc = str(row[col_isrc]).strip() if col_isrc < len(row) and row[col_isrc] is not None else ""

        if not artist:
            continue

        # Se esta linha tiver informações da faixa, atualiza o contexto da última faixa
        if song or track_id or pos:
            last_track_meta = {
                'position': pos or last_track_meta['position'],
                'name': song or last_track_meta['name'],
                'genres': genres or last_track_meta['genres'],
                'album': album or last_track_meta['album'],
                'track_id': track_id or last_track_meta['track_id'],
                'isrc': isrc or last_track_meta['isrc']
            }
        else:
            # Herda metadados da faixa anterior (forward-fill)
            pos = last_track_meta['position']
            song = last_track_meta['name']
            genres = last_track_meta['genres']
            album = last_track_meta['album']
            track_id = last_track_meta['track_id']
            isrc = last_track_meta['isrc']

        key = track_id if track_id else f"{pos}_{song}"
        if key not in tracks_dict:
            tracks_dict[key] = {
                'position': pos,
                'name': song,
                'genres': genres,
                'album': album,
                'track_id': track_id,
                'isrc': isrc,
                'artists': []
            }
        
        # Desmembra artistas se houver múltiplos na mesma célula
        artists_in_cell = [a.strip() for a in re.split(r'[,;/]|\bfeat\.?\b|\bft\.?\b', artist) if a.strip()]
        for a_name in artists_in_cell:
            if not any(exist['name'].lower() == a_name.lower() for exist in tracks_dict[key]['artists']):
                tracks_dict[key]['artists'].append({'name': a_name, 'id': None})

    return list(tracks_dict.values())


def load_tracks_from_csv(file_path):
    """
    Carrega as faixas de um arquivo CSV exportado do Chosic
    """
    tracks_dict = {}
    with open(file_path, mode='r', encoding='utf-8-sig', errors='ignore') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            pos = row.get('Position') or row.get('#') or row.get('Rank') or str(i)
            song = row.get('Song') or row.get('Track Name') or row.get('Title') or ''
            artists_raw = row.get('Artist') or row.get('Artist Name(s)') or ''
            genres = row.get('Genres') or row.get('Genre') or ''
            album = row.get('Album') or ''
            track_id = row.get('Spotify Track Id') or row.get('Track ID') or row.get('Spotify ID') or ''
            isrc = row.get('ISRC') or ''

            key = track_id if track_id else f"{pos}_{song}"
            if key not in tracks_dict:
                tracks_dict[key] = {
                    'position': pos,
                    'name': song,
                    'genres': genres,
                    'album': album,
                    'track_id': track_id,
                    'isrc': isrc,
                    'artists': []
                }
            artists_in_cell = [a.strip() for a in re.split(r'[,;/]|\bfeat\.?\b|\bft\.?\b', artists_raw) if a.strip()]
            for a_name in artists_in_cell:
                if not any(exist['name'].lower() == a_name.lower() for exist in tracks_dict[key]['artists']):
                    tracks_dict[key]['artists'].append({'name': a_name, 'id': None})

    return list(tracks_dict.values())


def load_spotify_credentials():
    """
    Tenta carregar as credenciais do Spotify Developer:
    1. De variáveis de ambiente (SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET)
    2. Do arquivo spotify_config.json na pasta do projeto
    """
    cid = os.getenv("SPOTIPY_CLIENT_ID")
    csec = os.getenv("SPOTIPY_CLIENT_SECRET")
    if cid and csec:
        return cid.strip(), csec.strip()

    cfg_file = "spotify_config.json"
    if os.path.exists(cfg_file):
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                cid = data.get("client_id") or data.get("SPOTIPY_CLIENT_ID")
                csec = data.get("client_secret") or data.get("SPOTIPY_CLIENT_SECRET")
                if cid and csec:
                    return str(cid).strip(), str(csec).strip()
        except Exception:
            pass
    return None, None


def save_spotify_credentials(client_id, client_secret, cfg_file="spotify_config.json"):
    """Salva as credenciais do Spotify Developer no arquivo local para não precisar redigitar"""
    try:
        data = {
            "client_id": client_id.strip(),
            "client_secret": client_secret.strip()
        }
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"  [✔] Credenciais salvas com sucesso em '{cfg_file}'.")
        return True
    except Exception as e:
        print(f"  [!] Não foi possível salvar credenciais: {e}")
        return False


def fetch_playlist_via_scraper(playlist_url_or_id):
    """
    Busca qualquer playlist pública do Spotify sem precisar de chaves/API (usando spotifyscraper)
    """
    try:
        from spotify_scraper import SpotifyClient
    except ImportError:
        return None, None

    clean_pid = extract_playlist_id(playlist_url_or_id)
    try:
        with SpotifyClient() as client:
            pl = client.get_playlist(clean_pid)
            name = getattr(pl, "name", "Playlist Spotify")
            tracks = []
            for pos, pt in enumerate(getattr(pl, "tracks", []), 1):
                t = pt.track
                tid = getattr(t, "id", "") or ""
                artists = []
                for a in getattr(t, "artists", []):
                    aid = ""
                    uri = getattr(a, "uri", "")
                    if uri and "artist:" in uri:
                        aid = uri.split(":")[-1]
                    artists.append({"name": a.name, "id": aid})

                album_name = getattr(t.album, "name", "") if getattr(t, "album", None) else ""
                tracks.append({
                    "position": str(pos),
                    "name": getattr(t, "name", ""),
                    "genres": "",
                    "album": album_name,
                    "track_id": tid,
                    "isrc": "",
                    "artists": artists
                })
            return name, tracks
    except Exception:
        # Retorna None para acionar fallback
        return None, None


def fetch_playlist_via_spotify_api(playlist_id, client_id, client_secret):
    """
    Busca todas as faixas e artistas de qualquer playlist via Spotipy com paginação completa
    """
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials

    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)

    clean_pid = extract_playlist_id(playlist_id)
    playlist = sp.playlist(clean_pid)
    playlist_name = playlist.get("name", "Playlist Spotify")

    tracks = []
    results = playlist.get("tracks", {})
    items = results.get("items", [])
    
    pos = 1
    while True:
        for item in items:
            t = item.get("track")
            if not t:
                continue
            track_obj = {
                "position": str(pos),
                "name": t.get("name", ""),
                "genres": "",
                "album": t.get("album", {}).get("name", ""),
                "track_id": t.get("id", ""),
                "isrc": t.get("external_ids", {}).get("isrc", ""),
                "artists": []
            }
            for a in t.get("artists", []):
                track_obj["artists"].append({
                    "name": a.get("name", ""),
                    "id": a.get("id", "")
                })
            tracks.append(track_obj)
            pos += 1

        if results.get("next"):
            results = sp.next(results)
            items = results.get("items", [])
        else:
            break

    return playlist_name, tracks


def load_tracks_from_playlist(playlist_url_or_id, client_id=None, client_secret=None, interactive=True):
    """
    Carrega faixas a partir de qualquer link de playlist do Spotify:
    1. Tenta coletar automaticamente sem chaves (via scraper)
    2. Se for uma playlist restrita (como Charts/Top 50 oficial), usa a API oficial do Spotify
    3. Se não houver chaves, solicita uma única vez de forma amigável e salva
    """
    clean_pid = extract_playlist_id(playlist_url_or_id)
    
    # 1. Tentativa sem chaves via scraper público
    print(f"  -> Conectando ao Spotify para carregar a playlist...")
    name, tracks = fetch_playlist_via_scraper(clean_pid)
    if name and tracks:
        print(f"  [✔] Playlist '{name}' ({len(tracks)} faixas) carregada com sucesso diretamente!")
        return name, tracks

    # 2. Fallback via API oficial (Spotipy)
    cid = client_id
    csec = client_secret
    if not (cid and csec):
        cid, csec = load_spotify_credentials()

    if cid and csec:
        print(f"  -> Acessando via API oficial do Spotify...")
        name, tracks = fetch_playlist_via_spotify_api(clean_pid, cid, csec)
        print(f"  [✔] Playlist '{name}' ({len(tracks)} faixas) carregada via Spotify API!")
        return name, tracks

    # 3. Se ainda não temos credenciais e estamos em modo interativo
    if interactive and sys.stdin.isatty():
        print("\n" + "=" * 70)
        print("  CONFIGURAÇÃO DE ACESSO DO SPOTIFY (Apenas 1 vez)")
        print("=" * 70)
        print("Esta playlist específica (Gráfico Oficial do Spotify) exige acesso à API.")
        print("Para liberar o acesso direto em 1 clique nas próximas vezes:")
        print("1. Acesse https://developer.spotify.com/dashboard")
        print("2. Crie um app gratuito e copie seu Client ID e Client Secret.")
        print("-" * 70)
        user_cid = input("Digite o seu Client ID (ou pressione ENTER para cancelar): ").strip()
        if user_cid:
            user_csec = input("Digite o seu Client Secret: ").strip()
            if user_csec:
                save_spotify_credentials(user_cid, user_csec)
                name, tracks = fetch_playlist_via_spotify_api(clean_pid, user_cid, user_csec)
                print(f"  [✔] Playlist '{name}' ({len(tracks)} faixas) carregada com sucesso!")
                return name, tracks

    raise ValueError(
        f"Não foi possível carregar a playlist '{playlist_url_or_id}' automaticamente.\n"
        "Configure o Client ID e Secret no arquivo spotify_config.json ou use o arquivo baixado do Chosic."
    )
