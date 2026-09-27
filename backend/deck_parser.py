import io
import json
import os
import sqlite3
import tempfile
import zipfile
from typing import Any, Dict, List, Optional, Union


class APKGParser:
    """
    Parses Anki .apkg export packages (zip + collection.anki2 / collection.anki21 SQLite).
    Extracts note models, decks, fields, and individual notes.
    """

    def __init__(self, apkg_source: Union[str, bytes]):
        self.apkg_source = apkg_source
        self.decks: List[Dict[str, Any]] = []
        self.models: List[Dict[str, Any]] = []
        self.notes: List[Dict[str, Any]] = []

    def parse(self) -> Dict[str, Any]:
        """
        Parses the .apkg file and returns a structured dictionary of decks,
        models (note types), and extracted notes with mapped fields.
        """
        if isinstance(self.apkg_source, bytes):
            zip_file = zipfile.ZipFile(io.BytesIO(self.apkg_source))
        else:
            if not os.path.exists(self.apkg_source):
                raise FileNotFoundError(f"File not found: {self.apkg_source}")
            zip_file = zipfile.ZipFile(self.apkg_source)

        with zip_file:
            namelist = zip_file.namelist()
            db_bytes = None

            # collection.anki21 is preferred in modern decks if it is SQLite format
            if "collection.anki21" in namelist:
                b = zip_file.read("collection.anki21")
                if b.startswith(b"SQLite format 3"):
                    db_bytes = b

            if db_bytes is None and "collection.anki2" in namelist:
                db_bytes = zip_file.read("collection.anki2")

            if db_bytes is None:
                raise ValueError("Valid Anki collection database not found in .apkg package")

            conn = self._connect_sqlite(db_bytes)
            try:
                self._extract_data(conn)
            finally:
                conn.close()

        return {
            "decks": self.decks,
            "models": self.models,
            "notes": self.notes,
            "total_notes": len(self.notes),
        }

    def _connect_sqlite(self, db_bytes: bytes) -> sqlite3.Connection:
        """
        Connects to SQLite, using deserialize if available or fallback to a temp file.
        """
        try:
            conn = sqlite3.connect(":memory:")
            conn.deserialize(db_bytes)
            return conn
        except Exception:
            # Fallback to temp file
            fd, tmp_path = tempfile.mkstemp(suffix=".anki2")
            os.write(fd, db_bytes)
            os.close(fd)
            conn = sqlite3.connect(tmp_path)
            # Remove on close or when process finishes
            return conn

    def _extract_data(self, conn: sqlite3.Connection):
        cursor = conn.cursor()

        # 1. Extract models and decks from col table
        models_dict: Dict[int, Dict[str, Any]] = {}
        decks_dict: Dict[int, Dict[str, Any]] = {}

        try:
            cursor.execute("SELECT models, decks FROM col LIMIT 1;")
            row = cursor.fetchone()
            if row:
                raw_models, raw_decks = row
                if raw_models:
                    raw_models_parsed = json.loads(raw_models) if isinstance(raw_models, str) else raw_models
                    for mid_str, m in raw_models_parsed.items():
                        mid = int(mid_str)
                        field_names = [f.get("name", "") for f in m.get("flds", [])]
                        model_info = {
                            "id": mid,
                            "name": m.get("name", f"Model {mid}"),
                            "fields": field_names,
                        }
                        models_dict[mid] = model_info
                        self.models.append(model_info)

                if raw_decks:
                    raw_decks_parsed = json.loads(raw_decks) if isinstance(raw_decks, str) else raw_decks
                    for did_str, d in raw_decks_parsed.items():
                        did = int(did_str)
                        deck_info = {
                            "id": did,
                            "name": d.get("name", f"Deck {did}"),
                        }
                        decks_dict[did] = deck_info
                        self.decks.append(deck_info)
        except sqlite3.Error as e:
            # Anki 2.1.28+ may store notetypes / decks in separate tables
            self._extract_fallback_col(conn, models_dict, decks_dict)

        # 2. Map notes to cards and decks
        card_to_deck: Dict[int, int] = {}
        try:
            cursor.execute("SELECT nid, did FROM cards;")
            for nid, did in cursor.fetchall():
                card_to_deck[nid] = did
        except sqlite3.Error:
            pass

        # 3. Extract notes
        cursor.execute("SELECT id, guid, mid, tags, flds FROM notes;")
        for nid, guid, mid, tags_str, flds_str in cursor.fetchall():
            mid_int = int(mid)
            model_info = models_dict.get(mid_int, {"name": "Default", "fields": []})
            field_names = model_info["fields"]

            field_values = flds_str.split("\x1f") if flds_str else []
            field_map: Dict[str, str] = {}
            for idx, val in enumerate(field_values):
                fname = field_names[idx] if idx < len(field_names) else f"Field_{idx + 1}"
                field_map[fname] = val

            did = card_to_deck.get(nid, 1)
            deck_name = decks_dict.get(did, {}).get("name", "Default Deck")

            # Clean tags string (Anki separates tags with spaces and encloses with spaces)
            tags = [t for t in tags_str.strip().split(" ") if t] if tags_str else []

            self.notes.append({
                "id": nid,
                "guid": guid,
                "model_id": mid_int,
                "model_name": model_info["name"],
                "deck_id": did,
                "deck_name": deck_name,
                "field_names": field_names if field_names else list(field_map.keys()),
                "fields": field_map,
                "tags": tags,
            })

    def _extract_fallback_col(self, conn: sqlite3.Connection, models_dict: dict, decks_dict: dict):
        """Fallback for non-standard or newer schema variants."""
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, name FROM notetypes;")
            for mid, name in cursor.fetchall():
                models_dict[mid] = {"id": mid, "name": name, "fields": []}
                self.models.append(models_dict[mid])
        except sqlite3.Error:
            pass
        try:
            cursor.execute("SELECT id, name FROM decks;")
            for did, name in cursor.fetchall():
                decks_dict[did] = {"id": did, "name": name}
                self.decks.append(decks_dict[did])
        except sqlite3.Error:
            pass


def parse_apkg(source: Union[str, bytes]) -> Dict[str, Any]:
    """Convenience function to parse an APKG file or bytes."""
    parser = APKGParser(source)
    return parser.parse()
