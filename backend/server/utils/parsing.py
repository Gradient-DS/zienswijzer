"""Parse documents into markdown."""

import typing as t
import logging

from pathlib import Path
from langchain_pymupdf4llm import PyMuPDF4LLMParser
from langchain_core.documents import Document as LCDocument
from langchain_core.document_loaders import Blob
from server import db

logger = logging.getLogger(__name__)


class PDFParser:
    """Parse PDF documents into markdown format."""

    def __init__(self):
        self.parser = PyMuPDF4LLMParser(mode="page")  # parse into a separate LCDocument per page

    def load_pdf(self, pdf_path: t.Union[str, Path]) -> Blob:
        """
        Load a PDF from a file path and return as a Blob.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Blob: Langchain Blob object containing the PDF

        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            ValueError: If the file is not a PDF
        """
        path = Path(pdf_path)

        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError(f"File is not a PDF: {path}")

        return Blob.from_path(str(path))

    def parse(self, blob: Blob, verbose: bool = False) -> t.List[LCDocument]:
        """
        Parse a single PDF Blob into a list of LCDocuments (one per page).

        Args:
            blob: A Blob object wrapping a PDF file.
            verbose: Whether to log progress.

        Returns:
            List[LCDocument]: List of documents, one per page.
        """
        if verbose:
            logger.info(f"Parsing PDF: {blob.source}")

        page_docs: t.List[LCDocument] = list(self.parser.lazy_parse(blob))
        return page_docs

    def parse_batch(self, blobs: t.List[Blob], verbose: bool = False) -> t.Dict[str, t.List[LCDocument]]:
        """
        Parse a list of PDF Blobs into documents.

        Args:
            blobs: List of Blob objects.
            verbose: Whether to log progress.

        Returns:
            Dict mapping PDF source paths to their parsed documents.
        """
        results: t.Dict[str, t.List[LCDocument]] = {}

        total = len(blobs)
        for idx, blob in enumerate(blobs, start=1):
            if verbose:
                print(f"Parsing PDF {idx}/{total}: {blob.source}")

            docs = self.parse(blob, verbose=verbose)
            if docs:
                results[blob.source] = docs

        return results


class EntityExtractor:
    """Extract entities from a document."""

    def __init__(self):
        return "TEST"


def main(doc_id: str):
    document = db.get_document_by_id(doc_id)
    if not document:
        raise ValueError(f"Document not found: {doc_id}")
<<<<<<< HEAD

    # Resolve file path relative to server directory
    server_dir = Path(__file__).parent.parent
    INPUT_PATH = server_dir / document["file_path"]

    logger.info(f"Parsing document: {INPUT_PATH}")
=======
    
    INPUT_PATH = Path(__file__).parent.parent / document['file_path']
    
    logger.info(f"Parsing document")
>>>>>>> origin/main
    parser = PDFParser()
    blob = parser.load_pdf(INPUT_PATH)
    results = parser.parse(blob=blob, verbose=True)

    document["title"] = results[0].metadata["title"]
    document["page_count"] = results[0].metadata["total_pages"]
    document["keywords"] = results[0].metadata["keywords"]
    document["author"] = results[0].metadata["author"]
    document["parse_status"] = "parsed"

    db.update_document(doc_id, document)

    logger.info(f"Document parsed, extracting entities")

    # entity_extractor = EntityExtractor()
    # entity_extractor.extract(results)


if __name__ == "__main__":
    # Example usage
    INPUT_DIR = Path("data/pdfs")
    INPUT_FILE = Path("data/document.pdf")

    # Parse the PDFs
    parser = PDFParser()
    blob = parser.load_pdf(INPUT_FILE)
    print(blob)
    results = parser.parse(blob=blob, verbose=True)
    print(results[0].metadata)
