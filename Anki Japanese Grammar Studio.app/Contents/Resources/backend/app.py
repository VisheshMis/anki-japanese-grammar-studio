import json
import logging
import os
import tempfile
import time
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, render_template, request, send_file

from .ai_analyzer import LocalAIAnalyzer
from .deck_parser import APKGParser, parse_apkg
from .grammar_kb import GRAMMAR_CATALOG, annotate_sentence, find_candidate_grammar
from .sync_engine import SyncEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
TEMPLATES_DIR = os.path.join(FRONTEND_DIR, "templates")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

app = Flask(
    __name__,
    template_folder=TEMPLATES_DIR,
    static_folder=STATIC_DIR,
    static_url_path="/static"
)

# Global in-memory session state
STATE: Dict[str, Any] = {
    "deck_loaded": False,
    "deck_name": "No Deck Loaded",
    "models": [],
    "notes": [],
    "field_mappings": {
        "sentence_field": "",
        "vocab_field": "",
        "meaning_field": "",
    },
    "analyzed_count": 0,
    "sync_engine": SyncEngine(),
    "ai_analyzer": LocalAIAnalyzer(),
}

SAMPLE_JAPANESE_DECK = [
    {
        "id": 1,
        "deck_name": "JLPT Master - Core Vocab & Grammar",
        "model_name": "Japanese Vocab & Context",
        "fields": {
            "Vocabulary": "出かける (でかける)",
            "English_Meaning": "to go out; to depart",
            "Sentence": "雨が降っているにもかかわらず、彼は出かけた。",
            "Sentence_English": "He went out despite the rain.",
            "Notes": "Focus on the conjunction nuance."
        }
    },
    {
        "id": 2,
        "deck_name": "JLPT Master - Core Vocab & Grammar",
        "model_name": "Japanese Vocab & Context",
        "fields": {
            "Vocabulary": "吸う (すう)",
            "English_Meaning": "to smoke; to inhale",
            "Sentence": "この病院の敷地内でタバコを吸ってはいけません。",
            "Sentence_English": "You must not smoke tobacco on the grounds of this hospital.",
            "Notes": "Formal prohibition"
        }
    },
    {
        "id": 3,
        "deck_name": "JLPT Master - Core Vocab & Grammar",
        "model_name": "Japanese Vocab & Context",
        "fields": {
            "Vocabulary": "休む (やすむ)",
            "English_Meaning": "to rest; to be absent",
            "Sentence": "明日は大事な最終面接があるから、休むわけにはいかない。",
            "Sentence_English": "Since tomorrow is the crucial final interview, I cannot afford to take the day off.",
            "Notes": "Moral / situational constraint"
        }
    },
    {
        "id": 4,
        "deck_name": "JLPT Master - Core Vocab & Grammar",
        "model_name": "Japanese Vocab & Context",
        "fields": {
            "Vocabulary": "作業 (さぎょう)",
            "English_Meaning": "work; operation; task",
            "Sentence": "安全マニュアルに沿って正確に作業を進めてください。",
            "Sentence_English": "Please proceed with the work accurately in accordance with the safety manual.",
            "Notes": "Following rules or guidelines"
        }
    },
    {
        "id": 5,
        "deck_name": "JLPT Master - Core Vocab & Grammar",
        "model_name": "Japanese Vocab & Context",
        "fields": {
            "Vocabulary": "認める (みとめる)",
            "English_Meaning": "to recognize; to acknowledge; to admit",
            "Sentence": "これほど明白な証拠が揃っている以上、事実を認めざるを得ない。",
            "Sentence_English": "Given that this much clear evidence is assembled, we have no choice but to admit the facts.",
            "Notes": "Reluctant obligation"
        }
    },
    {
        "id": 6,
        "deck_name": "JLPT Master - Core Vocab & Grammar",
        "model_name": "Japanese Vocab & Context",
        "fields": {
            "Vocabulary": "疲れる (つかれる)",
            "English_Meaning": "to get tired; to be exhausted",
            "Sentence": "彼はずっと徹夜で仕事をしているから、疲れているに違いない。",
            "Sentence_English": "He has been working all night, so he must surely be exhausted.",
            "Notes": "High subjective certainty"
        }
    },
    {
        "id": 7,
        "deck_name": "JLPT Master - Core Vocab & Grammar",
        "model_name": "Japanese Vocab & Context",
        "fields": {
            "Vocabulary": "食べる (たべる)",
            "English_Meaning": "to eat",
            "Sentence": "日本に来てから、納豆が食べられるようになった。",
            "Sentence_English": "Since coming to Japan, I have reached the point where I can eat natto.",
            "Notes": "Change of ability over time"
        }
    },
    {
        "id": 8,
        "deck_name": "JLPT Master - Core Vocab & Grammar",
        "model_name": "Japanese Vocab & Context",
        "fields": {
            "Vocabulary": "練習 (れんしゅう)",
            "English_Meaning": "practice; training",
            "Sentence": "ピアノは練習すればするほど上手になります。",
            "Sentence_English": "The more you practice the piano, the better you become.",
            "Notes": "Proportional increase"
        }
    },
    {
        "id": 9,
        "deck_name": "JLPT Master - Core Vocab & Grammar",
        "model_name": "Japanese Vocab & Context",
        "fields": {
            "Vocabulary": "無礼 (ぶれい)",
            "English_Meaning": "rude; impolite",
            "Sentence": "彼の無礼極まりない発言には本当に腹が立った。",
            "Sentence_English": "I was truly furious at his utterly insolent remark.",
            "Notes": "Extreme peak degree"
        }
    },
    {
        "id": 10,
        "deck_name": "JLPT Master - Core Vocab & Grammar",
        "model_name": "Japanese Vocab & Context",
        "fields": {
            "Vocabulary": "忘れる (わすれる)",
            "English_Meaning": "to forget",
            "Sentence": "慌てて家を出たせいで、駅に着いてから財布を忘れてしまったことに気づいた。",
            "Sentence_English": "Because I left the house in a rush, I realized after arriving at the station that I had completely forgotten my wallet.",
            "Notes": "Negative cause + regretful action"
        }
    }
]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status", methods=["GET"])
def get_status():
    ollama_info = STATE["ai_analyzer"].check_connection()
    return jsonify({
        "deck_loaded": STATE["deck_loaded"],
        "deck_name": STATE["deck_name"],
        "total_cards": len(STATE["notes"]),
        "analyzed_count": STATE["analyzed_count"],
        "field_mappings": STATE["field_mappings"],
        "ollama": ollama_info,
        "grammar_catalog_size": len(GRAMMAR_CATALOG),
    })


