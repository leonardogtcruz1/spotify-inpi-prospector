import re
import urllib.parse
import unicodedata
import openpyxl
import requests

INPI_BASE_URL = "https://busca.inpi.gov.br/pePI"

INPI_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Origin': 'https://busca.inpi.gov.br',
    'Referer': 'https://busca.inpi.gov.br/pePI/jsp/marcas/Pesquisa_classe_basica.jsp'
}


def normalize_text(text):
    """Normaliza texto removendo acentos e convertendo para minúsculas"""
    if not text:
        return ""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('ASCII').strip().lower()


def build_inpi_direct_url(artist_name):
    """
    Gera um link inteligente pré-configurado de pesquisa de marcas no INPI
    """
    safe_name = urllib.parse.quote(artist_name.strip())
    return f"https://busca.inpi.gov.br/pePI/servlet/MarcasServletController?Action=searchMarca&tipoPesquisa=marca&marca={safe_name}"


def load_known_marcas_from_excel(file_path):
    """
    Carrega o histórico de marcas já pesquisadas na planilha original do usuário.
    Garante que marcas já encontradas não precisem ser pesquisadas novamente.
    """
    known_marcas = {}
    try:
        wb = openpyxl.load_workbook(file_path, data_only=False)
        target_sheet = None
        for name in ['Artistas com marca', 'Todos os artistas']:
            if name in wb.sheetnames:
                target_sheet = wb[name]
                break

        if not target_sheet:
            return known_marcas

        current_artist = None
        for r in range(2, target_sheet.max_row + 1):
            art_val = target_sheet.cell(r, 2).value
            if art_val and str(art_val).strip():
                current_artist = str(art_val).strip()

            num_cell = target_sheet.cell(r, 3 if target_sheet.title == 'Artistas com marca' else 7)
            if not num_cell.value:
                continue

            num_str = str(num_cell.value).strip()
            if num_str.upper() in ['N/A', 'N/D', '']:
                continue

            num_link = num_cell.hyperlink.target if num_cell.hyperlink else None
            prio_val = target_sheet.cell(r, 4 if target_sheet.title == 'Artistas com marca' else 8).value
            marca_val = target_sheet.cell(r, 6 if target_sheet.title == 'Artistas com marca' else 10).value
            sit_val = target_sheet.cell(r, 8 if target_sheet.title == 'Artistas com marca' else 12).value
            tit_val = target_sheet.cell(r, 9 if target_sheet.title == 'Artistas com marca' else 13).value
            classe_val = target_sheet.cell(r, 10 if target_sheet.title == 'Artistas com marca' else 14).value
            proc_val = target_sheet.cell(r, 15).value if target_sheet.title == 'Todos os artistas' else ""

            rec = {
                'numero': num_str,
                'numero_link': num_link,
                'prioridade': prio_val or '',
                'marca': marca_val or '',
                'situacao': sit_val or '',
                'titular': tit_val or '',
                'classe': classe_val or '',
                'procurador': proc_val or ''
            }

            if current_artist:
                norm_key = normalize_text(current_artist)
                if norm_key not in known_marcas:
                    known_marcas[norm_key] = []
                known_marcas[norm_key].append(rec)
                
                # Também armazena a versão sem normalização para garantia
                raw_key = current_artist.strip().lower()
                if raw_key not in known_marcas:
                    known_marcas[raw_key] = known_marcas[norm_key]

    except Exception as e:
        print(f"  [!] Aviso ao carregar base histórica de marcas: {e}")

    return known_marcas


def init_inpi_session():
    """
    Inicia uma sessão anônima no sistema pePI do INPI
    """
    session = requests.Session()
    session.headers.update(INPI_HEADERS)
    try:
        resp_login = session.get(f"{INPI_BASE_URL}/servlet/LoginController?action=login", timeout=10)
        resp_menu = session.get(f"{INPI_BASE_URL}/jsp/marcas/Pesquisa_classe_basica.jsp", timeout=10)
        return session
    except Exception:
        return None


def search_inpi_live(artist_name, session=None):
    """
    Tenta consultar marcas registradas para o artista no pePI do INPI.
    Retorna uma lista de registros encontrados ou None se offline/sem resultados.
    """
    if not session:
        session = init_inpi_session()
        if not session:
            return None, "offline"

    search_url = f"{INPI_BASE_URL}/servlet/MarcasServletController"
    data = {
        'Action': 'searchMarca',
        'tipoPesquisa': 'marca',
        'marca': artist_name,
        'classeInter': '',
        'registerPerPage': '20',
        'botao': 'pesquisar'
    }

    try:
        resp = session.post(search_url, data=data, timeout=12)
        resp.encoding = 'iso-8859-1'
        html = resp.text

        if "SQLException" in html or "Banco de Marcas inacessível" in html:
            return None, "offline"

        if "Nenhum resultado foi encontrado" in html or "não retornou resultado" in html:
            return [], "sem_marca"

        records = []
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
        for r_html in rows:
            detail_m = re.search(r'href=[\"\'](/pePI/servlet/MarcasServletController\?Action=detail&CodPedido=[0-9]+)[\"\'][^>]*>([0-9]+)</a>', r_html)
            if detail_m:
                detail_path, num_processo = detail_m.groups()
                full_link = f"https://busca.inpi.gov.br{detail_path}"
                
                cols = [re.sub(r'<[^>]+>', '', c).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', r_html, re.DOTALL)]
                
                prioridade = cols[1] if len(cols) > 1 else ""
                marca = cols[2] if len(cols) > 2 else artist_name
                situacao = cols[4] if len(cols) > 4 else ""
                titular = cols[5] if len(cols) > 5 else ""
                classe = cols[6] if len(cols) > 6 else ""

                records.append({
                    'numero': num_processo,
                    'numero_link': full_link,
                    'prioridade': prioridade,
                    'marca': marca,
                    'situacao': situacao,
                    'titular': titular,
                    'classe': classe,
                    'procurador': ''
                })

        if records:
            return records, "encontrada"
        else:
            return [], "sem_marca"

    except Exception as e:
        return None, f"erro: {e}"
