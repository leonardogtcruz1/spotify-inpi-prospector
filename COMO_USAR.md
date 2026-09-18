# 📘 Guia de Uso: Automação de Planilhas Spotify & INPI

Este robô automatiza 100% da criação da sua planilha: ele lê qualquer **link de playlist do Spotify** ou **arquivo de Top 50**, calcula os ouvintes mensais em tempo real, descobre e coleta seguidores do Instagram, canais do YouTube (com número de inscritos) e perfis do TikTok (com links clicáveis), e cruza todos os artistas com registros de marcas no INPI.

---

## 🌟 Como Usar no Dia a Dia (3 Formas Simples)

Você não precisa entender de programação. Escolha a forma que achar mais prática:

### 🌟 Opção 1: Pelo Painel Web no Navegador (Mais Visual e Amigável)
Se você prefere uma interface gráfica bonita no navegador, com barra de progresso visual, cards e botão de download direto:

1. Dê **2 cliques** no arquivo:
   - **No Mac**: `iniciar_web.command`
   - **No Windows**: `iniciar_web.bat`
2. Uma tela preta abrirá para iniciar o robô e seu navegador padrão abrirá sozinho em:
   👉 **`http://localhost:8000`**
3. No painel web:
   - Cole o **link da playlist do Spotify** OU arraste sua **planilha do Chosic**.
   - Clique em **"Iniciar Automação Completa"**.
   - Acompanhe a barra de progresso, cada artista sendo enriquecido ao vivo e os logs do terminal.
   - Quando terminar, veja os cards de resultados (total de leads sem marca) e clique no botão verde para **Baixar a Planilha (.xlsx)**!
   - Você também pode clicar em **"Histórico de Planilhas"** no topo para baixar arquivos gerados em dias anteriores.

---

### Opção 2: Pelo Atalho Rápido de Terminal (Sem Abrir Navegador)
Se você prefere a execução rápida em janela de terminal:

1. Dê **2 cliques** no arquivo:
   - **No Mac**: `executar.command`
   - **No Windows**: `executar.bat`
2. Quando a tela pedir:
   - Se for rodar uma playlist, cole o link e aperte **ENTER**.
   - Se for rodar a planilha que está na pasta, apenas aperte **ENTER**.

---

### Opção 3: Baixando do Chosic (Para Gráficos Oficiais do Top 50 Brasil)
As paradas de gráfico oficiais do Spotify (como o *Top 50 - Brasil* oficial) possuem restrições externas de scraper. A forma mais fácil de processá-las é:

