"""
brand-voice-consistency-skill: Client SDK
Audit and enforce brand voice consistency across marketing content.
"""

from __future__ import annotations
import re
from typing import Optional

DEFAULT_BRAND_PROFILE = {
    "tone": ["professional", "friendly", "clear"],
    "values": ["quality", "innovation", "trust"],
    "prohibited_words": ["cheap", "dirt cheap", "crappy", "fail", "bad", "worst", "hate"],
    "preferred_words": ["premium", "innovative", "trusted", "seamless", "empowering"],
    "persona": "knowledgeable friend",
    "sentence_length": "short-to-medium",
    "use_contractions": True,
    "exclamation_limit": 1,
}

PASSIVE_VOICE_PATTERNS = [
    r"\bwas \w+ed\b", r"\bwere \w+ed\b", r"\bis \w+ed\b",
    r"\bare \w+ed\b", r"\bbeen \w+ed\b",
]

FILLER_WORDS = [
    "very", "really", "just", "quite", "basically", "literally",
    "actually", "honestly", "definitely", "absolutely"
]

JARGON_WORDS = [
    "synergy", "leverage", "paradigm", "disruptive", "holistic",
    "scalable", "agile", "pivot", "bandwidth", "circle back"
]


class BrandVoiceClient:
    """
    SDK for auditing brand voice consistency in marketing content.

    Checks:
      - Prohibited word usage
      - Preferred word usage
      - Passive voice overuse
      - Filler word density
      - Sentence length compliance
      - Exclamation mark overuse
      - Brand persona alignment
    """

    def __init__(self, brand_profile: Optional[dict] = None, strict_mode: bool = False):
        self.profile = {**DEFAULT_BRAND_PROFILE, **(brand_profile or {})}
        self.strict_mode = strict_mode

    def audit(self, content_pieces: list[str]) -> dict:
        """
        Audit a list of content strings for brand voice consistency.

        Args:
            content_pieces: List of text strings to evaluate.

        Returns:
            dict with: audit_results, overall_score, critical_issues
        """
        results = []
        for i, text in enumerate(content_pieces):
            result = self._audit_piece(text, i)
            results.append(result)

        scores = [r["consistency_score"] for r in results]
        overall = round(sum(scores) / len(scores), 1) if scores else 0.0

        critical = []
        for r in results:
            for issue in r["issues"]:
                if issue["severity"] == "critical":
                    critical.append({"content_index": r["index"], "issue": issue})

        return {
            "audit_results": results,
            "overall_score": overall,
            "critical_issues": critical,
            "pieces_audited": len(content_pieces),
            "brand_profile_summary": {
                "tone": self.profile.get("tone"),
                "persona": self.profile.get("persona"),
            }
        }

    def _audit_piece(self, text: str, index: int) -> dict:
        issues = []
        suggestions = []
        deductions = 0.0

        # Check prohibited words
        prohibited = self.profile.get("prohibited_words", [])
        for word in prohibited:
            if re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE):
                issues.append({"type": "prohibited_word", "detail": f"Prohibited word: '{word}'", "severity": "critical"})
                deductions += 20
                suggestions.append(f"Remove '{word}' — it conflicts with brand values.")

        # Check preferred words presence
        preferred = self.profile.get("preferred_words", [])
        preferred_found = [w for w in preferred if re.search(rf"\b{re.escape(w)}\b", text, re.IGNORECASE)]
        if preferred_found:
            deductions -= min(len(preferred_found) * 3, 10)  # Bonus for using preferred words
        elif self.strict_mode and len(text.split()) > 20:
            issues.append({"type": "no_preferred_words", "detail": "No preferred brand words detected.", "severity": "warning"})
            deductions += 5

        # Passive voice check
        passive_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in PASSIVE_VOICE_PATTERNS)
        words = text.split()
        if passive_count > 2 or (len(words) > 30 and passive_count / max(len(words), 1) > 0.05):
            issues.append({"type": "passive_voice", "detail": f"{passive_count} passive voice instances detected.", "severity": "warning"})
            deductions += 8
            suggestions.append("Rewrite passive sentences in active voice for stronger brand impact.")

        # Filler word density
        fillers_found = [w for w in FILLER_WORDS if re.search(rf"\b{re.escape(w)}\b", text, re.IGNORECASE)]
        if len(fillers_found) > 2:
            issues.append({"type": "filler_words", "detail": f"Filler words detected: {', '.join(fillers_found[:4])}", "severity": "info"})
            deductions += len(fillers_found) * 2
            suggestions.append(f"Remove filler words ({', '.join(fillers_found[:3])}) for crisper copy.")

        # Jargon check
        jargon_found = [w for w in JARGON_WORDS if re.search(rf"\b{re.escape(w)}\b", text, re.IGNORECASE)]
        if jargon_found:
            issues.append({"type": "jargon", "detail": f"Corporate jargon: {', '.join(jargon_found)}", "severity": "warning"})
            deductions += 10
            suggestions.append(f"Replace jargon ({', '.join(jargon_found)}) with plain, customer-friendly language.")

        # Exclamation mark overuse
        exc_count = text.count("!")
        limit = self.profile.get("exclamation_limit", 1)
        if exc_count > limit:
            issues.append({"type": "exclamation_overuse", "detail": f"{exc_count} exclamation marks (limit: {limit}).", "severity": "info"})
            deductions += (exc_count - limit) * 5
            suggestions.append(f"Reduce exclamation marks to {limit} per piece for a more confident tone.")

        # Sentence length
        sentences = re.split(r"[.!?]+", text)
        long_sentences = [s for s in sentences if len(s.split()) > 25]
        if long_sentences:
            issues.append({"type": "long_sentences", "detail": f"{len(long_sentences)} sentence(s) exceed 25 words.", "severity": "info"})
            deductions += len(long_sentences) * 5
            suggestions.append("Break long sentences into shorter ones for better readability.")

        # Contractions check
        if self.profile.get("use_contractions"):
            no_contractions = re.findall(r"\b(do not|cannot|will not|it is|they are|we are|you are|I am)\b", text)
            if len(no_contractions) > 2:
                issues.append({"type": "no_contractions", "detail": "Formal phrasing detected — use contractions for friendlier tone.", "severity": "info"})
                deductions += 5
                suggestions.append("Use contractions (don't, can't, we're) to match the brand's friendly persona.")

        score = round(max(0.0, min(100.0, 100 - deductions)), 1)

        return {
            "index": index,
            "text_preview": text[:100] + "..." if len(text) > 100 else text,
            "consistency_score": score,
            "issues": issues,
            "suggestions": suggestions[:5],
            "preferred_words_used": preferred_found,
            "word_count": len(words),
        }
