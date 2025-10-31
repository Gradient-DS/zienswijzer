"""
PDF generation endpoints for stakeholders.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import logging
from server import db

logger = logging.getLogger(__name__)

pdf_router = APIRouter(prefix="/pdf", tags=["pdf"])


class GeneratePDFRequest(BaseModel):
    """Request to generate a PDF for a stakeholder"""

    case_id: str
    content_type: str  # "full_documents", "pages_only", or "chunks_only"


@pdf_router.post("/stakeholders/{stakeholder_id}/generate")
def generate_stakeholder_pdf(stakeholder_id: str, request: GeneratePDFRequest):
    """
    Generate a PDF for a stakeholder based on their mentions.

    Args:
        stakeholder_id: Stakeholder identifier
        request: PDF generation request with case_id and content_type

    Returns:
        PDF file response
    """
    try:
        # Verify stakeholder exists
        stakeholder = db.get_stakeholder_by_id(stakeholder_id)
        if not stakeholder:
            raise HTTPException(status_code=404, detail="Stakeholder not found")

        # Get case and documents
        case = db.get_case_by_id(request.case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        document_ids = case.get("document_ids", [])
        if not document_ids:
            raise HTTPException(status_code=404, detail="No documents found for case")

        # Collect relevant chunks and pages
        relevant_chunks = []
        relevant_pages_by_doc = {}  # Map document_id -> set of page numbers

        for doc_id in document_ids:
            chunks = db.get_chunks_by_document(doc_id)
            doc_pages = set()

            for chunk in chunks:
                chunk_stakeholders = db.get_chunk_stakeholders(chunk["id"])

                # Check if this chunk has a mention for our stakeholder
                has_stakeholder_mention = any(cs["stakeholder_id"] == stakeholder_id for cs in chunk_stakeholders)

                if has_stakeholder_mention:
                    relevant_chunks.append(
                        {
                            "chunk": chunk,
                            "document_id": doc_id,
                        }
                    )
                    doc_pages.add(chunk["page"])

            if doc_pages:
                relevant_pages_by_doc[doc_id] = doc_pages

        if not relevant_chunks:
            raise HTTPException(status_code=404, detail="No mentions found for this stakeholder in the case documents")

        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise HTTPException(
                status_code=500, detail="PDF generation requires PyMuPDF. It should be installed already."
            )

        # Create output PDF
        output_pdf = fitz.open()  # Create new PDF

        if request.content_type == "full_documents":
            # Include all documents
            for doc_id in document_ids:
                doc = db.get_document_by_id(doc_id)
                if doc and doc.get("file_path"):
                    file_path = Path(doc["file_path"])
                    if file_path.exists() and file_path.suffix.lower() == ".pdf":
                        source_pdf = fitz.open(str(file_path))
                        output_pdf.insert_pdf(source_pdf)
                        source_pdf.close()

        elif request.content_type == "pages_only":
            # Extract only relevant pages
            for doc_id, pages in relevant_pages_by_doc.items():
                doc = db.get_document_by_id(doc_id)
                if doc and doc.get("file_path"):
                    file_path = Path(doc["file_path"])
                    if file_path.exists() and file_path.suffix.lower() == ".pdf":
                        source_pdf = fitz.open(str(file_path))
                        # Insert specific pages (0-indexed in PyMuPDF)
                        for page_num in sorted(pages):
                            # PyMuPDF uses 0-indexed pages, but our chunks use 1-indexed
                            output_pdf.insert_pdf(source_pdf, from_page=page_num - 1, to_page=page_num - 1)
                        source_pdf.close()

        else:  # chunks_only
            # Use PyMuPDF to create a text-based PDF with chunk excerpts
            # Create a blank page and add text
            page = output_pdf.new_page(width=595, height=842)  # A4 size
            text_content = f"Documenten voor {stakeholder['name']}\n\n"
            text_content += "Tekstfragmenten met vermeldingen:\n\n"

            for item in relevant_chunks:
                chunk = item["chunk"]
                doc = db.get_document_by_id(item["document_id"])
                doc_title = doc["title"] if doc else "Document"
                text_content += f"{doc_title} - Pagina {chunk['page']}\n"
                text_content += f"{chunk['context'][:300]}...\n\n"

            # Insert text on page (PyMuPDF will handle text wrapping automatically)
            text_rect = fitz.Rect(50, 50, 545, 792)  # Margins
            page.insert_text(
                text_rect.tl,  # Top-left point
                text_content,
                fontsize=11,
                fontname="helv",
            )

        # Convert output PDF to bytes
        pdf_bytes = output_pdf.tobytes()
        output_pdf.close()

        # Determine filename
        filename_type = {
            "full_documents": "volledige_documenten",
            "pages_only": "paginas",
            "chunks_only": "chunks",
        }.get(request.content_type, "document")

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="stakeholder_{stakeholder_id}_{filename_type}.pdf"'},
        )

    except HTTPException:
        raise
    except ImportError as e:
        # PyMuPDF not installed
        logger.error(f"PyMuPDF import failed: {e}")
        raise HTTPException(status_code=500, detail="PDF generation requires PyMuPDF. It should be installed already.")
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")


# Export router for integration with main app
__all__ = ["pdf_router"]
