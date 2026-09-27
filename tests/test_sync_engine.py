import os
import shutil
import tempfile
import unittest
from backend.sync_engine import SyncEngine


class TestSyncEngine(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.engine = SyncEngine(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_drive_status_not_created(self):
        status = self.engine.check_drive_status(self.test_dir)
        self.assertTrue(status["exists"])
        self.assertTrue(status["writable"])
        self.assertFalse(status["has_sync_db"])

    def test_export_and_import_cycle(self):
        test_notes = [
            {
                "id": 101,
                "guid": "guid_101",
                "model_name": "Japanese Vocab",
                "target_word": "出かける",
                "original_sentence": "雨が降っているにもかかわらず、出かけた。",
                "annotated_html": "雨が降っている<span class=\"grammar-point\">にもかかわらず</span>、出かけた。",
                "grammar_points": [{"pattern": "〜にもかかわらず", "jlpt": "N3"}],
                "custom_notes": "Important N3 point",
                "review_status": "learning",
                "repetitions": 2,
            },
            {
                "id": 102,
                "guid": "guid_102",
                "model_name": "Japanese Vocab",
                "target_word": "吸う",
                "original_sentence": "タバコを吸ってはいけない。",
                "annotated_html": "タバコを吸っ<span class=\"grammar-point\">てはいけない</span>。",
                "grammar_points": [{"pattern": "〜てはいけない", "jlpt": "N5"}],
                "custom_notes": "",
                "review_status": "review",
                "repetitions": 5,
            }
        ]

        export_res = self.engine.export_to_drive(
            target_directory=self.test_dir,
            deck_name="Test JLPT Deck",
            notes=test_notes,
            device_name="macOS Test"
        )
        self.assertTrue(export_res["success"])
        self.assertEqual(export_res["cards_synced"], 2)

        # Check drive status updated
        status = self.engine.check_drive_status(self.test_dir)
        self.assertTrue(status["has_sync_db"])
        self.assertEqual(status["card_count"], 2)

        # Re-import and verify data integrity
        import_res = self.engine.import_from_drive(self.test_dir)
        self.assertEqual(import_res["total_notes"], 2)
        self.assertEqual(import_res["meta"]["deck_name"], "Test JLPT Deck")

        imported_cards = {c["id"]: c for c in import_res["notes"]}
        self.assertIn(101, imported_cards)
        self.assertEqual(imported_cards[101]["target_word"], "出かける")
        self.assertEqual(imported_cards[101]["review_status"], "learning")
        self.assertEqual(imported_cards[101]["grammar_points"][0]["pattern"], "〜にもかかわらず")


if __name__ == "__main__":
    unittest.main()
