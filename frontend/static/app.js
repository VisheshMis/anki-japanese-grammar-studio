// Anki Japanese Grammar Studio Frontend Logic

let appState = {
  currentTab: 'deck',
  deckLoaded: false,
  deckName: '',
  cards: [],
  currentCardIndex: 0,
  fieldMappings: {},
  analyzedCount: 0,
  ollama: { online: false, model_available: false, current_model: '' }
};

document.addEventListener('DOMContentLoaded', () => {
  initApp();
  setupEventListeners();
});

async function initApp() {
  await fetchStatus();
  setupHoverPopover();
}

// -------------------------------------------------------------
// Status & Polling
// -------------------------------------------------------------
async function fetchStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    appState.ollama = data.ollama;
    appState.deckLoaded = data.deck_loaded;
    appState.deckName = data.deck_name;
    appState.analyzedCount = data.analyzed_count;

    updateHeaderBadges();
    updateAnalyzeEngineBadge();

    if (appState.deckLoaded && appState.cards.length === 0) {
      await loadCards();
    }
  } catch (err) {
    console.error('Failed to fetch status:', err);
  }
}

function updateHeaderBadges() {
  const aiBadge = document.getElementById('ai-status-badge');
  const aiText = document.getElementById('ai-status-text');
  const deckBadge = document.getElementById('deck-status-badge');
  const deckText = document.getElementById('deck-status-text');

  if (appState.ollama && appState.ollama.online) {
    aiBadge.className = 'status-pill status-online';
    aiText.textContent = `Local AI (${appState.ollama.current_model || 'Ollama'})`;
  } else {
    aiBadge.className = 'status-pill status-offline';
    aiText.textContent = 'Grammar KB (Offline Active)';
  }

  if (appState.deckLoaded) {
    deckBadge.className = 'status-pill status-online';
    deckText.textContent = `${appState.deckName} (${appState.cards.length} cards)`;
  } else {
    deckBadge.className = 'status-pill status-neutral';
    deckText.textContent = 'No Deck Loaded';
  }
}

function updateAnalyzeEngineBadge() {
  const engineName = document.getElementById('engine-name');
  if (appState.ollama && appState.ollama.online && appState.ollama.model_available) {
    engineName.textContent = `Ollama LLM (${appState.ollama.current_model})`;
    engineName.style.color = '#10b981';
  } else {
    engineName.textContent = 'Built-in Grammar Engine (35+ JLPT Rules)';
    engineName.style.color = '#38bdf8';
  }

  document.getElementById('stat-total-cards').textContent = appState.cards.length;
  document.getElementById('stat-analyzed-cards').textContent = appState.analyzedCount;
}

// -------------------------------------------------------------
// Navigation Tabs
// -------------------------------------------------------------
function switchTab(tabId) {
  appState.currentTab = tabId;

  document.querySelectorAll('.nav-tab').forEach((tab, idx) => {
    tab.classList.toggle('active', tab.getAttribute('onclick').includes(tabId));
  });

  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.remove('active');
  });

  const activeContent = document.getElementById(`tab-${tabId}`);
  if (activeContent) activeContent.classList.add('active');

  if (tabId === 'study') {
    renderCurrentCard();
  }
}

// -------------------------------------------------------------
// Deck Upload & Sample Loading
// -------------------------------------------------------------
function setupEventListeners() {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    if (e.dataTransfer.files.length > 0) {
      uploadFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      uploadFile(e.target.files[0]);
    }
  });

  // Spacebar to flip card in study mode
  document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && appState.currentTab === 'study') {
      e.preventDefault();
      flipCard();
    }
  });
}

async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.error) {
      alert(`Error: ${data.error}`);
      return;
    }

    onDeckLoaded(data);
  } catch (err) {
    alert(`Upload failed: ${err}`);
  }
}

async function loadSampleDeck() {
  try {
    const res = await fetch('/api/sample-deck', { method: 'POST' });
    const data = await res.json();
    if (data.error) {
      alert(`Error: ${data.error}`);
      return;
    }

    onDeckLoaded(data);
  } catch (err) {
    alert(`Failed to load sample deck: ${err}`);
  }
}