1. Acesse o site gratuito: [chosic.com/spotify-playlist-exporter](https://www.chosic.com/spotify-playlist-exporter/)
2. Cole o link do Top 50 Brasil (`https://open.spotify.com/playlist/37i9dQZEVXbMXbN3b9qiWe`) e baixe a planilha (.xlsx ou .csv).
3. Arraste-a para dentro do Painel Web (Opção 1) OU para dentro da pasta do projeto e dê 2 cliques em `executar.command` / `executar.bat`.

---

## 📁 Onde Fica a Planilha Gerada?

Assim que o robô terminar, uma mensagem verde de sucesso aparecerá na tela.
Basta abrir a pasta **`output/`**:
- Se usou uma playlist por link: `output/[Nome da Playlist] DD.MM.AA - Automatizada.xlsx` (ex: `output/RapCaviar 18.09.26 - Automatizada.xlsx`).
- Se usou um arquivo do Top 50: `output/Top 50 BR Spotify DD.MM.AA - Automatizada.xlsx`.

> 📌 **Atenção sobre novas execuções**: Se você rodar o robô mais de uma vez **no mesmo dia**, ele atualizará a planilha do dia. Se rodar em **dias diferentes**, ele criará arquivos separados com a data de cada dia (ex: `18.09.26`, `25.09.26`), preservando todo o seu histórico!

---

## 📊 3. Entendendo as 4 Abas Geradas

A planilha gerada mantém rigorosamente a estrutura original do seu projeto:

1. **`Top 50 - [Nome]`**:
   - As 50 faixas detalhadas, com feats/colaborações desmembrados linha a linha.
   - Colunas: Posição, Música, Artista, Gênero, Álbum, Spotify Track ID e ISRC.

2. **`Todos os artistas`**:
   - Todos os artistas únicos em ordem alfabética (A-Z).
   - `Músicas no top 50`: exibe o número se o artista tiver 2 ou mais músicas (ex: 2, 3, 4...).
   - `Ouvintes mensais do Spotify`: número formatado com ponto e link clicável direto para o perfil do artista.
   - `IG`, `Tiktok`, `Youtube`: links clicáveis diretos para os canais oficiais.
   - Colunas do INPI: Número do pedido, Prioridade, Marca, Situação, Titular e Classe.

3. **`Artistas sem marca` (SEUS LEADS DE PROSPECÇÃO)**:
   - Contém **apenas** os artistas que não têm registro de marca no INPI.
   - Ideal para focar seu contato comercial ou prospecção de assessoria jurídica/registro.
   - Na coluna `Número`, há um link direto de pesquisa rápida no INPI em 1 clique.

4. **`Artistas com marca`**:
   - Contém todos os processos catalogados no INPI com link azul clicável para abrir a tela oficial do processo no portal do INPI.

---

## 🛡 4. Como o Módulo do INPI Funciona

1. **Reaproveitamento Histórico (Cache inteligente)**:
   - Toda vez que o script roda, ele lê as planilhas anteriores da pasta raiz E da pasta `output/`. Se um artista já teve sua marca cadastrada na semana anterior, ele reaproveita instantaneamente os dados e links do INPI.
2. **Busca ao Vivo**:
   - Para artistas novos, o script tenta consultar o sistema pePI do INPI.
3. **Links Inteligentes em 1 Clique**:
   - Como o site do INPI frequentemente passa por manutenções ou instabilidade, para qualquer artista sem marca confirmada o script insere um link pré-configurado que abre a busca daquele artista direto no portal do INPI.

---

## 🔍 5. Como Funciona a Coleta de Redes Sociais & Memória Contínua

O script possui um sistema inteligente de busca e preservação de dados:

1. **Spotify**:
   - Conecta-se à página pública de cada artista.
   - Extrai a quantidade exata de **Ouvintes Mensais** (ex: `16.098.634`) e gera o link clicável direto para o perfil.
   - Lê os links de redes sociais declarados na bio do artista.

2. **YouTube (Descoberta Automática)**:
   - Para cada artista, o script busca automaticamente pelo canal oficial no YouTube (`{Artista} oficial`).
   - Identifica o `@handle` oficial e extrai a contagem de inscritos (ex: `17,7 mi de inscritos`, `166 mil inscritos`).
   - Insere o número de inscritos com link clicável para o canal. Se o canal existir mas a contagem estiver oculta, exibe `"Ver canal"` clicável.

3. **TikTok (Descoberta Automática)**:
   - Usa o `@handle` do Instagram do artista para testar variações no TikTok.
   - Coleta a quantidade de seguidores em tempo real formatada no padrão da rede (ex: `29.5K`, `1.2M`).

4. **Memória Contínua (Seus ajustes manuais nunca são perdidos)**:
   - Se você abrir a planilha gerada e preencher ou corrigir manualmente a rede social de algum artista (ou cadastrar uma marca nova), **o script aprende e memoriza isso**.
   - Nas semanas seguintes, ao rodar uma nova playlist, o script lê as planilhas anteriores e **prioriza os dados que você já conferiu**, evitando trabalho repetido!

---

## 💡 6. Dicas Importantes e Cuidados ao Rodar

* **Feche a planilha no Excel antes de rodar**: Se você estiver com a planilha de saída aberta no Microsoft Excel, o Excel pode bloquear a regravação do arquivo. Feche a aba ou a janela antes de rodar o `./run.sh`.
* **Conexão com a Internet**: O script precisa de conexão com a internet para consultar ouvintes no Spotify, canais no YouTube e o sistema do INPI.
* **Músicas com vários artistas (Feats)**: Não precisa separar manualmente os artistas no Chosic. O script já detecta vírgulas, `&`, `feat.`, `ft.` e separa cada artista em uma linha própria automaticamente.
* **Ignorar consulta ao vivo do INPI**: Se o site do INPI estiver muito lento e você quiser gerar a planilha em segundos usando apenas o histórico e links rápidos:
  ```bash
  ./run.sh --skip-live-inpi
  ```

---

## ⚙ 7. (Opcional) Configurando Chaves do Spotify Developer

Se você quiser processar até mesmo as paradas de gráficos oficiais (como o Top 50 Brasil oficial `37i9dQZEVX...`) direto pelo link sem precisar do Chosic:

1. Acesse o portal gratuito: [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) e faça login com sua conta Spotify.
2. Clique em **Create app**, dê qualquer nome e copie o `Client ID` e `Client Secret`.
3. Você pode:
   - Salvar essas chaves em um arquivo chamado `spotify_config.json` na pasta do projeto:
     ```json
     {
       "client_id": "seu_client_id_aqui",
       "client_secret": "seu_client_secret_aqui"
     }
     ```
   - Ou simplesmente colar o link do Top 50 no robô: na primeira vez, o terminal perguntará o seu Client ID e Client Secret e salvará tudo sozinho para você!
   - Ou definir variáveis de ambiente `SPOTIPY_CLIENT_ID` e `SPOTIPY_CLIENT_SECRET`.

Depois disso, você pode rodar qualquer link de gráfico oficial diretamente:
```bash
./run.sh "https://open.spotify.com/playlist/37i9dQZEVXbMXbN3b9qiWe"
```

---

## 🛠 8. Solução de Problemas (FAQ)

### "Deu 'Permission denied' ao tentar rodar `./run.sh`"
Se você moveu os arquivos ou baixou em outra máquina, dê permissão de execução com o comando:
```bash
chmod +x run.sh
```

### "Como rodar em outro computador do zero?"
Se você transferir a pasta para outro computador (Mac, Windows ou Linux), basta ter o Python 3.9+ instalado e executar uma única vez:
```bash
python3 -m venv .venv
source .venv/bin/activate       # No Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
Depois disso, basta rodar `./run.sh` normalmente.

### "Um artista novo veio com 'Ver perfil' ou 'N/D' no YouTube/TikTok"
Isso ocorre quando o artista não disponibilizou links públicos na bio do Spotify ou usa um nome artístico genérico que não bateu com canal verificado. Você pode colar o link diretamente na célula do Excel. Nas próximas semanas, o script vai reutilizar automaticamente o que você colocou!

### "Apareceu aviso de 'INPI OFFLINE' no terminal"
O portal do INPI (pePI) frequentemente passa por instabilidades aos finais de semana e noites. Quando isso acontece, o script não trava: ele marca o artista para prospecção e insere na coluna o botão **"Pesquisar INPI"**, que abre a busca daquele nome no portal do INPI com apenas 1 clique no navegador.

---

## 📂 9. Estrutura de Arquivos do Projeto

- `automator.py`: Código principal de orquestração do robô.
- `run.sh`: Atalho executável simples para rodar no dia a dia.
- `output/`: Pasta onde ficam organizadas todas as planilhas geradas.
- `modules/spotify_service.py`: Leitura de faixas, forward-fill e scraping de ouvintes do Spotify.
- `modules/social_service.py`: Enriquecimento e descoberta automática de Instagram, TikTok e YouTube.
- `modules/inpi_service.py`: Consulta, persistência histórica e geração de links de marcas no INPI.
- `modules/excel_builder.py`: Construtor do Excel com estilos visuais, fontes Aptos Narrow e hyperlinks.

