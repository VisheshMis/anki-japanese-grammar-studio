import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import requests

from .grammar_kb import annotate_sentence, find_candidate_grammar

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:7b"

SYSTEM_PROMPT = """You are an expert Japanese linguist and JLPT pedagogue.
Given a Japanese sentence, identify the key grammar patterns (JLPT N5 to N1 constructions, auxiliary verb conjugations, and functional expressions).

Ignore standard nouns that merely contain homophonic characters.
Only identify real functional grammar patterns active in the sentence.

For each active grammar point, return a JSON object with:
- "pattern": standard Japanese grammar point name (e.g. "〜わけにはいかない", "〜にもかかわらず")
- "matched_text": exact substring from the sentence
- "jlpt": JLPT level ("N5", "N4", "N3", "N2", or "N1")
- "meaning": concise English meaning
- "formation": connection rule in this sentence (e.g. "Verb Plain + わけにはいかない")
- "explanation": brief pedagogical explanation of why this grammar pattern is used in context

Return ONLY a valid JSON object matching:
{
  "grammar_points": [
    {
      "pattern": "...",
      "matched_text": "...",
      "jlpt": "N3",
      "meaning": "...",
      "formation": "...",
      "explanation": "..."
    }
  ]
}"""


class LocalAIAnalyzer:
    """
    Interfaces with local LLMs (via Ollama or OpenAI-compatible endpoints)
    and falls back to grammar_kb pattern matching when offline.
    """

    def __init__(self, ollama_url: str = DEFAULT_OLLAMA_URL, model: str = DEFAULT_MODEL):
        self.ollama_url = ollama_url.rstrip("/")
        self.model = model

    def check_connection(self) -> Dict[str, Any]:
        """Checks if Ollama service is reachable and lists available models."""
        try:
            resp = requests.get(f"{self.ollama_url}/api/tags", timeout=2.0)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return {
                    "online": True,
                    "models": models,
                    "current_model": self.model,
                    "model_available": any(self.model in m for m in models),
                }
        except Exception:
            pass

        return {
            "online": False,
            "models": [],
            "current_model": self.model,
            "model_available": False,
        }

    def analyze_sentence(self, sentence: str, force_offline: bool = False) -> Tuple[str, List[Dict[str, Any]], str]:
        """
        Analyzes a sentence using Local LLM (if online) or Rule-Based KB (if offline).
        Returns (annotated_html, grammar_points, provider_used).
        """
        clean_sentence = sentence.strip()
        if not clean_sentence:
            return "", [], "none"

        # 1. Check for candidate grammar rules to ground the AI
        candidates = find_candidate_grammar(clean_sentence)

        if not force_offline:
            ai_result = self._call_ollama(clean_sentence, candidates)
            if ai_result:
                # Merge character offsets for precise HTML injection
                annotated_html, confirmed_points = self._format_ai_response(clean_sentence, ai_result)
                if confirmed_points:
                    return annotated_html, confirmed_points, f"Ollama ({self.model})"

        # 2. Fallback to Rule-Based Grammar KB
        annotated_html, matches = annotate_sentence(clean_sentence, candidates)
        return annotated_html, matches, "Built-in Grammar KB (Offline)"

    def _call_ollama(self, sentence: str, candidates: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """Calls the local Ollama API to detect grammar patterns."""
        candidate_hints = ""
        if candidates:
            candidate_hints = "\nCandidate patterns identified by dictionary lookup:\n" + "\n".join(
                [f"- {c['pattern']} ({c['jlpt']}): {c['meaning']}" for c in candidates]
            )

        prompt = f"Sentence: {sentence}\n{candidate_hints}\nAnalyze the sentence and output the JSON object."

        try:
            url = f"{self.ollama_url}/api/chat"
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "format": "json",
                "stream": False,
                "options": {
                    "temperature": 0.1,
                },
            }
            resp = requests.post(url, json=payload, timeout=25.0)
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("message", {}).get("content", "")
                parsed = json.loads(content)
                if isinstance(parsed, dict) and "grammar_points" in parsed:
                    return parsed["grammar_points"]
        except Exception as e:
            logger.debug(f"Ollama call failed or timed out: {e}")

        return None

    def _format_ai_response(self, sentence: str, ai_points: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Maps AI identified substrings to character positions in the original sentence
        and constructs the highlighted HTML spans.
        """
        matched_items = []
        for pt in ai_points:
            text = pt.get("matched_text", "").strip()
            if not text or text not in sentence:
                continue

            # Find position in sentence
            start = sentence.find(text)
            end = start + len(text)
            matched_items.append({
                "pattern": pt.get("pattern", text),
                "matched_text": text,
                "start": start,
                "end": end,
                "jlpt": pt.get("jlpt", "N3"),
                "meaning": pt.get("meaning", ""),
                "formation": pt.get("formation", ""),
                "explanation": pt.get("explanation", ""),
            })

        if not matched_items:
            return sentence, []

        return annotate_sentence(sentence, matched_items)