function cleanText(text) {
  if (!text) return '';
  let s = String(text).replace(/\[sound:[^\]]+\]/g, '');
  s = s.replace(/<br\s*\/?>/gi, ' ');
  s = s.replace(/<[^>]+>/g, '');
  return s.trim();
}

function onDeckLoaded(data) {
  appState.deckLoaded = true;
  appState.deckName = data.deck_name;
  appState.cards = data.preview_cards || [];
  appState.fieldMappings = data.field_mappings || {};

  // Populate field dropdowns
  populateFieldDropdown('select-sentence-field', data.available_fields, appState.fieldMappings.sentence_field);
  populateFieldDropdown('select-vocab-field', data.available_fields, appState.fieldMappings.vocab_field);
  populateFieldDropdown('select-meaning-field', data.available_fields, appState.fieldMappings.meaning_field);

  document.getElementById('btn-save-fields').disabled = false;

  // Render Card #1 Field Inspector
  if (data.preview_cards && data.preview_cards.length > 0) {
    renderCardInspector(data.preview_cards[0]);
  }

  // Show preview
  renderPreviewTable(data.preview_cards);
  updateHeaderBadges();
  updateAnalyzeEngineBadge();
}

function populateFieldDropdown(elementId, fields, selectedValue) {
  const select = document.getElementById(elementId);
  select.innerHTML = '';

  const defaultOpt = document.createElement('option');
  defaultOpt.value = '';
  defaultOpt.textContent = '-- None / Select Field --';
  select.appendChild(defaultOpt);

  fields.forEach(f => {
    const opt = document.createElement('option');
    opt.value = f;
    opt.textContent = f;
    if (f === selectedValue) opt.selected = true;
    select.appendChild(opt);
  });
}

function updateTableHeaderBadges() {
  const sField = appState.fieldMappings.sentence_field || '';
  const vField = appState.fieldMappings.vocab_field || '';
  const mField = appState.fieldMappings.meaning_field || '';

  const hSentence = document.getElementById('header-sentence-field');
  const hVocab = document.getElementById('header-vocab-field');
  const hMeaning = document.getElementById('header-meaning-field');

  if (hSentence) hSentence.textContent = sField ? `[${sField}]` : '[Not selected]';
  if (hVocab) hVocab.textContent = vField ? `[${vField}]` : '[None]';
  if (hMeaning) hMeaning.textContent = mField ? `[${mField}]` : '[None]';
}

function renderCardInspector(card) {
  const inspector = document.getElementById('card-fields-inspector');
  const list = document.getElementById('inspector-fields-list');
  if (!card || !card.fields) {
    if (inspector) inspector.style.display = 'none';
    return;
  }

  list.innerHTML = '';
  Object.entries(card.fields).forEach(([fname, rawval]) => {
    const cleanval = cleanText(rawval);
    const row = document.createElement('div');
    row.className = 'inspector-field-row';
    row.innerHTML = `
      <span class="inspector-name">${fname}</span>
      <span class="inspector-val" title="${cleanval || '(empty)'}">${cleanval || '<em style="color:#64748b">(empty)</em>'}</span>
      <div class="inspector-actions">
        <button type="button" class="btn-tag" onclick="assignField('${fname}', 'sentence')">Sentence</button>
        <button type="button" class="btn-tag" onclick="assignField('${fname}', 'vocab')">Vocab</button>
        <button type="button" class="btn-tag" onclick="assignField('${fname}', 'meaning')">Meaning</button>
      </div>
    `;
    list.appendChild(row);
  });
  inspector.style.display = 'block';
}

function assignField(fieldName, targetSlot) {
  if (targetSlot === 'sentence') {
    document.getElementById('select-sentence-field').value = fieldName;
  } else if (targetSlot === 'vocab') {
    document.getElementById('select-vocab-field').value = fieldName;
  } else if (targetSlot === 'meaning') {
    document.getElementById('select-meaning-field').value = fieldName;
  }
  onFieldDropdownChanged();
}