@app.route("/api/upload", methods=["POST"])
def upload_apkg():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        content = file.read()
        parsed = parse_apkg(content)

        STATE["deck_loaded"] = True
        STATE["deck_name"] = file.filename
        STATE["models"] = parsed["models"]
        STATE["notes"] = []
        STATE["analyzed_count"] = 0

        # Auto-detect field candidates
        candidate_fields = set()
        for m in parsed["models"]:
            for f in m.get("fields", []):
                candidate_fields.add(f)

        # Populate internal cards
        for n in parsed["notes"]:
            STATE["notes"].append({
                "id": n["id"],
                "guid": n["guid"],
                "model_name": n["model_name"],
                "deck_name": n["deck_name"],
                "fields": n["fields"],
                "target_word": "",
                "original_sentence": "",
                "annotated_html": "",
                "grammar_points": [],
                "review_status": "new",
                "repetitions": 0,
            })

        # Try sensible defaults for field mapping
        sentence_f = next((f for f in candidate_fields if any(w in f.lower() for w in ["sentence", "expression", "text", "german", "front", "japanese"])), "")
        vocab_f = next((f for f in candidate_fields if any(w in f.lower() for w in ["vocab", "word", "kanji", "front"])), "")
        meaning_f = next((f for f in candidate_fields if any(w in f.lower() for w in ["meaning", "english", "back", "translation"])), "")

        STATE["field_mappings"] = {
            "sentence_field": sentence_f,
            "vocab_field": vocab_f,
            "meaning_field": meaning_f,
        }

        # Apply initial mapping if detected
        if sentence_f:
            _apply_field_mapping()

        return jsonify({
            "success": True,
            "deck_name": STATE["deck_name"],
            "total_cards": len(STATE["notes"]),
            "models": parsed["models"],
            "available_fields": list(candidate_fields),
            "field_mappings": STATE["field_mappings"],
            "preview_cards": STATE["notes"][:5],
        })

    except Exception as e:
        logger.exception("Error parsing uploaded deck")
        return jsonify({"error": f"Failed to parse Anki deck: {str(e)}"}), 500


@app.route("/api/sample-deck", methods=["POST"])
def load_sample_deck():
    """Loads a pre-packaged authentic Japanese deck for immediate testing."""
    STATE["deck_loaded"] = True
    STATE["deck_name"] = "JLPT Master - Core Vocab & Grammar (Sample)"
    STATE["models"] = [{"id": 1, "name": "Japanese Vocab & Context", "fields": ["Vocabulary", "English_Meaning", "Sentence", "Sentence_English", "Notes"]}]
    STATE["notes"] = []
    STATE["analyzed_count"] = 0

    for item in SAMPLE_JAPANESE_DECK:
        STATE["notes"].append({
            "id": item["id"],
            "guid": f"sample_{item['id']}",
            "model_name": item["model_name"],
            "deck_name": item["deck_name"],
            "fields": item["fields"],
            "target_word": item["fields"]["Vocabulary"],
            "original_sentence": item["fields"]["Sentence"],
            "annotated_html": "",
            "grammar_points": [],
            "review_status": "new",
            "repetitions": 0,
        })

    STATE["field_mappings"] = {
        "sentence_field": "Sentence",
        "vocab_field": "Vocabulary",
        "meaning_field": "English_Meaning",
    }

    _apply_field_mapping()

    return jsonify({
        "success": True,
        "deck_name": STATE["deck_name"],
        "total_cards": len(STATE["notes"]),
        "available_fields": ["Vocabulary", "English_Meaning", "Sentence", "Sentence_English", "Notes"],
        "field_mappings": STATE["field_mappings"],
        "preview_cards": STATE["notes"][:5],
    })


