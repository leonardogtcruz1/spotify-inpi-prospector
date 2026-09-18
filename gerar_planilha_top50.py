"""
Script de Automação para Planilha Top 50 Spotify & Prospecção de Marcas

Funcionalidades:
1. Ingestão dos dados da Playlist Top 50 (via Chosic CSV/Excel ou Spotify API).
2. Extração, contagem de ocorrências ('Músicas no top 50') e ordenação alfabética dos artistas.
3. Coleta automática no Spotify dos ouvintes mensais e redes sociais oficiais (Instagram, Twitter, Facebook).
4. Coleta/estimativa de seguidores (TikTok, YouTube, Instagram) com hyperlinks embutidos.
5. Integração e link direto de consulta ao INPI (Marcas).
6. Geração da planilha Excel (.xlsx) com as 4 abas estruturadas idênticas ao modelo.
"""

import os
import re
import sys
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime
from collections import Counter
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Headers padrão simulando navegador desktop
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

SPOTIFY_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'
}


def get_artist_spotify_info(artist_id):
    """
    Busca a página pública do artista no Spotify e extrai:
    - Ouvintes mensais (número exato ou aproximado)
    - Links de redes sociais (Instagram, Twitter/X, Facebook, Wikipedia)
    """
    url = f"https://open.spotify.com/artist/{artist_id}"
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
            # Regex 1: data-testid="monthly-listeners-label">11,574,456 monthly listeners</div>
            m = re.search(r'data-testid=[\"\']monthly-listeners-label[\"\']>([0-9.,]+)\s*monthly listeners', html, re.I)
            if not m:
                # Regex 2: meta tag og:description ou twitter:description
                m = re.search(r'content=[\"\']Artist\s*[·\u00B7]\s*([0-9.,]+[MBK]?)\s*monthly listeners', html, re.I)
            if not m:
                m = re.search(r'>([0-9.,]+)\s*(?:monthly listeners|ouvintes mensais)<', html, re.I)
            
            if m:
                # Remove vírgulas/pontos para manter o formato numérico limpo
                val_str = m.group(1).replace(',', '').replace('.', '')
                if val_str.isdigit():
                    info['monthly_listeners'] = int(val_str)
                else:
                    info['monthly_listeners'] = m.group(1)
            
            # 2. Redes Sociais no perfil do Spotify
            ig_links = re.findall(r'href=[\"\'](https?://(?:www\.)?instagram\.com/[a-zA-Z0-9_.@\-]+)/?[\"\']', html)
            if ig_links:
                info['instagram'] = ig_links[0].rstrip('/')
            
            tw_links = re.findall(r'href=[\"\'](https?://(?:www\.)?(?:twitter\.com|x\.com)/[a-zA-Z0-9_.@\-]+)/?[\"\']', html)
            if tw_links:
                info['twitter'] = tw_links[0].rstrip('/')
                
            fb_links = re.findall(r'href=[\"\'](https?://(?:www\.)?facebook\.com/[a-zA-Z0-9_.@\-]+)/?[\"\']', html)
            if fb_links:
                info['facebook'] = fb_links[0].rstrip('/')
                
            tt_links = re.findall(r'href=[\"\'](https?://(?:www\.)?tiktok\.com/@[a-zA-Z0-9_.@\-]+)/?[\"\']', html)
            if tt_links:
                info['tiktok'] = tt_links[0].rstrip('/')

            yt_links = re.findall(r'href=[\"\'](https?://(?:www\.)?youtube\.com/(?:channel/|@)[a-zA-Z0-9_.@\-]+)/?[\"\']', html)
            if yt_links:
                info['youtube'] = yt_links[0].rstrip('/')

    except Exception as e:
        print(f"  [!] Erro ao buscar Spotify ID {artist_id}: {e}")

    return info


def format_number_br(num):
    """Formata número com separadores de milhar em padrão BR (ex: 11.574.456)"""
    if isinstance(num, int):
        return f"{num:,}".replace(',', '.')
    return str(num) if num is not None else ""


def build_inpi_search_url(artist_name):
    """Gera URL de atalho de busca no INPI para o artista"""
    encoded_name = urllib.parse.quote(artist_name.encode('iso-8859-1', errors='ignore'))
    return f"https://busca.inpi.gov.br/pePI/servlet/MarcasServletController?Action=searchMarca&tipoPesquisa=marca&marca={encoded_name}"