function onFieldDropdownChanged() {
  const sField = document.getElementById('select-sentence-field').value;
  const vField = document.getElementById('select-vocab-field').value;
  const mField = document.getElementById('select-meaning-field').value;

  appState.fieldMappings = {
    sentence_field: sField,
    vocab_field: vField,
    meaning_field: mField
  };

  // Immediately update cards in memory for instant feedback
  if (appState.cards && appState.cards.length > 0) {
    appState.cards.forEach(card => {
      const f = card.fields || {};
      card.original_sentence = cleanText(f[sField] || '');
      card.target_word = vField ? cleanText(f[vField] || '') : '';
      card.meaning = mField ? cleanText(f[mField] || '') : '';
      card.annotated_html = ''; // Reset any stale annotations
      card.grammar_points = [];
    });
    appState.analyzedCount = 0;
    renderPreviewTable(appState.cards);
    updateAnalyzeEngineBadge();
  }

  // Flash live toast
  const toast = document.getElementById('field-saved-toast');
  if (toast) {
    toast.style.display = 'inline-block';
    toast.textContent = '✓ Updated live';
    setTimeout(() => { toast.style.display = 'none'; }, 2000);
  }

  // Sync to backend asynchronously
  syncFieldMappingsToBackend();
}

async function syncFieldMappingsToBackend() {
  const sField = appState.fieldMappings.sentence_field;
  const vField = appState.fieldMappings.vocab_field;
  const mField = appState.fieldMappings.meaning_field;

  if (!sField) return;

  try {
    const res = await fetch('/api/configure-fields', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sentence_field: sField,
        vocab_field: vField,
        meaning_field: mField
      })
    });
    const data = await res.json();
    if (data.success && data.preview_cards) {
      appState.cards = data.preview_cards;
    }
  } catch (err) {
    console.error('Failed to sync field mappings:', err);
  }
}

async function proceedToAnalysis() {
  await syncFieldMappingsToBackend();
  switchTab('analyze');
}

