import json
import os
import shutil
import sqlite3
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

SYNC_DB_FILENAME = "anki_grammar_sync.db"


class SyncEngine:
    """
    Manages direct, serverless file synchronization to a user-selected drive or folder
    (e.g., Google Drive, iCloud Drive, OneDrive, or local directory).
    Stores annotations, grammar highlights, and review states in an SQLite sync bundle.
    """

    def __init__(self, target_directory: Optional[str] = None):
        self.target_directory = target_directory

    def set_target_directory(self, target_directory: str):
        self.target_directory = target_directory

    def get_sync_filepath(self, target_directory: Optional[str] = None) -> str:
        base_dir = target_directory or self.target_directory
        if not base_dir:
            raise ValueError("No target drive directory specified for sync.")
        return os.path.join(os.path.expanduser(base_dir), SYNC_DB_FILENAME)

    def check_drive_status(self, target_directory: Optional[str] = None) -> Dict[str, Any]:
        """
        Checks whether the specified drive directory exists, is writable,
        and whether an existing sync database is present.
        """
        base_dir = target_directory or self.target_directory
        if not base_dir:
            return {"configured": False, "exists": False, "writable": False, "has_sync_db": False}

        expanded_dir = os.path.expanduser(base_dir)
        exists = os.path.isdir(expanded_dir)
        writable = os.access(expanded_dir, os.W_OK) if exists else False
        sync_file = self.get_sync_filepath(expanded_dir)
        has_sync_db = os.path.isfile(sync_file)

        info = {
            "configured": True,
            "directory": expanded_dir,
            "exists": exists,
            "writable": writable,
            "has_sync_db": has_sync_db,
            "last_synced_at": None,
            "card_count": 0,
        }

        if has_sync_db:
            try:
                conn = sqlite3.connect(sync_file)
                cursor = conn.cursor()
                cursor.execute("SELECT val FROM sync_meta WHERE key='last_synced_at';")
                row = cursor.fetchone()
                if row:
                    info["last_synced_at"] = row[0]
                cursor.execute("SELECT count(*) FROM sync_notes;")
                info["card_count"] = cursor.fetchone()[0]
                conn.close()
            except Exception:
                pass

        return info

    def export_to_drive(
        self,
        target_directory: str,
        deck_name: str,
        notes: List[Dict[str, Any]],
        device_name: str = "macOS Studio",
    ) -> Dict[str, Any]:
        """
        Exports the annotated notes, grammar highlights, and review states
        into an SQLite database directly in the chosen drive folder.
        """
        expanded_dir = os.path.expanduser(target_directory)
        os.makedirs(expanded_dir, exist_ok=True)
        sync_file = self.get_sync_filepath(expanded_dir)

        now_iso = datetime.now(timezone.utc).isoformat()

        conn = sqlite3.connect(sync_file)
        cursor = conn.cursor()

        # Create schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_meta (
                key TEXT PRIMARY KEY,
                val TEXT
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_notes (
                id INTEGER PRIMARY KEY,
                guid TEXT,
                deck_name TEXT,
                model_name TEXT,
                target_word TEXT,
                original_sentence TEXT,
                annotated_html TEXT,
                grammar_points_json TEXT,
                custom_notes TEXT,
                review_status TEXT DEFAULT 'new',
                repetitions INTEGER DEFAULT 0,
                interval_days INTEGER DEFAULT 0,
                due_timestamp INTEGER DEFAULT 0,
                updated_at TEXT
            );
        """)

        # Upsert metadata
        cursor.execute("REPLACE INTO sync_meta (key, val) VALUES ('deck_name', ?);", (deck_name,))
        cursor.execute("REPLACE INTO sync_meta (key, val) VALUES ('last_synced_at', ?);", (now_iso,))
        cursor.execute("REPLACE INTO sync_meta (key, val) VALUES ('last_device', ?);", (device_name,))
        cursor.execute("REPLACE INTO sync_meta (key, val) VALUES ('total_cards', ?);", (str(len(notes)),))

        # Insert / Update notes
        for note in notes:
            nid = note.get("id")
            guid = note.get("guid", "")
            model_name = note.get("model_name", "")
            target_word = note.get("target_word", "")
            sentence = note.get("original_sentence", "")
            annotated_html = note.get("annotated_html", sentence)
            grammar_points = json.dumps(note.get("grammar_points", []), ensure_ascii=False)
            custom_notes = note.get("custom_notes", "")
            review_status = note.get("review_status", "new")
            repetitions = note.get("repetitions", 0)
            interval_days = note.get("interval_days", 0)
            due_timestamp = note.get("due_timestamp", int(time.time()))

            cursor.execute("""
                INSERT INTO sync_notes (
                    id, guid, deck_name, model_name, target_word, original_sentence,
                    annotated_html, grammar_points_json, custom_notes,
                    review_status, repetitions, interval_days, due_timestamp, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    annotated_html=excluded.annotated_html,
                    grammar_points_json=excluded.grammar_points_json,
                    custom_notes=excluded.custom_notes,
                    review_status=excluded.review_status,
                    repetitions=excluded.repetitions,
                    interval_days=excluded.interval_days,
                    due_timestamp=excluded.due_timestamp,
                    updated_at=excluded.updated_at;
            """, (
                nid, guid, deck_name, model_name, target_word, sentence,
                annotated_html, grammar_points, custom_notes,
                review_status, repetitions, interval_days, due_timestamp, now_iso
            ))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "sync_file": sync_file,
            "cards_synced": len(notes),
            "timestamp": now_iso,
        }

    def import_from_drive(self, target_directory: str) -> Dict[str, Any]:
        """
        Imports and merges the latest cards and study progress from the chosen drive folder.
        """
        sync_file = self.get_sync_filepath(target_directory)
        if not os.path.isfile(sync_file):
            raise FileNotFoundError(f"Sync file not found at: {sync_file}")

        conn = sqlite3.connect(sync_file)
        cursor = conn.cursor()

        meta = {}
        cursor.execute("SELECT key, val FROM sync_meta;")
        for k, v in cursor.fetchall():
            meta[k] = v

        notes = []
        cursor.execute("""
            SELECT id, guid, deck_name, model_name, target_word, original_sentence,
                   annotated_html, grammar_points_json, custom_notes,
                   review_status, repetitions, interval_days, due_timestamp, updated_at
            FROM sync_notes;
        """)

        for row in cursor.fetchall():
            (nid, guid, deck_name, model_name, target_word, sentence,
             annotated_html, grammar_json, custom_notes,
             review_status, repetitions, interval_days, due_timestamp, updated_at) = row

            try:
                grammar_points = json.loads(grammar_json) if grammar_json else []
            except Exception:
                grammar_points = []

            notes.append({
                "id": nid,
                "guid": guid,
                "deck_name": deck_name,
                "model_name": model_name,
                "target_word": target_word,
                "original_sentence": sentence,
                "annotated_html": annotated_html,
                "grammar_points": grammar_points,
                "custom_notes": custom_notes,
                "review_status": review_status,
                "repetitions": repetitions,
                "interval_days": interval_days,
                "due_timestamp": due_timestamp,
                "updated_at": updated_at,
            })

        conn.close()

        return {
            "meta": meta,
            "notes": notes,
            "total_notes": len(notes),
        }
