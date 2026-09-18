import re
import json
import time
import unicodedata
import urllib.request
import urllib.parse
import openpyxl

DESKTOP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
}


def normalize_text(text):
    if not text:
        return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('ASCII').strip().lower()


def format_follower_count_br(number, platform='general'):
    """
    Formata contagens de seguidores no estilo brasileiro:
    - 11574456 -> 11,6 mi
    - 91100 -> 91,1 mil
    - 29500 -> 29.5K (TikTok) ou 29,5 mil
    """
    if not number:
        return None

    try:
        val = float(number)
    except (ValueError, TypeError):
        return str(number)

    if platform == 'tiktok':
        if val >= 1_000_000:
            return f"{val / 1_000_000:.1f}M".replace('.0M', 'M')
        elif val >= 1_000:
            return f"{val / 1_000:.1f}K".replace('.0K', 'K')
        return str(int(val))

    if platform == 'youtube':
        if val >= 1_000_000:
            formatted = f"{val / 1_000_000:.1f} mi".replace('.0 mi', ' mi')
        elif val >= 1_000:
            formatted = f"{val / 1_000:.1f} mil".replace('.0 mil', ' mil')
        else:
            formatted = str(int(val))
        return f"{formatted} inscritos"

    if val >= 1_000_000:
        return f"{val / 1_000_000:.1f} mi".replace('.', ',')
    elif val >= 1_000:
        return f"{val / 1_000:.1f} mil".replace('.', ',')
    return str(int(val))


def extract_ig_handle(ig_url):
    """Extrai o @handle de uma URL do Instagram"""
    if not ig_url:
        return None
    m = re.search(r'instagram\.com/([a-zA-Z0-9_.@\-]+)', ig_url)
    if m:
        handle = m.group(1).strip().lstrip('@').rstrip('/')
        if handle.lower() not in ['p', 'explore', 'reels', 'stories', 'accounts']:
            return handle
    return None


def format_ig_count(count_str):
    """Formata o texto de seguidores do Instagram no estilo brasileiro (ex: 408 mil, 10 mi)"""
    if not count_str:
        return None
    cs = count_str.strip().upper().replace('FOLLOWERS', '').replace('SEGUIDORES', '').strip()
    if cs.endswith('M'):
        num = cs[:-1].replace(',', '.')
        try:
            val = float(num)
            return f'{val:.1f} mi'.replace('.0 mi', ' mi').replace('.', ',')
        except:
            return cs
    elif cs.endswith('K'):
        num = cs[:-1].replace(',', '.')
        try:
            val = float(num)
            return f'{val:.1f} mil'.replace('.0 mil', ' mil').replace('.', ',')
        except:
            return cs
    return cs


def scrape_ig_followers(handle, artist_name=''):
    """
    Busca e extrai a quantidade de seguidores no Instagram a partir do @handle e/ou nome do artista.
    """
    if not handle:
        return None
    clean_handle = handle.lower().lstrip('@').rstrip('/')
    clean_artist = re.sub(r'^(?:mc|dj)\s+', '', str(artist_name).lower()).strip() if artist_name else ''

    queries = [
        f'site:instagram.com/{clean_handle}',
        f'\"instagram.com/{clean_handle}\"',
        f'@{clean_handle} instagram',
        f'@{clean_handle} instagram followers',
        f'{clean_artist} instagram' if clean_artist and len(clean_artist) > 3 else None
    ]

    for q in queries:
        if not q:
            continue
        url = f'https://search.yahoo.com/search?p={urllib.parse.quote(q)}'
        req = urllib.request.Request(url, headers=DESKTOP_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=4) as resp:
                page = resp.read().decode('utf-8', errors='ignore')
                snippets = re.findall(r'<div class=\"compText[^\"]*\"[^>]*>(.*?)</div>', page)

                # Prioridade 1: snippet menciona especificamente o @handle do artista
                for s in snippets:
                    c = re.sub(r'<[^>]+>', '', s).strip()
                    if f'@{clean_handle}' in c.lower() or f'/{clean_handle}' in c.lower():
                        m = re.search(r'([0-9.,]+\s*[KMBkmb]?)\s*(?:Followers|seguidores)', c, re.I)
                        if m:
                            val = m.group(1).strip()
                            if val.upper() not in ['686M', '0', '1', '2']:
                                return format_ig_count(val)

                # Prioridade 2: qualquer snippet do perfil com métrica válida
                for s in snippets:
                    c = re.sub(r'<[^>]+>', '', s).strip()
                    m = re.search(r'([0-9.,]+\s*[KMBkmb]?)\s*(?:Followers|seguidores)', c, re.I)
                    if m:
                        val = m.group(1).strip()
                        if val.upper() not in ['686M', '0', '1', '2', '3']:
                            return format_ig_count(val)
        except Exception:
            pass
        time.sleep(0.1)

    return None



