"""
Reply classification API for sentiment analysis.

This module provides endpoints for classifying text responses to determine
whether stakeholders agree to publish or object to publication.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# Router for classification endpoints
classification_router = APIRouter(prefix="/classification", tags=["classification"])


# Pydantic Models
class ClassificationRequest(BaseModel):
    """Request model for text classification"""

    text: str


class ClassificationResult(BaseModel):
    """Result model for text classification"""

    text: str
    classification: str
    confidence: float
    all_scores: dict[str, float]


# Initialize the classification model (lazy loading)
_classifier = None
CANDIDATE_LABELS = ["agrees to publish", "objects to publication"]


def get_classifier():
    """Get or initialize the classification model (lazy loading)"""
    global _classifier
    if _classifier is None:
        logger.info("Initializing zero-shot classification model...")
        try:
            from transformers import pipeline

            _classifier = pipeline("zero-shot-classification", model="cross-encoder/nli-deberta-v3-small")
            logger.info("Classification model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize classification model: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize classification model: {str(e)}")
    return _classifier


@classification_router.post("/classify", response_model=ClassificationResult)
def classify_text(request: ClassificationRequest):
    """
    Classify text to determine sentiment regarding publication.

    This endpoint uses zero-shot classification to determine whether a text
    expresses agreement or objection to publication. It's particularly useful
    for analyzing stakeholder responses in WOO (Wet open overheid) requests.

    Args:
        request: ClassificationRequest with text to classify

    Returns:
        ClassificationResult with classification label, confidence score,
        and scores for all candidate labels

    Example:
        POST /classification/classify
        {
            "text": "Bedankt voor jullie bericht. Ik heb graag liever niet dat jullie dit publiceren."
        }

        Response:
        {
            "text": "Bedankt voor jullie bericht...",
            "classification": "objects to publication",
            "confidence": 0.89,
            "all_scores": {
                "objects to publication": 0.89,
                "agrees to publish": 0.11
            }
        }
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        classifier = get_classifier()

        # Perform classification
        result = classifier(request.text, candidate_labels=CANDIDATE_LABELS)

        # Extract results
        top_label = result["labels"][0]
        top_score = result["scores"][0]

        # Create score dictionary for all labels
        all_scores = {label: score for label, score in zip(result["labels"], result["scores"])}

        logger.info(f"Classified text (length={len(request.text)}): {top_label} ({top_score:.2f})")

        return ClassificationResult(
            text=request.text, classification=top_label, confidence=top_score, all_scores=all_scores
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during classification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@classification_router.get("/health")
def health_check():
    """
    Check if the classification service is ready.

    Returns:
        Status information about the classification service
    """
    try:
        # Try to get/initialize the classifier
        classifier = get_classifier()
        return {"status": "ready", "model": "cross-encoder/nli-deberta-v3-small", "candidate_labels": CANDIDATE_LABELS}
    except Exception as e:
        return {"status": "error", "error": str(e)}