@app.route("/api/configure-fields", methods=["POST"])
def configure_fields():
    data = request.json or {}
    sentence_field = data.get("sentence_field", "").strip()
    vocab_field = data.get("vocab_field", "").strip()
    meaning_field = data.get("meaning_field", "").strip()

    if not sentence_field:
        return jsonify({"error": "Example Sentence field must be selected"}), 400

    STATE["field_mappings"] = {
        "sentence_field": sentence_field,
        "vocab_field": vocab_field,
        "meaning_field": meaning_field,
    }

    _apply_field_mapping()

    return jsonify({
        "success": True,
        "field_mappings": STATE["field_mappings"],
        "preview_cards": STATE["notes"][:5],
    })


def _apply_field_mapping():
    s_field = STATE["field_mappings"]["sentence_field"]
    v_field = STATE["field_mappings"]["vocab_field"]
    m_field = STATE["field_mappings"]["meaning_field"]

    for note in STATE["notes"]:
        fields = note.get("fields", {})
        note["original_sentence"] = fields.get(s_field, "")
        if v_field:
            note["target_word"] = fields.get(v_field, "")
        if m_field:
            note["meaning"] = fields.get(m_field, "")


@app.route("/api/analyze-batch", methods=["POST"])
def analyze_batch():
    """
    Analyzes all loaded cards (or a specific subset) using Local AI / Grammar KB.
    """
    if not STATE["deck_loaded"] or not STATE["notes"]:
        return jsonify({"error": "No cards loaded to analyze."}), 400

    data = request.json or {}
    card_ids = data.get("card_ids")  # Optional list of specific card IDs
    force_offline = data.get("force_offline", False)

    analyzer: LocalAIAnalyzer = STATE["ai_analyzer"]
    provider_used = ""
    processed_count = 0

    for note in STATE["notes"]:
        if card_ids and note["id"] not in card_ids:
            continue

        sentence = note.get("original_sentence", "")
        if sentence:
            annotated_html, points, provider = analyzer.analyze_sentence(sentence, force_offline=force_offline)
            note["annotated_html"] = annotated_html
            note["grammar_points"] = points
            provider_used = provider
            processed_count += 1

    STATE["analyzed_count"] = sum(1 for n in STATE["notes"] if n.get("annotated_html"))

    return jsonify({
        "success": True,
        "processed_count": processed_count,
        "total_analyzed": STATE["analyzed_count"],
        "provider": provider_used,
        "cards": STATE["notes"],
    })


@app.route("/api/cards", methods=["GET"])
def get_cards():
    return jsonify({
        "deck_name": STATE["deck_name"],
        "cards": STATE["notes"],
        "total": len(STATE["notes"]),
        "analyzed_count": STATE["analyzed_count"],
    })


@app.route("/api/review-card", methods=["POST"])
def review_card():
    data = request.json or {}
    card_id = data.get("card_id")
    grade = data.get("grade", "good")  # again, hard, good, easy

    target_note = next((n for n in STATE["notes"] if n["id"] == card_id), None)
    if not target_note:
        return jsonify({"error": "Card not found"}), 404

    target_note["repetitions"] = target_note.get("repetitions", 0) + 1
    if grade == "again":
        target_note["review_status"] = "learning"
    elif grade in ["good", "easy"]:
        target_note["review_status"] = "review"

    return jsonify({"success": True, "card": target_note})


@app.route("/api/sync/status", methods=["POST"])
def check_sync_status():
    data = request.json or {}
    drive_path = data.get("drive_path", "")
    info = STATE["sync_engine"].check_drive_status(drive_path)
    return jsonify(info)


@app.route("/api/sync/export", methods=["POST"])
def sync_export():
    data = request.json or {}
    drive_path = data.get("drive_path", "").strip()
    if not drive_path:
        return jsonify({"error": "Drive folder path required"}), 400

    try:
        res = STATE["sync_engine"].export_to_drive(
            target_directory=drive_path,
            deck_name=STATE["deck_name"],
            notes=STATE["notes"],
            device_name="macOS Studio"
        )
        return jsonify(res)
    except Exception as e:
        logger.exception("Sync export failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/sync/import", methods=["POST"])
def sync_import():
    data = request.json or {}
    drive_path = data.get("drive_path", "").strip()
    if not drive_path:
        return jsonify({"error": "Drive folder path required"}), 400

    try:
        res = STATE["sync_engine"].import_from_drive(drive_path)
        STATE["deck_loaded"] = True
        STATE["deck_name"] = res["meta"].get("deck_name", "Synced Deck")
        STATE["notes"] = res["notes"]
        STATE["analyzed_count"] = sum(1 for n in STATE["notes"] if n.get("annotated_html"))

        return jsonify({
            "success": True,
            "total_notes": len(STATE["notes"]),
            "deck_name": STATE["deck_name"],
            "meta": res["meta"],
            "cards": STATE["notes"][:10],
        })
    except Exception as e:
        logger.exception("Sync import failed")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
