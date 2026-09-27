import unittest
from backend.grammar_kb import GRAMMAR_CATALOG, annotate_sentence, find_candidate_grammar


class TestGrammarKB(unittest.TestCase):

    def test_catalog_integrity(self):
        self.assertGreater(len(GRAMMAR_CATALOG), 20)
        for entry in GRAMMAR_CATALOG:
            self.assertIn("pattern", entry)
            self.assertIn("regex", entry)
            self.assertIn("jlpt", entry)
            self.assertIn("meaning", entry)
            self.assertIn("formation", entry)

    def test_n5_prohibition(self):
        sentence = "ここでタバコを吸ってはいけない。"
        matches = find_candidate_grammar(sentence)
        patterns = [m["pattern"] for m in matches]
        self.assertIn("〜てはいけない", patterns)

        annotated, _ = annotate_sentence(sentence, matches)
        self.assertIn('class="grammar-point jlpt-n5"', annotated)
        self.assertIn('data-meaning="must not; may not (prohibition)"', annotated)

    def test_n3_contrast(self):
        sentence = "雨が降っているにもかかわらず、出かけた。"
        matches = find_candidate_grammar(sentence)
        patterns = [m["pattern"] for m in matches]
        self.assertIn("〜にもかかわらず", patterns)

        annotated, _ = annotate_sentence(sentence, matches)
        self.assertIn('class="grammar-point jlpt-n3"', annotated)

    def test_n2_obligation(self):
        sentence = "事実を認めざるを得ない。"
        matches = find_candidate_grammar(sentence)
        patterns = [m["pattern"] for m in matches]
        self.assertIn("〜ざるを得ない", patterns)

        annotated, _ = annotate_sentence(sentence, matches)
        self.assertIn('class="grammar-point jlpt-n2"', annotated)

    def test_n1_peak(self):
        sentence = "彼の無礼極まりない態度に腹が立った。"
        matches = find_candidate_grammar(sentence)
        patterns = [m["pattern"] for m in matches]
        self.assertIn("〜極まりない", patterns)

        annotated, _ = annotate_sentence(sentence, matches)
        self.assertIn('class="grammar-point jlpt-n1"', annotated)


if __name__ == "__main__":
    unittest.main()