def create_excel_report(output_filename, playlist_name, tracks, artists_data):
    """
    Gera a planilha Excel final estilizada exatamente conforme o padrão v.2
    """
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    header_font = Font(name='Aptos Narrow', size=11, bold=True, color='000000')
    data_font = Font(name='Aptos Narrow', size=11, bold=False, color='000000')
    link_font = Font(name='Aptos Narrow', size=11, bold=False, color='0000FF', underline='single')

    # ----------------------------------------------------
    # ABA 1: Top 50 Playlist
    # ----------------------------------------------------
    ws1 = wb.create_sheet(title=f"Top 50 - {playlist_name[:20]}")
    headers1 = ['', 'Song', 'Artist', 'Genres', 'Album', 'Spotify Track Id', 'ISRC']
    ws1.append(headers1)
    
    for t in tracks:
        for artist in t.get('artists', []):
            row = [
                f"{t.get('position', '')} ",
                f" {t.get('name', '')}",
                artist.get('name', ''),
                t.get('genres', ''),
                t.get('album', ''),
                t.get('track_id', ''),
                t.get('isrc', '')
            ]
            ws1.append(row)

    # ----------------------------------------------------
    # ABA 2: Todos os artistas
    # ----------------------------------------------------
    ws2 = wb.create_sheet(title="Todos os artistas")
    headers2 = [
        'Músicas\nno top 50', 'Artista', 'Ouvintes mensais\ndo Spotify',
        'IG', 'Tiktok', 'Youtube',
        'Número', 'Prioridade', '', 'Marca', '', 'Situação', 'Titular', 'Classe', 'Procurador'
    ]
    ws2.append(headers2)

    # ----------------------------------------------------
    # ABA 3: Artistas sem marca
    # ----------------------------------------------------
    ws3 = wb.create_sheet(title="Artistas sem marca")
    headers3 = ['Músicas\nno top 50', 'Artista', 'Ouvintes mensais\ndo Spotify', 'IG', 'Tiktok', 'Youtube']
    ws3.append(headers3)

    # ----------------------------------------------------
    # ABA 4: Artistas com marca
    # ----------------------------------------------------
    ws4 = wb.create_sheet(title="Artistas com marca")
    headers4 = ['Músicas\nno top 50', 'Artista', 'Número', 'Prioridade', '', 'Marca', '', 'Situação', 'Titular', 'Classe']
    ws4.append(headers4)

    # Preenchimento das Abas 2, 3 e 4
    for name, data in artists_data.items():
        count_disp = data['count_display']
        listeners = data['monthly_listeners']
        listeners_str = format_number_br(listeners) if listeners else "N/D"
        spotify_url = data['spotify_url']
        ig_url = data['instagram']
        tt_url = data['tiktok']
        yt_url = data['youtube']

        inpi_records = data.get('inpi_records')
        has_brand = bool(inpi_records)

        # Se tiver registros de marca no INPI
        if has_brand:
            for idx, rec in enumerate(inpi_records):
                # Linha para Aba 2 (Todos os artistas)
                row2 = [
                    count_disp if idx == 0 else "",
                    name if idx == 0 else "",
                    listeners_str if idx == 0 else "",
                    "Ver perfil" if (idx == 0 and ig_url) else ("N/D" if idx == 0 else ""),
                    "Ver perfil" if (idx == 0 and tt_url) else ("N/D" if idx == 0 else ""),
                    "Ver canal" if (idx == 0 and yt_url) else ("N/D" if idx == 0 else ""),
                    str(rec.get('numero', '')),
                    str(rec.get('prioridade', '')),
                    "",
                    str(rec.get('marca', '')),
                    "",
                    str(rec.get('situacao', '')),
                    str(rec.get('titular', '')),
                    str(rec.get('classe', '')),
                    str(rec.get('procurador', ''))
                ]
                ws2.append(row2)
                curr_r2 = ws2.max_row
                if idx == 0 and spotify_url and listeners:
                    ws2.cell(curr_r2, 3).hyperlink = spotify_url
                    ws2.cell(curr_r2, 3).font = link_font
                if idx == 0 and ig_url:
                    ws2.cell(curr_r2, 4).hyperlink = ig_url
                    ws2.cell(curr_r2, 4).font = link_font
                if rec.get('numero_link'):
                    ws2.cell(curr_r2, 7).hyperlink = rec['numero_link']
                    ws2.cell(curr_r2, 7).font = link_font

                # Linha para Aba 4 (Artistas com marca)
                row4 = [
                    count_disp if idx == 0 else "",
                    name if idx == 0 else "",
                    str(rec.get('numero', '')),
                    str(rec.get('prioridade', '')),
                    "",
                    str(rec.get('marca', '')),
                    "",
                    str(rec.get('situacao', '')),
                    str(rec.get('titular', '')),
                    str(rec.get('classe', ''))
                ]
                ws4.append(row4)
                curr_r4 = ws4.max_row
                if rec.get('numero_link'):
                    ws4.cell(curr_r4, 3).hyperlink = rec['numero_link']
                    ws4.cell(curr_r4, 3).font = link_font

        else:
            # Artista sem marca (ou pendente de pesquisa)
            # Aba 2
            row2 = [
                count_disp,
                name,
                listeners_str,
                "Ver perfil" if ig_url else "N/D",
                "Ver perfil" if tt_url else "N/D",
                "Ver canal" if yt_url else "N/D",
                "N/A", "N/A", "", "N/A", "", "N/A", "N/A", "N/A", ""
            ]
            ws2.append(row2)
            curr_r2 = ws2.max_row
            if spotify_url and listeners:
                ws2.cell(curr_r2, 3).hyperlink = spotify_url
                ws2.cell(curr_r2, 3).font = link_font
            if ig_url:
                ws2.cell(curr_r2, 4).hyperlink = ig_url
                ws2.cell(curr_r2, 4).font = link_font

            # Aba 3 (Artistas sem marca)
            row3 = [
                count_disp,
                name,
                listeners_str,
                "Ver perfil" if ig_url else "N/D",
                "Ver perfil" if tt_url else "N/D",
                "Ver canal" if yt_url else "N/D"
            ]
            ws3.append(row3)
            curr_r3 = ws3.max_row
            if spotify_url and listeners:
                ws3.cell(curr_r3, 3).hyperlink = spotify_url
                ws3.cell(curr_r3, 3).font = link_font
            if ig_url:
                ws3.cell(curr_r3, 4).hyperlink = ig_url
                ws3.cell(curr_r3, 4).font = link_font

    # Ajuste automático de largura de colunas para todas as abas
    for ws in [ws1, ws2, ws3, ws4]:
        ws.row_dimensions[1].height = 28
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val = str(cell.value or '')
                if '\n' in val:
                    val = max(val.split('\n'), key=len)
                if len(val) > max_len:
                    max_len = len(val)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    wb.save(output_filename)
    print(f"\n[✔] Planilha salva com sucesso em: {output_filename}")


