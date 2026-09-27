import io
import json
import sqlite3
import unittest
import zipfile
from backend.deck_parser import APKGParser, parse_apkg


class TestDeckParser(unittest.TestCase):

    def _create_mock_apkg(self) -> bytes:
        """Constructs a minimal valid .apkg zip file in memory."""
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        # col table
        cursor.execute("CREATE TABLE col (id integer primary key, models text, decks text);")
        models = {
            "1600000000": {
                "id": 1600000000,
                "name": "Japanese-Vocab",
                "flds": [
                    {"name": "Vocab", "ord": 0},
                    {"name": "Sentence", "ord": 1},
                    {"name": "English", "ord": 2}
                ]
            }
        }
        decks = {
            "1": {
                "id": 1,
                "name": "Default"
            },
            "1500000000": {
                "id": 1500000000,
                "name": "Core Japanese"
            }
        }
        cursor.execute("INSERT INTO col VALUES (1, ?, ?);", (json.dumps(models), json.dumps(decks)))

        # notes table
        cursor.execute("CREATE TABLE notes (id integer primary key, guid text, mid integer, tags text, flds text);")
        cursor.execute(
            "INSERT INTO notes VALUES (?, ?, ?, ?, ?);",
            (1, "guid1", 1600000000, " jlpt-n3 grammar ", "出かける\x1f雨が降っているにもかかわらず、出かけた。\x1fHe went out despite the rain.")
        )
        cursor.execute(
            "INSERT INTO notes VALUES (?, ?, ?, ?, ?);",
            (2, "guid2", 1600000000, " jlpt-n5 ", "吸う\x1fタバコを吸ってはいけない。\x1fMust not smoke.")
        )

        # cards table
        cursor.execute("CREATE TABLE cards (id integer primary key, nid integer, did integer);")
        cursor.execute("INSERT INTO cards VALUES (101, 1, 1500000000);")
        cursor.execute("INSERT INTO cards VALUES (102, 2, 1500000000);")

        conn.commit()
        db_bytes = conn.serialize()
        conn.close()

        # Create zip archive
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as z:
            z.writestr("collection.anki2", db_bytes)
        return zip_buf.getvalue()

    def test_mock_apkg_parsing(self):
        apkg_bytes = self._create_mock_apkg()
        res = parse_apkg(apkg_bytes)

        self.assertEqual(res["total_notes"], 2)
        self.assertEqual(len(res["models"]), 1)
        self.assertEqual(res["models"][0]["name"], "Japanese-Vocab")
        self.assertEqual(res["models"][0]["fields"], ["Vocab", "Sentence", "English"])

        note1 = res["notes"][0]
        self.assertEqual(note1["fields"]["Vocab"], "出かける")
        self.assertEqual(note1["fields"]["Sentence"], "雨が降っているにもかかわらず、出かけた。")
        self.assertEqual(note1["deck_name"], "Core Japanese")
        self.assertIn("jlpt-n3", note1["tags"])


if __name__ == "__main__":
    unittest.main()
