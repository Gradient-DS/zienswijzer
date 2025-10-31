"""
Verification endpoints for chunk stakeholder mentions.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import logging
from server import db

logger = logging.getLogger(__name__)

verification_router = APIRouter(prefix="/verification", tags=["verification"])


class VerifyMentionRequest(BaseModel):
    """Request to verify a single mention"""

    verified: bool = True


class BulkVerifyRequest(BaseModel):
    """Request to bulk verify mentions"""

    stakeholder_id: str
    case_id: str
    filter_type: str  # "high" (>=0.9), "medium" (>=0.7), "all"
    verified: bool = True


class VerifyMentionResponse(BaseModel):
    """Response after verifying a mention"""

    success: bool
    message: str
    mention_id: str
    verified: bool


class BulkVerifyResponse(BaseModel):
    """Response after bulk verification"""

    success: bool
    message: str
    verified_count: int


@verification_router.post("/mention/{mention_id}", response_model=VerifyMentionResponse)
def verify_mention(mention_id: str, request: VerifyMentionRequest):
    """
    Verify or unverify a single chunk stakeholder mention.

    Args:
        mention_id: ChunkStakeholder ID
        request: Verification request with verified flag

    Returns:
        Success status and updated mention info
    """
    try:
        # Get the mention to verify it exists
        mention = db.get_chunk_stakeholders_by_id(mention_id)
        if not mention:
            raise HTTPException(status_code=404, detail="Mention not found")

        # Update verification status
        db.update_chunk_stakeholder_verified(mention_id, request.verified)

        logger.info(f"Updated verification status for mention {mention_id}: {request.verified}")

        return VerifyMentionResponse(
            success=True,
            message=f"Mention {'verified' if request.verified else 'unverified'} successfully",
            mention_id=mention_id,
            verified=request.verified,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify mention {mention_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to verify mention: {str(e)}")


@verification_router.post("/bulk", response_model=BulkVerifyResponse)
def bulk_verify_mentions(request: BulkVerifyRequest):
    """
    Bulk verify or unverify mentions for a stakeholder in a case.

    Args:
        request: Bulk verification request with filter criteria

    Returns:
        Success status and count of verified mentions
    """
    try:
        # Get the case to find its documents
        case = db.get_case_by_id(request.case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        document_ids = case.get("document_ids", [])
        if not document_ids:
            raise HTTPException(status_code=404, detail="No documents found for case")

        verified_count = 0

        # Process each document
        for doc_id in document_ids:
            chunks = db.get_chunks_by_document(doc_id)

            for chunk in chunks:
                chunk_stakeholders = db.get_chunk_stakeholders(chunk["id"])

                for cs in chunk_stakeholders:
                    # Filter by stakeholder
                    if cs["stakeholder_id"] != request.stakeholder_id:
                        continue

                    # Apply confidence filter
                    confidence = cs.get("confidence", 0.0)
                    if request.filter_type == "high" and confidence < 0.9:
                        continue
                    if request.filter_type == "medium" and confidence < 0.7:
                        continue
                    # "all" includes everything regardless of confidence

                    # Update verification status
                    db.update_chunk_stakeholder_verified(cs["id"], request.verified)
                    verified_count += 1

        logger.info(
            f"Bulk verified {verified_count} mentions for stakeholder {request.stakeholder_id} in case {request.case_id}"
        )

        return BulkVerifyResponse(
            success=True,
            message=f"Successfully {'verified' if request.verified else 'unverified'} {verified_count} mentions",
            verified_count=verified_count,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to bulk verify mentions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk verify mentions: {str(e)}")
