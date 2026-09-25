"""
ScamCheck Rules-Based Baseline Detector Service.

Implements the detection pipeline adhering to DETECTION_SPEC.md:
1. Normalization
2. Indicator Detection
3. Category Scoring
4. Risk Assessment
5. Explanation & Guidance Generation
"""

from typing import Dict, List, Optional, Protocol, Tuple

from app.schemas import CheckResponse
from app.services.guidance import (
    generate_explanation,
    generate_safety_guidance,
    generate_summary,
)
from app.services.normalization import normalize_text
from app.services.rules import DetectedIndicator, detect_all_indicators


class DetectorService(Protocol):
    """Protocol defining the interface for all scam detection implementations."""

    def analyze(self, message: str) -> CheckResponse:
        """
        Analyze a message string and return a structured risk assessment.
        """
        ...


class RulesBaselineDetector:
    """
    Explainable rules-based baseline detector.

    Evaluates text messages against curated semantic and contextual patterns across
    three primary categories (bank_payment, fake_job, investment) and cross-cutting signals.
    """

    STRENGTH_WEIGHTS = {
        "strong": 3.0,
        "medium": 1.5,
        "weak": 0.5,
    }

    RISK_LABELS = {
        "low": "No obvious warning signs detected",
        "needs_verification": "Needs further verification",
        "high": "Multiple warning signs detected",
    }

    def analyze(self, message: str) -> CheckResponse:
        """
        Execute the complete baseline detection pipeline.
        """
        # Step 1: Text Normalization
        normalized_text = normalize_text(message)

        # Step 2: Indicator Detection
        detected_indicators = detect_all_indicators(normalized_text, message)

        # Step 3: Category Scoring
        category, category_scores = self._score_categories(detected_indicators)

        # Step 4: Risk Assessment
        risk_level, risk_label = self._assess_risk(detected_indicators, category, category_scores)

        # Step 5: Summary, Explanation, and Guidance
        summary = generate_summary(risk_level, category, detected_indicators)
        explanation = generate_explanation(risk_level, category, detected_indicators)
        safety_guidance = generate_safety_guidance(risk_level, category, detected_indicators)

        # Step 6: Map to CheckResponse contract
        indicator_labels = [ind.definition.label for ind in detected_indicators]

        return CheckResponse(
            risk_level=risk_level,
            risk_label=risk_label,
            summary=summary,
            category=category,
            explanation=explanation,
            indicators=indicator_labels,
            safety_guidance=safety_guidance,
        )

    def _score_categories(
        self,
        indicators: List[DetectedIndicator]
    ) -> Tuple[Optional[str], Dict[str, float]]:
        """
        Calculate evidence weight per category and determine the dominant category.
        """
        scores: Dict[str, float] = {
            "bank_payment": 0.0,
            "fake_job": 0.0,
            "investment": 0.0,
        }

        for ind in indicators:
            cat = ind.definition.category
            if cat and cat in scores:
                weight = self.STRENGTH_WEIGHTS.get(ind.definition.strength, 1.0)
                scores[cat] += weight

        # Determine dominant category
        best_category = None
        highest_score = 0.0

        for cat, score in scores.items():
            if score > highest_score:
                highest_score = score
                best_category = cat

        return best_category, scores

    def _assess_risk(
        self,
        indicators: List[DetectedIndicator],
        dominant_category: Optional[str],
        category_scores: Dict[str, float]
    ) -> Tuple[str, str]:
        """
        Determine explainable risk tier (low, needs_verification, high).
        """
        if not indicators:
            return "low", self.RISK_LABELS["low"]

        num_strong = sum(1 for ind in indicators if ind.definition.strength == "strong")
        num_medium = sum(1 for ind in indicators if ind.definition.strength == "medium")
        total_score = sum(self.STRENGTH_WEIGHTS.get(ind.definition.strength, 1.0) for ind in indicators)

        # Criteria for HIGH risk (multiple converging signals or strong indicator convergence)
        if (
            num_strong >= 2
            or (num_strong >= 1 and num_medium >= 1)
            or (num_strong >= 1 and dominant_category and category_scores.get(dominant_category, 0) >= 3.0)
            or (num_medium >= 2 and dominant_category and category_scores.get(dominant_category, 0) >= 3.0)
            or (num_medium >= 3)
            or (total_score >= 3.5)
        ):
            return "high", self.RISK_LABELS["high"]

        # Criteria for LOW risk: only 1 weak signal with no specific category evidence
        if num_strong == 0 and num_medium == 0 and total_score <= 0.5:
            return "low", self.RISK_LABELS["low"]

        # Default fallback for single or moderate indicators: NEEDS_VERIFICATION
        return "needs_verification", self.RISK_LABELS["needs_verification"]


# Singleton instance for dependency injection
_detector_instance = RulesBaselineDetector()


def get_detector_service() -> RulesBaselineDetector:
    """FastAPI route dependency provider."""
    return _detector_instance
