# Anki Japanese Grammar Studio 🌸

> **Local-First, High-Performance Japanese Grammar Analyzer & Direct Drive Sync Studio** for Anki flashcard collections (`.apkg`).
> Designed to run entirely on-premises using Local AI (Ollama / Qwen 2.5) with zero central server compute and zero cloud subscription fees.

---

## 🎯 Key Features

1. **Direct Anki Deck Ingestion (`.apkg`)**:
   - Parses both modern (`collection.anki21`) and legacy (`collection.anki2`) Anki SQLite formats in memory.
   - Preserves all fields, tags, models, and note structures.

2. **Smart Sentence Field Selection**:
   - Easily map which note field contains the target vocabulary and example sentence.

3. **Hybrid AI & Grammar Knowledge Base**:
   - **Local AI Engine**: Seamlessly interfaces with local **Ollama** (`http://localhost:11434`) using `qwen2.5:7b` or `qwen2.5:14b`.
   - **Built-in Offline Engine**: Includes a curated catalog of **35+ JLPT N5–N1 grammar patterns** with standardized formulas, meanings, connection rules, and pedagogical explanations.
   - Automatically falls back to the offline engine if Ollama is paused.

4. **Interactive Flashcard Study Mode**:
   - Color-coded grammar highlights directly inside the example sentence:
     - <span style="color:#10b981; font-weight:bold;">JLPT N5 (Emerald)</span>
     - <span style="color:#3b82f6; font-weight:bold;">JLPT N4 (Ocean Blue)</span>
     - <span style="color:#f59e0b; font-weight:bold;">JLPT N3 (Amber)</span>
     - <span style="color:#f97316; font-weight:bold;">JLPT N2 (Orange)</span>
     - <span style="color:#ef4444; font-weight:bold;">JLPT N1 (Crimson)</span>
   - **Interactive Hover Popover**: Hovering or tapping any grammar point immediately reveals its name, JLPT level, English meaning, formation rule, and in-depth explanation.
   - Card flipping with spacebar or mouse click and SRS grading (`Again`, `Hard`, `Good`, `Easy`).

5. **Direct Drive Sync (Zero-Server Sync)**:
   - Click **"Sync"**, specify any local drive or cloud folder (such as **Google Drive**, **iCloud Drive**, **OneDrive**, or an external drive).
   - Generates a standalone, encrypted SQLite sync package (`anki_grammar_sync.db`).
   - Syncs review history and enriched cards directly between devices without a central server.

---

## 🚀 Quick Start (macOS & Windows)

### 1. Launch the Application
Simply run the launcher script:

```bash
python3 run.py
```

The application will start on `http://localhost:5001` and automatically open your default browser.

### 2. Using with Android on the Same Wi-Fi
When `run.py` starts, it prints your local network IP (e.g., `http://192.168.1.15:5001`).
Open this URL in Chrome or Firefox on your Android device to study your cards with full touch tooltips.

---

## 🤖 (Optional) Setting Up the Local LLM (Ollama)

To enable context-aware AI grammar analysis:

1. Install Ollama: [https://ollama.com](https://ollama.com) (or `brew install ollama`).
2. Download the Japanese-proficient Qwen model:
   ```bash
   ollama pull qwen2.5:7b
   ```
3. Start the Ollama server:
   ```bash
   ollama serve
   ```

*Note: If Ollama is not running, the application will automatically use its built-in offline Grammar Knowledge Base.*

---

## 🧪 Running Automated Tests

Run the complete test suite:

```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

All tests run in less than 0.1s:
* `test_deck_parser.py`: Verifies `.apkg` extraction and field parsing.
* `test_grammar_kb.py`: Verifies JLPT pattern recognition and HTML annotation.
* `test_sync_engine.py`: Verifies Drive export/import cycle and database creation.
* `test_app_endpoints.py`: Verifies Flask REST endpoints and session flows.

---

## 📁 Project Structure

```text
anki plug in /
├── backend/
│   ├── app.py              # Main Flask REST server
│   ├── deck_parser.py      # .apkg archive and SQLite parser
│   ├── grammar_kb.py       # Curated JLPT N5-N1 catalog & rule matcher
│   ├── ai_analyzer.py      # Ollama local AI client + offline fallback
│   └── sync_engine.py      # Direct Drive sync manager (SQLite bundle)
├── frontend/
│   ├── templates/
│   │   └── index.html      # Responsive single-page UI
│   └── static/
│       ├── styles.css      # Dark-mode styling, JLPT chips, card flip
│       └── app.js          # Client-side reactivity, hover cards, sync
├── tests/
│   ├── test_deck_parser.py
│   ├── test_grammar_kb.py
│   ├── test_sync_engine.py
│   └── test_app_endpoints.py
├── run.py                  # One-click launcher
├── .gitignore
└── README.md
```