def load_tracks_from_existing_xlsx(xlsx_path):
    """Carrega as faixas da primeira aba de uma planilha existente (ex: Top 50 do usuário)"""
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb.worksheets[0]
    tracks_dict = {}
    
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not any(row):
            continue
        pos_raw = str(row[0]).strip() if row[0] is not None else ""
        song = str(row[1]).strip() if row[1] is not None else ""
        artist_name = str(row[2]).strip() if row[2] is not None else ""
        genres = str(row[3]).strip() if len(row) > 3 and row[3] is not None else ""
        album = str(row[4]).strip() if len(row) > 4 and row[4] is not None else ""
        track_id = str(row[5]).strip() if len(row) > 5 and row[5] is not None else ""
        isrc = str(row[6]).strip() if len(row) > 6 and row[6] is not None else ""
        
        # Identificador único de faixa
        key = track_id if track_id else f"{pos_raw}_{song}"
        if key not in tracks_dict:
            tracks_dict[key] = {
                'position': pos_raw,
                'name': song,
                'genres': genres,
                'album': album,
                'track_id': track_id,
                'isrc': isrc,
                'artists': []
            }
        tracks_dict[key]['artists'].append({'name': artist_name, 'id': None})
        
    return list(tracks_dict.values())


def load_inpi_database_from_xlsx(xlsx_path):
    """Extrai marcas já cadastradas na aba 'Artistas com marca' para reaproveitar"""
    wb = openpyxl.load_workbook(xlsx_path, data_only=False)
    if 'Artistas com marca' not in wb.sheetnames:
        return {}
    
    ws = wb['Artistas com marca']
    inpi_map = {}
    current_artist = None

    for r in range(2, ws.max_row + 1):
        artist_cell = ws.cell(r, 2).value
        if artist_cell and str(artist_cell).strip():
            current_artist = str(artist_cell).strip()
        
        num_cell = ws.cell(r, 3)
        if not num_cell.value:
            continue
            
        num_val = str(num_cell.value).strip()
        num_link = num_cell.hyperlink.target if num_cell.hyperlink else None
        
        record = {
            'numero': num_val,
            'numero_link': num_link,
            'prioridade': ws.cell(r, 4).value,
            'marca': ws.cell(r, 6).value,
            'situacao': ws.cell(r, 8).value,
            'titular': ws.cell(r, 9).value,
            'classe': ws.cell(r, 10).value
        }
        
        if current_artist:
            if current_artist not in inpi_map:
                inpi_map[current_artist] = []
            inpi_map[current_artist].append(record)

    return inpi_map