def get_tiktok_followers(tiktok_url_or_handle):
    """
    Tenta coletar a quantidade de seguidores no TikTok a partir de uma URL ou @handle
    """
    if not tiktok_url_or_handle:
        return None, None

    if tiktok_url_or_handle.startswith('http'):
        url = tiktok_url_or_handle
    else:
        clean_handle = tiktok_url_or_handle.lstrip('@')
        url = f"https://www.tiktok.com/@{clean_handle}"

    req = urllib.request.Request(url, headers=DESKTOP_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            m = re.findall(r'\"followerCount\":([0-9]+)', html)
            if m:
                count = int(m[0])
                formatted = format_follower_count_br(count, platform='tiktok')
                return formatted, url
    except Exception:
        pass
    return None, url


def discover_tiktok_from_ig(ig_url):
    """
    Tenta descobrir o perfil do TikTok usando variações do @handle do Instagram
    """
    handle = extract_ig_handle(ig_url)
    if not handle:
        return None, None

    candidates = [
        handle,
        f"{handle}oficial",
        f"dj{handle}" if not handle.startswith('dj') else handle,
        f"mc{handle}" if not handle.startswith('mc') else handle,
        f"{handle}.ofc"
    ]

    for cand in candidates[:3]:
        count_str, url = get_tiktok_followers(cand)
        if count_str:
            return count_str, url

    return None, None


def load_known_socials_from_excel(file_path):
    """
    Carrega o histórico de redes sociais (IG, TikTok, YouTube) já preenchidas
    em planilhas anteriores para que nenhuma informação seja perdida.
    """
    socials_map = {}
    try:
        wb = openpyxl.load_workbook(file_path, data_only=False)
        for sname in ['Artistas sem marca', 'Todos os artistas']:
            if sname in wb.sheetnames:
                ws = wb[sname]
                for r in range(2, ws.max_row + 1):
                    art = ws.cell(r, 2).value
                    if not art or not str(art).strip():
                        continue
                    name = str(art).strip()
                    norm_key = normalize_text(name)

                    # Colunas de rede social
                    # Em Artistas sem marca: D=IG, E=TikTok, F=YouTube
                    # Em Todos os artistas: D=IG, E=TikTok, F=YouTube
                    c_ig = ws.cell(r, 4)
                    c_tt = ws.cell(r, 5)
                    c_yt = ws.cell(r, 6)

                    ig_val = str(c_ig.value).strip() if c_ig.value is not None else ""
                    ig_link = c_ig.hyperlink.target if c_ig.hyperlink else None

                    tt_val = str(c_tt.value).strip() if c_tt.value is not None else ""
                    tt_link = c_tt.hyperlink.target if c_tt.hyperlink else None

                    yt_val = str(c_yt.value).strip() if c_yt.value is not None else ""
                    yt_link = c_yt.hyperlink.target if c_yt.hyperlink else None

                    if norm_key not in socials_map:
                        socials_map[norm_key] = {
                            'ig_val': None, 'ig_link': None,
                            'tt_val': None, 'tt_link': None,
                            'yt_val': None, 'yt_link': None
                        }

                    # Só guarda valores reais de seguidores (não 'N/D', 'Ver perfil' ou @handle provisório)
                    if ig_val and ig_val.upper() != 'N/D' and ig_val != 'Ver perfil':
                        if not ig_val.startswith('@'):
                            socials_map[norm_key]['ig_val'] = ig_val
                        elif not socials_map[norm_key]['ig_val']:
                            # Se ainda não temos seguidores, podemos guardar o handle
                            socials_map[norm_key]['ig_val'] = ig_val
                    if ig_link:
                        socials_map[norm_key]['ig_link'] = ig_link

                    if tt_val and tt_val.upper() != 'N/D' and tt_val != 'Ver perfil':
                        socials_map[norm_key]['tt_val'] = tt_val
                    if tt_link:
                        socials_map[norm_key]['tt_link'] = tt_link

                    if yt_val and yt_val.upper() != 'N/D' and yt_val != 'Ver canal':
                        socials_map[norm_key]['yt_val'] = yt_val
                    if yt_link:
                        socials_map[norm_key]['yt_link'] = yt_link

    except Exception as e:
        print(f"  [!] Aviso ao carregar base histórica de redes: {e}")

    return socials_map


def discover_youtube_channel(artist_name):
    """
    Busca automaticamente o canal oficial do artista no YouTube
    e extrai a contagem de inscritos e o link do canal (@handle).
    """
    if not artist_name:
        return None, None

    query = urllib.parse.quote(f"{artist_name} oficial")
    url = f"https://www.youtube.com/results?search_query={query}"
    req = urllib.request.Request(url, headers=DESKTOP_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

            channel_url = None
            m_channel = re.search(r'\"channelRenderer\":.*?\"canonicalBaseUrl\":\"(/@[^\"]+)\"', html)
            if m_channel:
                channel_url = "https://www.youtube.com" + m_channel.group(1)
            else:
                m_url = re.search(r'\"canonicalBaseUrl\":\"(/@[^\"]+)\"', html)
                if m_url:
                    channel_url = "https://www.youtube.com" + m_url.group(1)

            m_subs = re.search(r'\"subscriberCountText\":\{.*?\"simpleText\":\"([^\"]+inscritos)\"', html)
            if not m_subs:
                m_subs = re.search(r'\"videoCountText\":.*?\"simpleText\":\"([^\"]+inscritos)\"', html)
            if not m_subs:
                m_subs = re.search(r'\"([0-9.,]+\s*(?:mil|mi|milhões)?\s*(?:de\s*)?inscritos)\"', html)

            subs = m_subs.group(1).replace('\xa0', ' ').strip() if m_subs else None
            return subs, channel_url
    except Exception:
        pass
    return None, None


def enrich_artist_social_metrics(artist_info, known_social=None, artist_name=None):
    """
    Enriquece os dados sociais do artista combinando:
    1. Histórico salvo de planilhas anteriores
    2. Links encontrados no perfil do Spotify
    3. Descoberta automática de perfis de TikTok a partir do Instagram
    4. Descoberta automática do canal oficial e inscritos do YouTube
    """
    known = known_social or {}

    # 1. Instagram
    ig_url = known.get('ig_link') or artist_info.get('instagram')
    ig_display = known.get('ig_val')

    # Se ainda não temos a contagem numérica de seguidores ou só temos o @handle
    if not ig_display or ig_display.startswith('@') or ig_display in ['Ver perfil', 'N/D']:
        if ig_url:
            handle = extract_ig_handle(ig_url)
            if handle:
                followers = scrape_ig_followers(handle, artist_name=artist_name)
                if followers:
                    ig_display = followers
                elif not ig_display or ig_display in ['Ver perfil', 'N/D']:
                    ig_display = f"@{handle}"
            else:
                ig_display = "Ver perfil"
        else:
            ig_display = "N/D"

    # 2. TikTok
    tt_url = known.get('tt_link') or artist_info.get('tiktok')
    tt_display = known.get('tt_val')

    if not tt_display:
        if tt_url:
            followers, _ = get_tiktok_followers(tt_url)
            tt_display = followers if followers else "Ver perfil"
        elif ig_url:
            # Tenta descobrir o TikTok automaticamente usando o @ do Instagram
            followers, auto_tt_url = discover_tiktok_from_ig(ig_url)
            if followers:
                tt_display = followers
                tt_url = auto_tt_url
            else:
                tt_display = "N/D"
        else:
            tt_display = "N/D"

    # 3. YouTube
    yt_url = known.get('yt_link') or artist_info.get('youtube')
    yt_display = known.get('yt_val')

    if not yt_display or yt_display == "N/D":
        # Descoberta automática do YouTube caso não esteja no histórico
        subs, ch_url = discover_youtube_channel(artist_name)
        if ch_url:
            yt_url = ch_url
            yt_display = subs if subs else "Ver canal"
        elif yt_url:
            yt_display = "Ver canal"
        else:
            yt_display = "N/D"

    return {
        'ig_url': ig_url,
        'ig_display': ig_display,
        'tiktok_url': tt_url,
        'tiktok_display': tt_display,
        'youtube_url': yt_url,
        'youtube_display': yt_display
    }