function renderPreviewTable(cards) {
  const previewSection = document.getElementById('deck-preview-section');
  const tbody = document.getElementById('preview-table-body');
  document.getElementById('preview-count').textContent = appState.cards.length || cards.length;
  document.getElementById('preview-deck-name').textContent = appState.deckName;

  updateTableHeaderBadges();

  const sField = appState.fieldMappings.sentence_field;
  const vField = appState.fieldMappings.vocab_field;
  const mField = appState.fieldMappings.meaning_field;

  tbody.innerHTML = '';
  cards.forEach((card, idx) => {
    const fields = card.fields || {};
    const sentenceVal = sField ? cleanText(fields[sField]) : (card.original_sentence || '-');
    const vocabVal = vField ? cleanText(fields[vField]) : (card.target_word || '-');
    const meaningVal = mField ? cleanText(fields[mField]) : (card.meaning || '-');

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${idx + 1}</td>
      <td style="font-weight: 700; color: #38bdf8;">${vocabVal || '<span style="color:#64748b">-</span>'}</td>
      <td style="font-family: var(--font-japanese); font-size: 1.05rem;">${sentenceVal || '<span style="color:#64748b">-</span>'}</td>
      <td style="color: var(--text-muted);">${meaningVal || '<span style="color:#64748b">-</span>'}</td>
    `;
    tbody.appendChild(tr);
  });

  previewSection.style.display = 'block';
}

async function saveFieldMappings(e) {
  if (e) e.preventDefault();
  await proceedToAnalysis();
}

async function loadCards() {
  try {
    const res = await fetch('/api/cards');
    const data = await res.json();
    appState.cards = data.cards;
    appState.analyzedCount = data.analyzed_count;
    updateHeaderBadges();
    updateAnalyzeEngineBadge();
    if (data.cards.length > 0) {
      renderPreviewTable(data.cards.slice(0, 5));
    }
  } catch (err) {
    console.error('Failed to load cards:', err);
  }
}

// -------------------------------------------------------------
// Batch AI Grammar Analysis
// -------------------------------------------------------------
async function runBatchAnalysis() {
  const btn = document.getElementById('btn-run-analysis');
  const progContainer = document.getElementById('analysis-progress-container');
  const progBar = document.getElementById('analysis-progress-bar');
  const statusMsg = document.getElementById('analysis-status-msg');
  const forceOffline = document.getElementById('chk-force-offline').checked;

  btn.disabled = true;
  progContainer.style.display = 'block';
  progBar.style.width = '30%';
  statusMsg.textContent = 'Sending sentences to grammar analysis engine...';

  try {
    const res = await fetch('/api/analyze-batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ force_offline: forceOffline })
    });
    const data = await res.json();

    progBar.style.width = '100%';
    if (data.success) {
      statusMsg.textContent = `Analysis complete! Processed ${data.processed_count} cards with ${data.provider}.`;
      appState.cards = data.cards;
      appState.analyzedCount = data.total_analyzed;
      updateHeaderBadges();
      updateAnalyzeEngineBadge();

      setTimeout(() => {
        switchTab('study');
      }, 800);
    } else {
      statusMsg.textContent = `Analysis failed: ${data.error}`;
    }
  } catch (err) {
    statusMsg.textContent = `Error during analysis: ${err}`;
  } finally {
    btn.disabled = false;
  }
}

// -------------------------------------------------------------
// Flashcard Study & Review
// -------------------------------------------------------------
function renderCurrentCard() {
  if (appState.cards.length === 0) {
    document.getElementById('card-vocab').textContent = 'No Cards Loaded';
    document.getElementById('card-sentence-front').textContent = 'Please upload a deck or load sample cards in Tab 1.';
    return;
  }

  const idx = appState.currentCardIndex;
  const card = appState.cards[idx];

  document.getElementById('current-card-idx').textContent = idx + 1;
  document.getElementById('total-study-cards').textContent = appState.cards.length;

  // Reset flip
  const cardElem = document.getElementById('active-flashcard');
  cardElem.classList.remove('flipped');
  document.getElementById('grade-buttons').style.display = 'none';

  // Front content
  document.getElementById('card-vocab').textContent = card.target_word || '';
  
  // Render highlighted sentence if available, or plain sentence
  const frontSentenceContainer = document.getElementById('card-sentence-front');
  if (card.annotated_html) {
    frontSentenceContainer.innerHTML = card.annotated_html;
  } else {
    frontSentenceContainer.textContent = card.original_sentence || '(No sentence found for this field)';
  }

  // Back content
  document.getElementById('card-meaning').textContent = card.target_word || 'Vocabulary';
  document.getElementById('card-sentence-english').textContent = card.meaning || '(No meaning field selected)';

  // Grammar breakdown list on back
  const breakdownList = document.getElementById('grammar-breakdown-list');
  breakdownList.innerHTML = '';

  const grammarPoints = card.grammar_points || [];
  if (grammarPoints.length > 0) {
    grammarPoints.forEach(pt => {
      const item = document.createElement('div');
      item.className = 'grammar-card-item';
      item.innerHTML = `
        <div class="item-header">
          <span class="item-title">${pt.pattern || pt.matched_text}</span>
          <span class="legend-chip jlpt-${(pt.jlpt || 'n3').toLowerCase()}">${pt.jlpt || 'N3'}</span>
        </div>
        <div style="font-size: 0.9rem; color: #f1f5f9;"><strong>${pt.meaning}</strong></div>
        <div class="item-rule"><code>${pt.formation || ''}</code></div>
        <div style="font-size: 0.8rem; color: #cbd5e1; margin-top: 0.25rem;">${pt.explanation || ''}</div>
      `;
      breakdownList.appendChild(item);
    });
  } else {
    breakdownList.innerHTML = '<div style="color: var(--text-muted); font-size: 0.85rem;">No grammar points identified yet. Run Tab 2 to analyze.</div>';
  }
}

function flipCard() {
  const cardElem = document.getElementById('active-flashcard');
  cardElem.classList.toggle('flipped');

  const gradeButtons = document.getElementById('grade-buttons');
  gradeButtons.style.display = cardElem.classList.contains('flipped') ? 'flex' : 'none';
}

function prevCard() {
  if (appState.currentCardIndex > 0) {
    appState.currentCardIndex--;
    renderCurrentCard();
  }
}

function nextCard() {
  if (appState.currentCardIndex < appState.cards.length - 1) {
    appState.currentCardIndex++;
    renderCurrentCard();
  }
}

async function gradeCard(grade) {
  const card = appState.cards[appState.currentCardIndex];
  if (!card) return;

  try {
    await fetch('/api/review-card', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ card_id: card.id, grade: grade })
    });
  } catch (e) {
    console.error('Failed to grade card:', e);
  }

  nextCard();
}

// -------------------------------------------------------------
// Interactive Grammar Popover Tooltip
// -------------------------------------------------------------
function setupHoverPopover() {
  const popover = document.getElementById('grammar-popover');

  document.addEventListener('mouseover', (e) => {
    const target = e.target.closest('.grammar-point');
    if (!target) return;

    const pattern = target.getAttribute('data-pattern') || target.textContent;
    const jlpt = target.getAttribute('data-jlpt') || 'N3';
    const meaning = target.getAttribute('data-meaning') || '';
    const formation = target.getAttribute('data-formation') || '';
    const explanation = target.getAttribute('data-explanation') || '';

    document.getElementById('popover-pattern').textContent = pattern;
    const jlptChip = document.getElementById('popover-jlpt');
    jlptChip.textContent = jlpt;
    jlptChip.className = `legend-chip jlpt-${jlpt.toLowerCase()}`;

    document.getElementById('popover-meaning').textContent = meaning;
    document.getElementById('popover-formation').textContent = formation;
    document.getElementById('popover-explanation').textContent = explanation;

    popover.style.display = 'block';
    positionPopover(e, popover);
  });

  document.addEventListener('mousemove', (e) => {
    const target = e.target.closest('.grammar-point');
    if (target && popover.style.display === 'block') {
      positionPopover(e, popover);
    }
  });

  document.addEventListener('mouseout', (e) => {
    const target = e.target.closest('.grammar-point');
    if (target) {
      popover.style.display = 'none';
    }
  });
}

function positionPopover(e, popover) {
  const offsetX = 15;
  const offsetY = 20;

  let x = e.pageX + offsetX;
  let y = e.pageY + offsetY;

  const popoverWidth = 320;
  if (x + popoverWidth > window.innerWidth - 20) {
    x = e.pageX - popoverWidth - offsetX;
  }

  popover.style.left = `${x}px`;
  popover.style.top = `${y}px`;
}

// -------------------------------------------------------------
// Direct Drive Sync
// -------------------------------------------------------------
async function checkDrivePath() {
  const path = document.getElementById('drive-path-input').value.trim();
  const statusBox = document.getElementById('drive-status-box');
  const details = document.getElementById('drive-status-details');

  try {
    const res = await fetch('/api/sync/status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ drive_path: path })
    });
    const data = await res.json();

    if (data.exists && data.writable) {
      statusBox.className = 'info-box info-success';
      details.innerHTML = `
        <strong>Directory Ready:</strong> <code>${data.directory}</code><br>
        Has existing sync database: <strong>${data.has_sync_db ? 'Yes (' + data.card_count + ' cards)' : 'No (Will create new)'}</strong>
        ${data.last_synced_at ? '<br>Last Synced: ' + new Date(data.last_synced_at).toLocaleString() : ''}
      `;
    } else {
      statusBox.className = 'info-box info-neutral';
      details.innerHTML = `Directory not yet created: <code>${data.directory}</code>. It will be created automatically on first sync.`;
    }
  } catch (err) {
    alert(`Could not verify path: ${err}`);
  }
}

async function triggerExportSync() {
  const path = document.getElementById('drive-path-input').value.trim();
  if (!path) {
    alert('Please enter a target drive folder.');
    return;
  }

  try {
    const res = await fetch('/api/sync/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ drive_path: path })
    });
    const data = await res.json();
    if (data.success) {
      alert(`Sync Export Successful!\nSynced ${data.cards_synced} cards to:\n${data.sync_file}`);
      checkDrivePath();
    } else {
      alert(`Sync failed: ${data.error}`);
    }
  } catch (err) {
    alert(`Sync export error: ${err}`);
  }
}

async function triggerImportSync() {
  const path = document.getElementById('drive-path-input').value.trim();
  if (!path) {
    alert('Please enter a target drive folder.');
    return;
  }

  try {
    const res = await fetch('/api/sync/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ drive_path: path })
    });
    const data = await res.json();
    if (data.success) {
      alert(`Sync Import Successful!\nImported ${data.total_notes} cards from ${data.deck_name}`);
      await loadCards();
      switchTab('study');
    } else {
      alert(`Sync import failed: ${data.error}`);
    }
  } catch (err) {
    alert(`Sync import error: ${err}`);
  }
}
