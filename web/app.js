// Spotify & INPI Lead Prospector - Frontend Controller
document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');
  const playlistUrlInput = document.getElementById('playlistUrlInput');
  const btnClearUrl = document.getElementById('btnClearUrl');
  
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  const fileChip = document.getElementById('fileChip');
  const fileNameText = document.getElementById('fileNameText');
  const btnRemoveFile = document.getElementById('btnRemoveFile');
  
  const skipLiveInpiCheckbox = document.getElementById('skipLiveInpiCheckbox');
  const btnStartPipeline = document.getElementById('btnStartPipeline');
  
  // Progress Elements
  const topProgressContainer = document.getElementById('topProgressContainer');
  const topProgressBar = document.getElementById('topProgressBar');
  const headerStatusPill = document.getElementById('headerStatusPill');
  const headerStatusText = document.getElementById('headerStatusText');

  const progressSection = document.getElementById('progressSection');
  const progressStepTitle = document.getElementById('progressStepTitle');
  const progressSubtitle = document.getElementById('progressSubtitle');
  const progressPercentBadge = document.getElementById('progressPercentBadge');
  const progressBarFill = document.getElementById('progressBarFill');
  
  // Spotlight Elements
  const spotlightName = document.getElementById('spotlightName');
  const spotlightMarcaTag = document.getElementById('spotlightMarcaTag');
  const spotlightListeners = document.getElementById('spotlightListeners');
  const spotlightIG = document.getElementById('spotlightIG');
  const spotlightYT = document.getElementById('spotlightYT');
  const spotlightTikTok = document.getElementById('spotlightTikTok');
  
  // Console & Debug Elements
  const debugLogsDrawer = document.getElementById('debugLogsDrawer');
  const btnToggleConsole = document.getElementById('btnToggleConsole');
  const consoleBody = document.getElementById('consoleBody');
  const consoleArrow = document.getElementById('consoleArrow');
  const consoleOutput = document.getElementById('consoleOutput');
  const logsCountBadge = document.getElementById('logsCountBadge');
  const btnCopyLogs = document.getElementById('btnCopyLogs');
  const btnCopyLogsText = document.getElementById('btnCopyLogsText');
  const btnClearLogs = document.getElementById('btnClearLogs');
  const btnNavToggleLogs = document.getElementById('btnNavToggleLogs');
  const btnScrollToLogs = document.getElementById('btnScrollToLogs');

  // Error Banner Elements (Vermelho vivo)
  const errorBannerCard = document.getElementById('errorBannerCard');
  const errorMessageText = document.getElementById('errorMessageText');
  const btnErrorCopy = document.getElementById('btnErrorCopy');
  const btnErrorViewLogs = document.getElementById('btnErrorViewLogs');
  const btnErrorRetry = document.getElementById('btnErrorRetry');
  
  // Results Elements
  const resultsSection = document.getElementById('resultsSection');
  const resultsFilenameText = document.getElementById('resultsFilenameText');
  const btnDownloadFile = document.getElementById('btnDownloadFile');
  const statTracks = document.getElementById('statTracks');
  const statArtists = document.getElementById('statArtists');
  const statSemMarca = document.getElementById('statSemMarca');
  const statComMarca = document.getElementById('statComMarca');
  
  // Table Elements
  const filterBtns = document.querySelectorAll('.filter-btn');
  const countFilterAll = document.getElementById('countFilterAll');
  const countFilterLeads = document.getElementById('countFilterLeads');
  const countFilterMarcas = document.getElementById('countFilterMarcas');
  const tableSearchInput = document.getElementById('tableSearchInput');
  const artistsTableBody = document.getElementById('artistsTableBody');
  
  // Modals
  const historyModal = document.getElementById('historyModal');
  const btnOpenHistory = document.getElementById('btnOpenHistory');
  const btnCloseHistory = document.getElementById('btnCloseHistory');
  const historyList = document.getElementById('historyList');
  
  const configModal = document.getElementById('configModal');
  const btnOpenConfig = document.getElementById('btnOpenConfig');
  const btnCloseConfig = document.getElementById('btnCloseConfig');
  const btnCancelConfig = document.getElementById('btnCancelConfig');
  const btnSaveConfig = document.getElementById('btnSaveConfig');
  const cfgClientId = document.getElementById('cfgClientId');
  const cfgClientSecret = document.getElementById('cfgClientSecret');
  const configStatusMessage = document.getElementById('configStatusMessage');

  // State
  let currentTargetType = 'playlist'; // 'playlist' | 'file'
  let selectedFile = null;
  let activeEventSource = null;
  let currentJobId = null;
  let allArtists = [];
  let currentFilter = 'all'; // 'all' | 'sem_marca' | 'com_marca'
  let searchQuery = '';

  // 1. Tab Switching
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));
      
      btn.classList.add('active');
      const targetTab = btn.getAttribute('data-tab');
      document.getElementById(targetTab).classList.add('active');
      
      currentTargetType = (targetTab === 'playlistTab') ? 'playlist' : 'file';
    });
  });

  // 2. Botão Destaque: Pegar Top 50 Brasil
  const btnLoadTop50 = document.getElementById('btnLoadTop50');
  const TOP_50_BRASIL_URL = 'https://open.spotify.com/playlist/37i9dQZEVXbMXbN3EUUhlg';

  if (btnLoadTop50) {
    btnLoadTop50.addEventListener('click', () => {
      playlistUrlInput.value = TOP_50_BRASIL_URL;
      playlistUrlInput.focus();

      btnLoadTop50.classList.add('selected');
      const actionPill = btnLoadTop50.querySelector('.btn-action-pill');
      if (actionPill) {
        actionPill.innerHTML = '✓ Top 50 Selecionada!';
        actionPill.style.background = '#ffffff';
        actionPill.style.color = '#000000';
      }

      playlistUrlInput.classList.add('highlight-green');
      setTimeout(() => {
        playlistUrlInput.classList.remove('highlight-green');
        if (actionPill) {
          actionPill.innerHTML = '⚡ Inserir Top 50';
          actionPill.style.background = 'var(--spotify-green)';
          actionPill.style.color = '#000000';
        }
      }, 1500);
    });
  }

  // Atualiza estado do botão ao digitar ou colar na caixa de texto
  if (playlistUrlInput) {
    playlistUrlInput.addEventListener('input', () => {
      if (btnLoadTop50) {
        if (playlistUrlInput.value.includes('37i9dQZEVXbMXbN3EUUhlg')) {
          btnLoadTop50.classList.add('selected');
        } else {
          btnLoadTop50.classList.remove('selected');
        }
      }
    });
  }

  // 3. Limpar URL input
  if (btnClearUrl) {
    btnClearUrl.addEventListener('click', () => {
      playlistUrlInput.value = '';
      if (btnLoadTop50) btnLoadTop50.classList.remove('selected');
      playlistUrlInput.focus();
    });
  }

  // 4. Drag & Drop File Handling
  if (dropZone) {
    dropZone.addEventListener('click', (e) => {
      if (e.target !== btnRemoveFile) {
        fileInput.click();
      }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
      });
    });

    dropZone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      if (dt.files && dt.files.length > 0) {
        handleFileSelected(dt.files[0]);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files && fileInput.files.length > 0) {
        handleFileSelected(fileInput.files[0]);
      }
    });

    btnRemoveFile.addEventListener('click', (e) => {
      e.stopPropagation();
      selectedFile = null;
      fileInput.value = '';
      fileChip.style.display = 'none';
      document.querySelector('.drop-title').style.display = 'block';
      document.querySelector('.drop-hint').style.display = 'block';
    });
  }

  function handleFileSelected(file) {
    const validExts = ['.xlsx', '.csv'];
    const name = file.name.toLowerCase();
    if (!validExts.some(ext => name.endsWith(ext))) {
      alert('Por favor, selecione um arquivo válido .xlsx ou .csv');
      return;
    }
    selectedFile = file;
    fileNameText.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    fileChip.style.display = 'inline-flex';
    document.querySelector('.drop-title').style.display = 'none';
    document.querySelector('.drop-hint').style.display = 'none';
  }

  // 5. Console & Debug Drawer Management (Sempre recolhido por padrão)
  let consoleOpen = false;
  let totalLogEvents = 0;

  function appendLog(line) {
    if (!consoleOutput) return;
    if (consoleOutput.textContent.includes('Sistema pronto. Logs detalhados aparecerão')) {
      consoleOutput.textContent = '';
    }
    const timestamp = new Date().toLocaleTimeString();
    const formattedLine = line.startsWith('[') ? line : `[${timestamp}] ${line}`;
    consoleOutput.textContent += formattedLine + '\n';
    totalLogEvents++;
    if (logsCountBadge) {
      logsCountBadge.textContent = `${totalLogEvents} evento${totalLogEvents === 1 ? '' : 's'}`;
    }
    scrollConsoleToBottom();
  }

  function setConsoleOpen(open) {
    consoleOpen = open;
    if (consoleBody) {
      consoleBody.style.display = consoleOpen ? 'block' : 'none';
    }
    if (consoleArrow) {
      consoleArrow.textContent = consoleOpen ? '▼ Recolher' : '► Expandir';
    }
    if (debugLogsDrawer) {
      debugLogsDrawer.classList.toggle('expanded', consoleOpen);
    }
    if (consoleOpen) {
      scrollConsoleToBottom();
    }
  }

  if (btnToggleConsole) {
    btnToggleConsole.addEventListener('click', () => {
      setConsoleOpen(!consoleOpen);
    });
  }

  if (btnNavToggleLogs) {
    btnNavToggleLogs.addEventListener('click', () => {
      setConsoleOpen(true);
      if (debugLogsDrawer) {
        debugLogsDrawer.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
  }

  if (btnScrollToLogs) {
    btnScrollToLogs.addEventListener('click', () => {
      setConsoleOpen(true);
      if (debugLogsDrawer) {
        debugLogsDrawer.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
  }

  // 6. Botão de Copiar Logs para Suporte
  if (btnCopyLogs) {
    btnCopyLogs.addEventListener('click', async (e) => {
      e.stopPropagation();
      await copyLogsToClipboard();
    });
  }

  // Ações do Banner de Erro em Destaque Vermelho
  if (btnErrorCopy) {
    btnErrorCopy.addEventListener('click', async (e) => {
      e.stopPropagation();
      await copyLogsToClipboard();
      const originalText = btnErrorCopy.textContent;
      btnErrorCopy.textContent = '✓ Logs Copiados!';
      setTimeout(() => {
        btnErrorCopy.textContent = originalText;
      }, 2500);
    });
  }

  if (btnErrorViewLogs) {
    btnErrorViewLogs.addEventListener('click', (e) => {
      e.stopPropagation();
      setConsoleOpen(true);
      if (debugLogsDrawer) {
        debugLogsDrawer.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
  }

  if (btnErrorRetry) {
    btnErrorRetry.addEventListener('click', (e) => {
      e.stopPropagation();
      btnStartPipeline.click();
    });
  }

  if (btnClearLogs) {
    btnClearLogs.addEventListener('click', (e) => {
      e.stopPropagation();
      if (consoleOutput) {
        consoleOutput.textContent = '[INFO] Janela de logs limpa.\n';
        totalLogEvents = 1;
        if (logsCountBadge) logsCountBadge.textContent = '1 evento';
      }
    });
  }

  async function copyLogsToClipboard() {
    if (!consoleOutput) return;
    const rawLogs = consoleOutput.textContent.trim();
    const timestamp = new Date().toLocaleString('pt-BR');
    const fullReport = [
      `=======================================================`,
      `  LOGS DE DIAGNÓSTICO DO APP (SPOTIFY & INPI PROSPECTOR)`,
      `=======================================================`,
      `Data/Hora: ${timestamp}`,
      `URL: ${window.location.href}`,
      `Navegador: ${navigator.userAgent}`,
      `Job ID: ${currentJobId || 'Nenhum job recente'}`,
      `Tipo de Entrada: ${currentTargetType}`,
      `Total Artistas: ${allArtists.length}`,
      `-------------------------------------------------------`,
      `HISTÓRICO COMPLETO DOS EVENTOS:`,
      `-------------------------------------------------------`,
      rawLogs || '(Nenhum log registrado até o momento)'
    ].join('\n');

    let copied = false;
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(fullReport);
        copied = true;
      }
    } catch (_) {}

    if (!copied) {
      try {
        const tempText = document.createElement('textarea');
        tempText.value = fullReport;
        tempText.style.position = 'fixed';
        tempText.style.left = '-9999px';
        document.body.appendChild(tempText);
        tempText.select();
        document.execCommand('copy');
        document.body.removeChild(tempText);
        copied = true;
      } catch (_) {}
    }

    if (copied) {
      btnCopyLogs.classList.add('copied');
      if (btnCopyLogsText) btnCopyLogsText.textContent = '✓ Logs Copiados com Sucesso!';
      setTimeout(() => {
        btnCopyLogs.classList.remove('copied');
        if (btnCopyLogsText) btnCopyLogsText.textContent = '📋 Copiar Todos os Logs';
      }, 2500);
    } else {
      alert('Não foi possível copiar automaticamente para a área de transferência. Selecione o texto e copie manualmente.');
    }
  }

  // Captura erros globais do navegador e anexa aos logs para debug
  window.addEventListener('error', (e) => {
    appendLog(`[ERRO NAVEGADOR] ${e.message} (${e.filename}:${e.lineno})`);
  });
  window.addEventListener('unhandledrejection', (e) => {
    appendLog(`[ERRO PROMISE] ${e.reason}`);
  });

  // 6. Iniciar Pipeline
  btnStartPipeline.addEventListener('click', async () => {
    const formData = new FormData();
    formData.append('target_type', currentTargetType);
    formData.append('skip_live_inpi', skipLiveInpiCheckbox.checked ? 'true' : 'false');

    if (currentTargetType === 'playlist') {
      const url = playlistUrlInput.value.trim();
      if (!url) {
        alert('Por favor, cole a URL da playlist do Spotify.');
        playlistUrlInput.focus();
        return;
      }
      formData.append('playlist_url', url);
    } else {
      if (!selectedFile) {
        alert('Por favor, selecione ou arraste um arquivo .xlsx ou .csv');
        return;
      }
      formData.append('file', selectedFile);
    }

    // Reset UI State
    btnStartPipeline.disabled = true;
    btnStartPipeline.classList.remove('btn-failed');
    btnStartPipeline.innerHTML = '<span class="btn-icon">⏳</span> Iniciando Robô...';
    
    // Esconder banner de erro anterior se houver
    if (errorBannerCard) errorBannerCard.style.display = 'none';

    allArtists = [];
    renderTable();
    totalLogEvents = 0;
    if (consoleOutput) consoleOutput.textContent = '';
    appendLog('[INÍCIO] Conectando ao serviço em streaming contínuo...');
    
    progressSection.style.display = 'block';
    resultsSection.style.display = 'none';
    progressPercentBadge.textContent = '0%';
    progressPercentBadge.style.color = '';
    progressBarFill.style.width = '0%';
    progressBarFill.style.background = '';
    progressStepTitle.textContent = 'Conectando ao serviço...';
    progressSubtitle.textContent = 'Aguarde o carregamento inicial da playlist...';

    // Ativa linha de progresso no topo e badge de status
    if (topProgressContainer) topProgressContainer.style.display = 'block';
    if (topProgressBar) {
      topProgressBar.classList.remove('error-bar');
      topProgressBar.style.width = '5%';
    }
    if (headerStatusPill) {
      headerStatusPill.classList.remove('error-pill');
      headerStatusPill.style.display = 'flex';
      if (headerStatusText) headerStatusText.textContent = 'Iniciando robô...';
    }
    document.title = '▶ [Iniciando...] Spotify Prospector';
    
    // Smooth scroll to progress section
    progressSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    try {
      await runStreamingPipeline(formData);
    } catch (err) {
      console.warn('Falha no streaming direto, tentando fallback padrão...', err);
      // Fallback para POST /api/jobs se o streaming falhar
      try {
        const response = await fetch('/api/jobs', {
          method: 'POST',
          body: formData
        });
        if (!response.ok) {
          let errDetail = 'Erro ao iniciar o processamento.';
          try {
            const errData = await response.json();
            errDetail = errData.detail || errDetail;
          } catch (_) {}
          throw new Error(errDetail);
        }
        const resData = await response.json();
        currentJobId = resData.job_id;
        listenToJobEvents(currentJobId);
      } catch (fallbackErr) {
        showAppError(fallbackErr.message || err.message);
      }
    }
  });

  // Exibe erro crítico de forma destacada em vermelho vivo
  function showAppError(errMsg) {
    const cleanMsg = (errMsg || 'Ocorreu um erro inesperado durante a execução da automação.').toString();
    console.error('App Pipeline Error:', cleanMsg);

    // 1. Mostrar banner vermelho com destaque
    if (errorBannerCard) {
      errorBannerCard.style.display = 'flex';
      if (errorMessageText) {
        errorMessageText.textContent = cleanMsg;
      }
      errorBannerCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    // 2. Destacar barra superior e status pill em vermelho
    if (topProgressContainer) topProgressContainer.style.display = 'block';
    if (topProgressBar) {
      topProgressBar.classList.add('error-bar');
      topProgressBar.style.width = '100%';
    }
    if (headerStatusPill) {
      headerStatusPill.style.display = 'flex';
      headerStatusPill.classList.add('error-pill');
      if (headerStatusText) headerStatusText.textContent = '⚠️ Erro na automação';
    }

    // 3. Atualizar card de progresso em vermelho
    if (progressBarFill) {
      progressBarFill.style.background = 'linear-gradient(90deg, #ef4444, #dc2626)';
    }
    if (progressStepTitle) {
      progressStepTitle.innerHTML = '<span style="color: #ef4444; font-weight: 700;">⚠️ Automação Interrompida com Erro</span>';
    }
    if (progressSubtitle) {
      progressSubtitle.innerHTML = `<span style="color: #f87171;">${cleanMsg}</span>`;
    }
    if (progressPercentBadge) {
      progressPercentBadge.style.color = '#ef4444';
      progressPercentBadge.textContent = 'Erro';
    }

    // 4. Botão de ação volta como "Tentar Novamente" com estilo vermelho
    btnStartPipeline.disabled = false;
    btnStartPipeline.classList.add('btn-failed');
    btnStartPipeline.innerHTML = '<span class="btn-icon">⚠️</span> Falhou — Tentar Novamente';

    document.title = '❌ [Erro] Spotify Prospector';

    // 5. Registrar log crítico em destaque
    appendLog(`[ERRO CRÍTICO] ${cleanMsg}`);

    // 6. Abrir o console de logs para facilitar diagnóstico
    setConsoleOpen(true);
  }

  // Função para disparar o download automático imediato da planilha gerada
  function triggerAutoDownload(data) {
    let downloadUrl = data.download_url;

    if (data.file_base64) {
      try {
        const byteCharacters = atob(data.file_base64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], {
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        });
        downloadUrl = URL.createObjectURL(blob);
      } catch (e) {
        console.warn('Fallback para download_url convencional:', e);
      }
    }

    if (downloadUrl) {
      const autoLink = document.createElement('a');
      autoLink.href = downloadUrl;
      autoLink.download = data.output_filename || 'Planilha_Automatizada.xlsx';
      document.body.appendChild(autoLink);
      autoLink.click();
      setTimeout(() => {
        document.body.removeChild(autoLink);
      }, 1500);
    }
  }

  function onJobCompleted(data) {
    progressBarFill.style.width = '100%';
    progressPercentBadge.textContent = '100%';
    progressStepTitle.textContent = 'Processamento Concluído com Sucesso!';
    progressSubtitle.textContent = 'Download da planilha iniciado automaticamente!';

    if (topProgressBar) topProgressBar.style.width = '100%';
    setTimeout(() => {
      if (topProgressContainer) topProgressContainer.style.display = 'none';
    }, 3000);

    if (headerStatusPill) {
      headerStatusPill.style.display = 'none';
    }
    document.title = '✓ Concluído! | Spotify & INPI Prospector';

    const pulseDot = document.querySelector('.status-indicator');
    if (pulseDot) {
      pulseDot.classList.remove('live-pulse');
      pulseDot.style.background = 'var(--spotify-green)';
    }

    btnStartPipeline.disabled = false;
    btnStartPipeline.innerHTML = '<span class="btn-icon">🚀</span> Iniciar Nova Automação';

    // Show Results
    resultsSection.style.display = 'block';
    resultsFilenameText.textContent = `Arquivo pronto: ${data.output_filename} (Download iniciado automaticamente)`;
    if (data.download_url) {
      btnDownloadFile.href = data.download_url;
      btnDownloadFile.setAttribute('download', data.output_filename);
    }

    if (data.summary) {
      updateStats(data.summary);
    }

    // DISPARA O DOWNLOAD AUTOMÁTICO IMEDIATO
    triggerAutoDownload(data);

    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // 7. Streaming HTTP com ReadableStream (evita congelamento em Serverless)
  async function runStreamingPipeline(formData) {
    const response = await fetch('/api/jobs/run-stream', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      let msg = 'Erro ao iniciar fluxo em tempo real.';
      try {
        const errJson = await response.json();
        msg = errJson.detail || msg;
      } catch (_) {}
      throw new Error(msg);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    let completedReceived = false;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split('\n\n');
      buffer = chunks.pop(); // Mantém o pedaço restante

      for (const chunk of chunks) {
        const trimmed = chunk.trim();
        if (!trimmed || trimmed.startsWith(':')) continue; // Keep-alive

        const lines = trimmed.split('\n');
        let eventType = 'message';
        let dataStr = '';

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            dataStr = line.slice(6).trim();
          }
        }

        if (dataStr) {
          try {
            const data = JSON.parse(dataStr);
            if (eventType === 'init') {
              currentJobId = data.job_id;
              if (data.progress) updateProgress(data.progress);
            } else if (eventType === 'progress') {
              updateProgress(data);
            } else if (eventType === 'log') {
              appendLog(data.line);
            } else if (eventType === 'artist_done') {
              if (data.progress) updateProgress(data.progress);
              if (data.current_artist) updateSpotlight(data.current_artist);
              if (data.summary) updateStats(data.summary);

              allArtists.push(data.artist);
              updateFilterCounts();
              renderTable();
            } else if (eventType === 'completed') {
              completedReceived = true;
              onJobCompleted(data);
            } else if (eventType === 'error') {
              showAppError(data.message || 'Erro durante a execução.');
              return;
            }
          } catch (pe) {
            console.warn('Erro ao processar evento de stream:', pe);
          }
        }
      }
    }

    if (!completedReceived && currentJobId) {
      console.warn('Stream terminou antes do evento completed. Checando status via API...');
      await checkJobCompletion(currentJobId);
    }
  }

  // Polling de fallback caso a conexão caia
  async function checkJobCompletion(jobId) {
    for (let attempt = 0; attempt < 10; attempt++) {
      try {
        await new Promise(r => setTimeout(r, 2000));
        const res = await fetch(`/api/jobs/${jobId}`);
        if (res.ok) {
          const data = await res.json();
          if (data.status === 'completed') {
            onJobCompleted(data);
            return;
          } else if (data.status === 'error') {
            showAppError(data.error || 'Falha no processamento.');
            return;
          }
        }
      } catch (_) {}
    }
    showAppError('A conexão com o servidor foi interrompida antes da conclusão da automação. Verifique os logs abaixo ou tente novamente.');
  }

  // 8. EventSource (SSE) Listener Fallback
  function listenToJobEvents(jobId) {
    if (activeEventSource) {
      activeEventSource.close();
    }

    activeEventSource = new EventSource(`/api/jobs/${jobId}/stream`);

    activeEventSource.addEventListener('init', (e) => {
      const data = JSON.parse(e.data);
      if (data.progress) updateProgress(data.progress);
      if (data.logs && data.logs.length > 0) {
        data.logs.forEach(l => appendLog(l));
      }
    });

    activeEventSource.addEventListener('progress', (e) => {
      const progress = JSON.parse(e.data);
      updateProgress(progress);
    });

    activeEventSource.addEventListener('log', (e) => {
      const data = JSON.parse(e.data);
      appendLog(data.line);
    });

    activeEventSource.addEventListener('artist_done', (e) => {
      const payload = JSON.parse(e.data);
      if (payload.progress) updateProgress(payload.progress);
      if (payload.current_artist) updateSpotlight(payload.current_artist);
      if (payload.summary) updateStats(payload.summary);

      allArtists.push(payload.artist);
      updateFilterCounts();
      renderTable();
    });

    activeEventSource.addEventListener('completed', (e) => {
      const data = JSON.parse(e.data);
      activeEventSource.close();
      onJobCompleted(data);
    });

    activeEventSource.addEventListener('error', (e) => {
      let msg = 'Erro no servidor durante a execução.';
      try {
        const d = JSON.parse(e.data);
        if (d && d.message) msg = d.message;
      } catch (_) {}
      activeEventSource.close();
      showAppError(msg);
    });

    activeEventSource.onerror = async () => {
      console.warn('Conexão SSE oscilou. Verificando status do processamento via API...');
      activeEventSource.close();
      await checkJobCompletion(jobId);
    };
  }

  function updateProgress(progress) {
    if (!progress) return;
    const pct = progress.percent || 0;
    progressBarFill.style.width = `${pct}%`;
    progressPercentBadge.textContent = `${pct}%`;

    if (topProgressBar) {
      topProgressBar.style.width = `${pct}%`;
    }

    if (progress.step_name) {
      progressStepTitle.textContent = `Etapa ${progress.step || ''}: ${progress.step_name}`;
      if (headerStatusText) {
        headerStatusText.textContent = `[${pct}%] ${progress.step_name}`;
      }
      document.title = `▶ [${pct}%] ${progress.step_name} | Spotify Prospector`;
    }
  }

  function updateSpotlight(cur) {
    if (!cur) return;
    spotlightName.textContent = cur.name || 'Artista';
    spotlightListeners.textContent = cur.listeners || 'N/D';
    spotlightIG.textContent = cur.ig || 'N/D';
    spotlightYT.textContent = cur.yt || 'N/D';
    spotlightTikTok.textContent = cur.tiktok || 'N/D';

    if (cur.marca === 'Com Marca') {
      spotlightMarcaTag.textContent = '🛡 Com Marca Registrada';
      spotlightMarcaTag.style.background = 'rgba(56, 189, 248, 0.15)';
      spotlightMarcaTag.style.color = 'var(--accent-blue)';
    } else {
      spotlightMarcaTag.textContent = '🎯 SEM MARCA (Lead)';
      spotlightMarcaTag.style.background = 'var(--amber-lead-dim)';
      spotlightMarcaTag.style.color = 'var(--amber-lead)';
    }

    if (cur.name) {
      document.title = `▶ [${progressPercentBadge.textContent}] ${cur.name} | Spotify Prospector`;
      if (headerStatusText) {
        headerStatusText.textContent = `Analisando: ${cur.name}`;
      }
    }
  }

  function updateStats(summary) {
    if (!summary) return;
    if (statTracks) statTracks.textContent = summary.total_tracks || allArtists.length;
    if (statArtists) statArtists.textContent = summary.total_artists || allArtists.length;
    if (statSemMarca) statSemMarca.textContent = summary.sem_marca || 0;
    if (statComMarca) statComMarca.textContent = summary.com_marca || 0;
  }

  function updateFilterCounts() {
    const sem = allArtists.filter(a => !a.tem_marca).length;
    const com = allArtists.length - sem;
    countFilterAll.textContent = allArtists.length;
    countFilterLeads.textContent = sem;
    countFilterMarcas.textContent = com;
  }

  function scrollConsoleToBottom() {
    consoleBody.scrollTop = consoleBody.scrollHeight;
  }

  // 8. Table Rendering & Filters
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.getAttribute('data-filter');
      renderTable();
    });
  });

  if (tableSearchInput) {
    tableSearchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value.toLowerCase().trim();
      renderTable();
    });
  }

  function renderTable() {
    let filtered = allArtists;

    if (currentFilter === 'sem_marca') {
      filtered = filtered.filter(a => !a.tem_marca);
    } else if (currentFilter === 'com_marca') {
      filtered = filtered.filter(a => a.tem_marca);
    }

    if (searchQuery) {
      filtered = filtered.filter(a => a.name.toLowerCase().includes(searchQuery));
    }

    if (filtered.length === 0) {
      artistsTableBody.innerHTML = `
        <tr>
          <td colspan="8" style="text-align: center; color: var(--text-muted); padding: 30px;">
            ${allArtists.length === 0 ? 'Nenhum artista processado ainda...' : 'Nenhum artista corresponde aos filtros selecionados.'}
          </td>
        </tr>
      `;
      return;
    }

    artistsTableBody.innerHTML = filtered.map((a, idx) => {
      const spotifyLink = a.spotify_url ? 
        `<a href="${a.spotify_url}" target="_blank" class="table-link">${a.monthly_listeners_fmt}</a>` : 
        (a.monthly_listeners_fmt || 'N/D');

      const igLink = a.ig_url ? 
        `<a href="${a.ig_url}" target="_blank" class="table-link">${a.ig_display}</a>` : 
        (a.ig_display || 'N/D');

      const ytLink = a.youtube_url ? 
        `<a href="${a.youtube_url}" target="_blank" class="table-link">${a.youtube_display}</a>` : 
        (a.youtube_display || 'N/D');

      const ttLink = a.tiktok_url ? 
        `<a href="${a.tiktok_url}" target="_blank" class="table-link">${a.tiktok_display}</a>` : 
        (a.tiktok_display || 'N/D');

      const statusBadge = a.tem_marca ? 
        `<span class="tag-com-marca">🛡 Com Marca (${(a.inpi_records || []).length})</span>` : 
        `<a href="${a.inpi_search_url}" target="_blank" class="tag-sem-marca" title="Clique para pesquisar no INPI">🎯 Sem Marca 🔍</a>`;

      return `
        <tr>
          <td>${idx + 1}</td>
          <td><strong>${escapeHtml(a.name)}</strong></td>
          <td>${a.count_display || '1'}</td>
          <td>${spotifyLink}</td>
          <td>${igLink}</td>
          <td>${ytLink}</td>
          <td>${ttLink}</td>
          <td class="col-status-inpi">${statusBadge}</td>
        </tr>
      `;
    }).join('');
  }

  function escapeHtml(text) {
    if (!text) return '';
    return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // 9. History Modal
  btnOpenHistory.addEventListener('click', async () => {
    historyModal.classList.add('open');
    historyList.innerHTML = '<p class="empty-state">Buscando planilhas na pasta output/...</p>';
    try {
      const res = await fetch('/api/history');
      const data = await res.json();
      if (!data.files || data.files.length === 0) {
        historyList.innerHTML = '<p class="empty-state">Nenhuma planilha gerada ainda.</p>';
        return;
      }
      historyList.innerHTML = data.files.map(file => `
        <div class="history-item">
          <div>
            <div class="history-title">${escapeHtml(file.filename)}</div>
            <div class="history-sub">${file.size_kb} KB • Gerada em ${file.modified_at}</div>
          </div>
          <a href="${file.download_url}" class="history-btn" download>📥 Baixar</a>
        </div>
      `).join('');
    } catch {
      historyList.innerHTML = '<p class="empty-state">Erro ao carregar histórico.</p>';
    }
  });

  btnCloseHistory.addEventListener('click', () => {
    historyModal.classList.remove('open');
  });

  // 10. Config Modal
  btnOpenConfig.addEventListener('click', async () => {
    configModal.classList.add('open');
    configStatusMessage.textContent = '';
    try {
      const res = await fetch('/api/config/spotify');
      const data = await res.json();
      if (data.configured) {
        configStatusMessage.textContent = `Credenciais configuradas (${data.client_id_preview})`;
        configStatusMessage.className = 'status-msg success';
      }
    } catch {
      // Ignora erro
    }
  });

  [btnCloseConfig, btnCancelConfig].forEach(btn => {
    btn.addEventListener('click', () => {
      configModal.classList.remove('open');
    });
  });

  btnSaveConfig.addEventListener('click', async () => {
    const cid = cfgClientId.value.trim();
    const csec = cfgClientSecret.value.trim();
    if (!cid || !csec) {
      alert('Preencha tanto o Client ID quanto o Client Secret.');
      return;
    }

    const formData = new FormData();
    formData.append('client_id', cid);
    formData.append('client_secret', csec);

    try {
      const res = await fetch('/api/config/spotify', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        configStatusMessage.textContent = 'Credenciais salvas com sucesso!';
        configStatusMessage.className = 'status-msg success';
        setTimeout(() => {
          configModal.classList.remove('open');
        }, 1200);
      } else {
        throw new Error('Falha ao salvar');
      }
    } catch {
      alert('Erro ao salvar credenciais.');
    }
  });

  // Close modals on outside click
  window.addEventListener('click', (e) => {
    if (e.target === historyModal) historyModal.classList.remove('open');
    if (e.target === configModal) configModal.classList.remove('open');
  });
});
