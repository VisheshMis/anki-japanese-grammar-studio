import json
import unittest
from backend.app import app


class TestAppEndpoints(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_status_endpoint(self):
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("deck_loaded", data)
        self.assertIn("ollama", data)
        self.assertIn("grammar_catalog_size", data)

    def test_sample_deck_and_analysis_flow(self):
        # 1. Load sample deck
        load_res = self.client.post("/api/sample-deck")
        self.assertEqual(load_res.status_code, 200)
        data = load_res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["total_cards"], 10)

        # 2. Configure fields
        config_res = self.client.post(
            "/api/configure-fields",
            data=json.dumps({
                "sentence_field": "Sentence",
                "vocab_field": "Vocabulary",
                "meaning_field": "English_Meaning"
            }),
            content_type="application/json"
        )
        self.assertEqual(config_res.status_code, 200)

        # 3. Trigger batch analysis (force offline to ensure fast deterministic run)
        analysis_res = self.client.post(
            "/api/analyze-batch",
            data=json.dumps({"force_offline": True}),
            content_type="application/json"
        )
        self.assertEqual(analysis_res.status_code, 200)
        analysis_data = analysis_res.get_json()
        self.assertTrue(analysis_data["success"])
        self.assertEqual(analysis_data["processed_count"], 10)

        # 4. Fetch cards and verify annotations
        cards_res = self.client.get("/api/cards")
        self.assertEqual(cards_res.status_code, 200)
        cards_data = cards_res.get_json()
        self.assertEqual(cards_data["total"], 10)

        card1 = cards_data["cards"][0]
        self.assertIn("grammar-point", card1["annotated_html"])
        self.assertGreater(len(card1["grammar_points"]), 0)


if __name__ == "__main__":
    unittest.main()
