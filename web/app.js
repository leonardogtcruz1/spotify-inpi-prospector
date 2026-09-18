// Spotify & INPI Lead Prospector - Frontend Controller
document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');
  const playlistUrlInput = document.getElementById('playlistUrlInput');
  const btnClearUrl = document.getElementById('btnClearUrl');
  const pillBtns = document.querySelectorAll('.pill-btn');
  
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
  
  // Console Elements
  const btnToggleConsole = document.getElementById('btnToggleConsole');
  const consoleBody = document.getElementById('consoleBody');
  const consoleArrow = document.getElementById('consoleArrow');
  const consoleOutput = document.getElementById('consoleOutput');
  
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

  // 2. Clear URL input
  if (btnClearUrl) {
    btnClearUrl.addEventListener('click', () => {
      playlistUrlInput.value = '';
      playlistUrlInput.focus();
    });
  }

  // 3. Example Pills
  pillBtns.forEach(pill => {
    pill.addEventListener('click', () => {
      playlistUrlInput.value = pill.getAttribute('data-url');
    });
  });

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

  // 5. Console Toggle
  let consoleOpen = true;
  if (btnToggleConsole) {
    btnToggleConsole.addEventListener('click', () => {
      consoleOpen = !consoleOpen;
      consoleBody.style.display = consoleOpen ? 'block' : 'none';
      consoleArrow.textContent = consoleOpen ? '▼' : '►';
    });
  }

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
    btnStartPipeline.innerHTML = '<span class="btn-icon">⏳</span> Iniciando Robô...';
    
    allArtists = [];
    renderTable();
    consoleOutput.textContent = 'Iniciando conexão...\n';
    
    progressSection.style.display = 'block';
    resultsSection.style.display = 'none';
    progressPercentBadge.textContent = '0%';
    progressBarFill.style.width = '0%';
    progressStepTitle.textContent = 'Conectando ao serviço...';
    progressSubtitle.textContent = 'Aguarde o carregamento inicial da playlist...';

    // Ativa linha de progresso no topo e badge de status
    if (topProgressContainer) topProgressContainer.style.display = 'block';
    if (topProgressBar) topProgressBar.style.width = '5%';
    if (headerStatusPill) {
      headerStatusPill.style.display = 'flex';
      if (headerStatusText) headerStatusText.textContent = 'Iniciando robô...';
    }
    document.title = '▶ [Iniciando...] Spotify Prospector';
    
    // Smooth scroll to progress section
    progressSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    try {
      const response = await fetch('/api/jobs', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Erro ao iniciar o processamento.');
      }

      const resData = await response.json();
      currentJobId = resData.job_id;
      listenToJobEvents(currentJobId);

    } catch (err) {
      alert(`Erro: ${err.message}`);
      if (topProgressContainer) topProgressContainer.style.display = 'none';
      if (headerStatusPill) headerStatusPill.style.display = 'none';
      document.title = 'Spotify & INPI Lead Prospector';
      btnStartPipeline.disabled = false;
      btnStartPipeline.innerHTML = '<span class="btn-icon">🚀</span> Iniciar Automação Completa';
    }
  });

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

  // 7. EventSource (SSE) Listener
  function listenToJobEvents(jobId) {
    if (activeEventSource) {
      activeEventSource.close();
    }

    activeEventSource = new EventSource(`/api/jobs/${jobId}/stream`);

    activeEventSource.addEventListener('init', (e) => {
      const data = JSON.parse(e.data);
      if (data.progress) updateProgress(data.progress);
      if (data.logs && data.logs.length > 0) {
        consoleOutput.textContent = data.logs.join('\n') + '\n';
        scrollConsoleToBottom();
      }
    });

    activeEventSource.addEventListener('progress', (e) => {
      const progress = JSON.parse(e.data);
      updateProgress(progress);
    });

    activeEventSource.addEventListener('log', (e) => {
      const data = JSON.parse(e.data);
      consoleOutput.textContent += data.line + '\n';
      scrollConsoleToBottom();
    });

    activeEventSource.addEventListener('artist_done', (e) => {
      const payload = JSON.parse(e.data);
      const artist = payload.artist;
      const progress = payload.progress;
      const summary = payload.summary;
      const current = payload.current_artist;

      if (progress) updateProgress(progress);
      if (current) updateSpotlight(current);
      if (summary) updateStats(summary);

      allArtists.push(artist);
      updateFilterCounts();
      renderTable();
    });

    activeEventSource.addEventListener('completed', (e) => {
      const data = JSON.parse(e.data);
      activeEventSource.close();

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
      btnDownloadFile.href = data.download_url;
      btnDownloadFile.setAttribute('download', data.output_filename);

      if (data.summary) {
        updateStats(data.summary);
      }

      // DISPARA O DOWNLOAD AUTOMÁTICO IMEDIATO
      triggerAutoDownload(data);

      resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    activeEventSource.addEventListener('error', (e) => {
      try {
        const data = JSON.parse(e.data);
        alert(`Erro durante a execução: ${data.message}`);
      } catch {
        console.warn('Conexão SSE encerrada.');
      }
      activeEventSource.close();
      if (topProgressContainer) topProgressContainer.style.display = 'none';
      if (headerStatusPill) headerStatusPill.style.display = 'none';
      document.title = 'Spotify & INPI Lead Prospector';
      btnStartPipeline.disabled = false;
      btnStartPipeline.innerHTML = '<span class="btn-icon">🚀</span> Iniciar Automação Completa';
    });
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
          <td>${statusBadge}</td>
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
