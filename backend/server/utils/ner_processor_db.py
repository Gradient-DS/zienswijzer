"""
Markdown NER Processor with Database Integration

This module provides a class to process markdown files, perform Named Entity Recognition,
and populate the database using proper database functions from db.database.
"""

import uuid
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Tuple, Optional, Set
import sys

# Add parent directory to path for imports
server_dir = Path(__file__).parent.parent
sys.path.insert(0, str(server_dir))

from db.database import (
    init_db,
    create_stakeholder,
    get_stakeholders,
    get_stakeholder_by_id,
    create_chunk,
    create_chunk_stakeholder,
    get_chunk_stakeholders,
)
from utils.ner import extract_entities_from_text


class MarkdownNERProcessorDB:
    """
    Processes markdown files, performs NER, and populates the database using
    proper database functions following database schema requirements.
    """

    def __init__(
        self,
        markdown_path: str,
        document_id: str,
        entity_types: Optional[List[str]] = None,
        stakeholder_types_to_save: Optional[List[str]] = None,
        min_confidence: float = 0.5,
        model_type: str = "xlm-roberta",
        model_name: str = "Davlan/xlm-roberta-base-ner-hrl",
        verbose: bool = True,
        pdf_path: Optional[str] = None,
    ):
        """
        Initialize the Markdown NER Processor with database integration.

        Args:
            markdown_path: Path to the markdown file to process
            document_id: ID of the document in the database
            entity_types: Entity types to extract during NER (None = all types)
            stakeholder_types_to_save: Stakeholder types to save ("person", "organization", "location", or None = all)
            min_confidence: Minimum confidence threshold for NER entities
            model_type: NER model type ("spacy", "bert", "xlm-roberta", "robbert", "flair")
            model_name: Specific model name
            verbose: Whether to print progress messages
            pdf_path: Optional path to corresponding PDF file (for extracting bounding boxes)
        """
        self.markdown_path = Path(markdown_path)
        self.document_id = document_id
        self.entity_types = entity_types
        self.stakeholder_types_to_save = stakeholder_types_to_save
        self.min_confidence = min_confidence
        self.model_type = model_type
        self.model_name = model_name
        self.verbose = verbose
        self.pdf_path = pdf_path
        self.pdf_doc = None

        self.full_text = None
        self.pdf_text = None
        self.pdf_pages_text = []
        self.entities = []
        self.stakeholder_ids = {}  # Cache: (name, type) -> stakeholder_id

        # Open PDF if provided
        if pdf_path and Path(pdf_path).exists():
            try:
                import fitz  # PyMuPDF

                self.pdf_doc = fitz.open(pdf_path)
                if self.verbose:
                    self._print(f"Opened PDF: {pdf_path} ({len(self.pdf_doc)} pages)")
                self._extract_pdf_text()
            except ImportError:
                if self.verbose:
                    self._print("Warning: PyMuPDF not installed. Install with: pip install PyMuPDF")
            except Exception as e:
                if self.verbose:
                    self._print(f"Warning: Could not open PDF {pdf_path}: {e}")

    def _print(self, message: str):
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(message)

    def _extract_pdf_text(self) -> None:
        """Extract text from PDF and store it for chunking, along with character-to-bbox mapping."""
        if not hasattr(self, "pdf_doc") or self.pdf_doc is None:
            return

        try:
            import fitz  # PyMuPDF

            self.pdf_text = ""
            self.pdf_pages_text = []
            # Store mapping from character position to bounding box
            self.char_to_bbox = []  # List of (char_index, bbox, page_num)

            char_offset = 0
            for page_num in range(len(self.pdf_doc)):
                page = self.pdf_doc[page_num]

                # Get text with positions for better matching
                text_dict = page.get_text("dict")
                page_text_from_dict = ""

                # Extract text with character positions and bounding boxes
                for block in text_dict.get("blocks", []):
                    if "lines" not in block:
                        continue

                    for line in block["lines"]:
                        for span in line["spans"]:
                            span_text = span.get("text", "")
                            span_bbox = span.get("bbox", [])

                            if len(span_bbox) == 4:
                                # Store bbox for the span (more efficient than per-character)
                                span_start = char_offset + len(page_text_from_dict)
                                span_end = span_start + len(span_text)

                                self.char_to_bbox.append(
                                    {
                                        "char_index_start": span_start,
                                        "char_index_end": span_end,
                                        "bbox": {
                                            "x": span_bbox[0],
                                            "y": span_bbox[1],
                                            "width": span_bbox[2] - span_bbox[0],
                                            "height": span_bbox[3] - span_bbox[1],
                                        },
                                        "page_num": page_num + 1,
                                        "text": span_text,
                                    }
                                )

                            page_text_from_dict += span_text

                        page_text_from_dict += "\n"

                    page_text_from_dict += "\n"

                # Use the same text from dict extraction for consistency
                self.pdf_text += page_text_from_dict

                char_offset += len(page_text_from_dict)

                self.pdf_pages_text.append(
                    {
                        "page_num": page_num + 1,  # 1-based for frontend
                        "text": page_text_from_dict,
                        "page": page,
                        "pdf_page_index": page_num,  # 0-based for PyMuPDF
                    }
                )

            if self.verbose:
                self._print(f"Extracted {len(self.pdf_text)} characters from PDF ({len(self.pdf_pages_text)} pages)")
                self._print(f"Created {len(self.char_to_bbox)} character-to-bbox mappings")
        except Exception as e:
            if self.verbose:
                self._print(f"Error extracting PDF text: {e}")

    def load_markdown(self) -> str:
        """Load and return the markdown file content."""
        if not self.markdown_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {self.markdown_path}")

        with open(self.markdown_path, "r", encoding="utf-8") as f:
            self.full_text = f.read()

        self._print(f"Loaded {len(self.full_text)} characters from {self.markdown_path}")

        if self.pdf_text:
            self._print(
                f"Note: NER will use markdown text, but chunking will use PDF text ({len(self.pdf_text)} chars)"
            )

        return self.full_text

    def perform_ner(self) -> List[Dict]:
        """
        Perform Named Entity Recognition on the markdown text.

        Returns:
            List of entity dictionaries with 'text', 'label', 'start', 'end', 'confidence'
        """
        if not self.full_text:
            raise ValueError("Must load markdown file first (call load_markdown())")

        self._print("=" * 60)
        self._print("Performing Named Entity Recognition...")
        self._print(f"Model type: {self.model_type}, Model name: {self.model_name}")

        try:
            entities = extract_entities_from_text(
                self.full_text,
                entity_types=self.entity_types,
                min_confidence=self.min_confidence,
                model_type=self.model_type,
                model_name=self.model_name,
            )

            # Filter out very short entities and None values
            entities = [ent for ent in entities if ent is not None and len(ent.get("text", "").strip()) > 2]

            self.entities = entities
            self._print(f"Found {len(entities)} entities")

            return entities

        except Exception as e:
            self._print(f"Error during NER processing: {e}")
            if self.verbose:
                import traceback

                traceback.print_exc()
            raise

    @staticmethod
    def map_ner_label_to_stakeholder_type(label: str) -> str:
        """
        Map NER entity label to stakeholder type.

        PER/PERSON -> "person"
        ORG/ORGANIZATION -> "organization"
        LOC/LOCATION/GPE -> "location"
        Others -> lowercase of label
        """
        label_upper = label.upper()

        if label_upper in ["PER", "PERSON", "PERS"]:
            return "person"
        elif label_upper in ["ORG", "ORGANIZATION", "ORGANISATION"]:
            return "organization"
        elif label_upper in ["LOC", "LOCATION", "GPE", "GEO", "PLACE"]:
            return "location"
        else:
            return label.lower()

    def _get_stakeholder_id(self, name: str, stakeholder_type: str) -> Optional[str]:
        """
        Get stakeholder ID by name and type using database functions.
        Caches results for performance.
        """
        key = (name, stakeholder_type)
        if key in self.stakeholder_ids:
            return self.stakeholder_ids[key]

        # Use database function to get all stakeholders and find by name/type
        all_stakeholders = get_stakeholders()
        for stakeholder in all_stakeholders:
            if stakeholder["name"] == name and stakeholder.get("type") == stakeholder_type:
                self.stakeholder_ids[key] = stakeholder["id"]
                return stakeholder["id"]

        return None

    def _stakeholder_exists(self, name: str, stakeholder_type: str) -> bool:
        """Check if a stakeholder with this name and type already exists using database functions."""
        return self._get_stakeholder_id(name, stakeholder_type) is not None

    def _filter_entities_by_stakeholder_type(self) -> List[Dict]:
        """Filter entities by stakeholder types to save."""
        if self.stakeholder_types_to_save is None:
            return self.entities

        self._print(f"\nFiltering entities to only save: {self.stakeholder_types_to_save}")
        initial_count = len(self.entities)

        filtered = []
        for entity in self.entities:
            ner_label = entity.get("label", "")
            stakeholder_type = self.map_ner_label_to_stakeholder_type(ner_label)
            if stakeholder_type in self.stakeholder_types_to_save:
                filtered.append(entity)

        self._print(f"Filtered from {initial_count} to {len(filtered)} entities matching selected types")
        return filtered

    def _deduplicate_stakeholders(self, entities: List[Dict]) -> Dict[Tuple[str, str], Dict]:
        """
        Deduplicate entities by (name, type), keeping the one with highest confidence.

        Returns:
            Dictionary mapping (name, stakeholder_type) -> entity
        """
        unique_stakeholders = {}

        for entity in entities:
            name = entity.get("text", "").strip()
            if not name or len(name) < 2:
                continue

            ner_label = entity.get("label", "")
            stakeholder_type = self.map_ner_label_to_stakeholder_type(ner_label)
            key = (name, stakeholder_type)

            # Keep entity with highest confidence if duplicates exist
            if key not in unique_stakeholders:
                unique_stakeholders[key] = entity
            else:
                current_confidence = unique_stakeholders[key].get("confidence", 0.0)
                new_confidence = entity.get("confidence", 0.0)
                if new_confidence > current_confidence:
                    unique_stakeholders[key] = entity

        return unique_stakeholders

    def populate_stakeholders(self) -> Dict[str, int]:
        """
        Populate the Stakeholders table with entities found in the markdown file.
        Uses proper database functions and follows database schema requirements.

        Returns:
            Dictionary with 'created', 'skipped', 'total' counts
        """
        if not self.entities:
            self._print("No entities found.")
            return {"created": 0, "skipped": 0, "total": 0}

        # Initialize database
        self._print("\nInitializing database...")
        init_db()

        # Filter entities by stakeholder type
        filtered_entities = self._filter_entities_by_stakeholder_type()

        if not filtered_entities:
            self._print("No entities to save after filtering.")
            return {"created": 0, "skipped": 0, "total": 0}

        # Deduplicate stakeholders
        unique_stakeholders = self._deduplicate_stakeholders(filtered_entities)
        self._print(f"\nFound {len(unique_stakeholders)} unique stakeholders (after deduplication)")

        # Create stakeholders in database
        now = datetime.now().isoformat() + "Z"
        created_count = 0
        skipped_count = 0

        self._print("\nPopulating Stakeholders table...")
        for (name, stakeholder_type), entity in unique_stakeholders.items():
            # Check if already exists using database functions
            if self._stakeholder_exists(name, stakeholder_type):
                self._print(f"  [SKIP] {name} ({stakeholder_type}) - already exists")
                skipped_count += 1
                # Cache the existing stakeholder ID
                self.stakeholder_ids[(name, stakeholder_type)] = self._get_stakeholder_id(name, stakeholder_type)
                continue

            # Create stakeholder with proper database schema fields
            stakeholder_id = f"stakeholder_{uuid.uuid4().hex[:16]}"
            stakeholder = {
                "id": stakeholder_id,
                "type": stakeholder_type,
                "name": name,
                "contact_info": None,  # No hardcoded contact info - can be updated later
                "publication_status": None,  # Required field, defaults to None
                "created_at": now,
                "updated_at": now,
            }

            try:
                create_stakeholder(stakeholder)
                self.stakeholder_ids[(name, stakeholder_type)] = stakeholder_id
                self._print(f"  [✓] Created: {name} ({stakeholder_type})")
                created_count += 1
            except Exception as e:
                self._print(f"  [✗] Error creating {name}: {e}")

        # Summary
        result = {"created": created_count, "skipped": skipped_count, "total": len(unique_stakeholders)}

        self._print_summary(result)
        return result

    def _split_text_into_chunks(self, text: str, chunk_size: int = 500) -> List[Dict]:
        """
        Split text into chunks (paragraph-based for markdown).
        Returns list of chunks with 'text', 'start', 'end' positions.
        """
        chunks = []

        # Split by double newlines (paragraphs)
        paragraphs = text.split("\n\n")

        current_pos = 0
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If paragraph is too long, split it further
            if len(para) > chunk_size:
                words = para.split()
                current_chunk_words = []
                chunk_start = current_pos

                for word in words:
                    current_chunk_words.append(word)
                    chunk_text = " ".join(current_chunk_words)

                    if len(chunk_text) >= chunk_size:
                        chunk_end = current_pos + len(chunk_text)
                        chunks.append({"text": chunk_text, "start": chunk_start, "end": chunk_end})
                        current_pos = chunk_end
                        current_chunk_words = []
                        chunk_start = chunk_end

                if current_chunk_words:
                    chunk_text = " ".join(current_chunk_words)
                    chunk_end = current_pos + len(chunk_text)
                    chunks.append({"text": chunk_text, "start": chunk_start, "end": chunk_end})
                    current_pos = chunk_end
            else:
                # Find paragraph in original text
                para_start = text.find(para, current_pos)
                if para_start == -1:
                    para_start = current_pos
                para_end = para_start + len(para)

                chunks.append({"text": para, "start": para_start, "end": para_end})
                current_pos = para_end

        return chunks

    def _get_chunk_bbox_from_pdf(
        self, chunk_text: str, chunk_start: int, chunk_end: int, page: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Get bounding box for a chunk from PDF using character positions.

        Uses the character-to-bbox mapping created during PDF text extraction.
        """
        if not hasattr(self, "pdf_doc") or self.pdf_doc is None:
            return None

        if not chunk_text or len(chunk_text.strip()) < 5:
            return None

        # Method 1: Use character position mapping if available
        if hasattr(self, "char_to_bbox") and self.char_to_bbox:
            # Find bboxes for spans that overlap with this chunk's range
            chunk_bboxes = []
            for entry in self.char_to_bbox:
                entry_start = entry.get("char_index_start", entry.get("char_index", 0))
                entry_end = entry.get("char_index_end", entry_start + 1)

                # Check if span overlaps with chunk
                if entry_start < chunk_end and entry_end > chunk_start and (page is None or entry["page_num"] == page):
                    chunk_bboxes.append(entry["bbox"])

            if chunk_bboxes:
                # Calculate bounding box encompassing all spans in chunk
                min_x = min(bbox["x"] for bbox in chunk_bboxes)
                min_y = min(bbox["y"] for bbox in chunk_bboxes)
                max_x = max(bbox["x"] + bbox["width"] for bbox in chunk_bboxes)
                max_y = max(bbox["y"] + bbox["height"] for bbox in chunk_bboxes)

                return {
                    "x": min_x,
                    "y": min_y,
                    "width": max_x - min_x,
                    "height": max_y - min_y,
                }

        # Method 2: Fallback to direct PDF search
        try:
            import fitz  # PyMuPDF
        except ImportError:
            return None

        # Normalize chunk text for matching
        chunk_text_normalized = " ".join(chunk_text.strip().split())

        # Determine which pages to search
        pages_to_search = []
        if page is not None:
            pdf_page_index = page - 1 if page > 0 else 0
            if 0 <= pdf_page_index < len(self.pdf_doc):
                pages_to_search = [pdf_page_index]
            else:
                return None
        else:
            pages_to_search = list(range(len(self.pdf_doc)))

        for page_num in pages_to_search:
            pdf_page = self.pdf_doc[page_num]

            # Search for chunk text (try first 100 chars)
            search_text = chunk_text_normalized[:100]
            if len(search_text) >= 10:
                text_instances = pdf_page.search_for(search_text)
                if text_instances:
                    rect = text_instances[0]
                    return {
                        "x": rect.x0,
                        "y": rect.y0,
                        "width": max(rect.x1 - rect.x0, 300.0),
                        "height": max(rect.y1 - rect.y0, 50.0),
                    }

        return None

    def _bboxes_overlap(self, bbox1: Dict, bbox2: Dict, overlap_threshold: float = 0.5) -> bool:
        """
        Check if two bounding boxes overlap significantly.

        Args:
            bbox1: First bounding box dict with x, y, width, height
            bbox2: Second bounding box dict with x, y, width, height
            overlap_threshold: Minimum overlap ratio (0.0-1.0) to consider as overlap

        Returns:
            True if bounding boxes overlap significantly
        """
        # Calculate intersection area
        x1_left = bbox1["x"]
        x1_right = bbox1["x"] + bbox1["width"]
        y1_top = bbox1["y"]
        y1_bottom = bbox1["y"] + bbox1["height"]

        x2_left = bbox2["x"]
        x2_right = bbox2["x"] + bbox2["width"]
        y2_top = bbox2["y"]
        y2_bottom = bbox2["y"] + bbox2["height"]

        # Calculate intersection
        intersect_left = max(x1_left, x2_left)
        intersect_right = min(x1_right, x2_right)
        intersect_top = max(y1_top, y2_top)
        intersect_bottom = min(y1_bottom, y2_bottom)

        if intersect_right <= intersect_left or intersect_bottom <= intersect_top:
            return False  # No intersection

        intersect_area = (intersect_right - intersect_left) * (intersect_bottom - intersect_top)
        bbox1_area = bbox1["width"] * bbox1["height"]
        bbox2_area = bbox2["width"] * bbox2["height"]

        # Check if overlap is significant (overlap_threshold of smaller box)
        min_area = min(bbox1_area, bbox2_area)
        if min_area == 0:
            return False

        overlap_ratio = intersect_area / min_area
        return overlap_ratio >= overlap_threshold

    def _create_chunk(self, document_id: str, chunk_data: Dict, page: int = 0) -> str:
        """
        Create a chunk in the database using database functions.
        Returns chunk_id.
        """
        chunk_id = f"chunk_{uuid.uuid4().hex[:16]}"

        # Try to get bounding box from PDF if available (pass page number)
        chunk_bbox = self._get_chunk_bbox_from_pdf(
            chunk_data["text"], chunk_data.get("start", 0), chunk_data.get("end", 0), page=page
        )

        # If no PDF bbox found, use unique placeholder based on chunk position
        if chunk_bbox is None:
            # Use hash of chunk text and page to generate unique but consistent coordinates
            chunk_hash = hashlib.md5((chunk_data["text"] + str(page)).encode()).hexdigest()
            # Use hash to generate unique but reasonable coordinates
            x_offset = (int(chunk_hash[:4], 16) % 400) + 50  # 50-450
            y_offset = (int(chunk_hash[4:8], 16) % 600) + 50  # 50-650
            chunk_bbox = {
                "x": float(x_offset),
                "y": float(y_offset),  # Page-relative coordinates (no offset)
                "width": 400.0,
                "height": 100.0,
            }

        # Create chunk record using database function
        chunk_record = {
            "id": chunk_id,
            "document_id": document_id,
            "page": page,
            "context": chunk_data["text"],
            "bbox": chunk_bbox,  # Will be JSON encoded by create_chunk
            "created_at": datetime.now().isoformat() + "Z",
        }

        create_chunk(chunk_record)

        return chunk_id

    def _get_entity_bbox_from_pdf(
        self, mention_text: str, page: int, chunk_text: Optional[str] = None, chunk_start: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Get bounding box for an entity mention from PDF using PyMuPDF.

        This finds the exact bounding box of the entity text in the PDF.
        If chunk_text and chunk_start are provided, it searches within that chunk's region first.
        """
        if not hasattr(self, "pdf_doc") or self.pdf_doc is None:
            return None

        try:
            import fitz  # PyMuPDF
        except ImportError:
            return None

        if not mention_text or len(mention_text.strip()) < 2:
            return None

        try:
            # Convert 1-based page number to 0-based index for PyMuPDF
            pdf_page_index = page - 1 if page > 0 else 0
            if pdf_page_index >= len(self.pdf_doc) or pdf_page_index < 0:
                return None

            pdf_page = self.pdf_doc[pdf_page_index]

            # Clean and normalize mention text
            mention_text_clean = mention_text.strip()

            # Method 1: Search for text in spans (most accurate for exact matches)
            text_dict = pdf_page.get_text("dict")

            # If we have chunk context, try to find the mention within that chunk first
            if chunk_text and chunk_start is not None:
                # Find the chunk's bounding box area
                chunk_bbox = self._get_chunk_bbox_from_pdf(chunk_text, chunk_start, chunk_start + len(chunk_text), page)

            for block in text_dict.get("blocks", []):
                if "lines" not in block:
                    continue

                for line in block["lines"]:
                    for span in line["spans"]:
                        span_text = span.get("text", "").strip()

                        # Check if mention text is in this span (case-insensitive, lenient matching)
                        span_text_normalized = span_text.replace(" ", "").lower()
                        mention_normalized = mention_text_clean.replace(" ", "").lower()

                        if (
                            mention_text_clean.lower() in span_text.lower()
                            or span_text.lower() in mention_text_clean.lower()
                            or mention_normalized == span_text_normalized
                            or mention_normalized in span_text_normalized
                            or span_text_normalized in mention_normalized
                        ):
                            span_bbox = span.get("bbox", [])
                            if len(span_bbox) == 4:
                                # If chunk bbox exists, verify this span is within it
                                if chunk_text and chunk_start is not None and chunk_bbox:
                                    span_center_x = (span_bbox[0] + span_bbox[2]) / 2
                                    span_center_y = (span_bbox[1] + span_bbox[3]) / 2

                                    if not (
                                        chunk_bbox["x"] <= span_center_x <= chunk_bbox["x"] + chunk_bbox["width"]
                                        and chunk_bbox["y"] <= span_center_y <= chunk_bbox["y"] + chunk_bbox["height"]
                                    ):
                                        continue  # Skip if outside chunk area

                                return {
                                    "x": span_bbox[0],
                                    "y": span_bbox[1],
                                    "width": max(span_bbox[2] - span_bbox[0], 50.0),
                                    "height": max(span_bbox[3] - span_bbox[1], 10.0),
                                    "page": page,
                                }

            # Method 2: Fallback to direct page search
            mention_variants = [
                mention_text_clean,
                mention_text_clean.replace(" ", ""),
                " ".join(mention_text_clean.split()),
            ]

            for variant in mention_variants:
                if len(variant) >= 2:
                    text_instances = pdf_page.search_for(variant)
                    if text_instances:
                        rect = text_instances[0]
                        return {
                            "x": rect.x0,
                            "y": rect.y0,
                            "width": max(rect.x1 - rect.x0, 50.0),
                            "height": max(rect.y1 - rect.y0, 10.0),
                            "page": page,
                        }

        except Exception as e:
            if hasattr(self, "verbose") and self.verbose:
                self._print(f"  Warning: Error getting entity bbox: {e}")

        return None

    def _create_chunk_stakeholder(
        self,
        chunk_id: str,
        stakeholder_id: str,
        entity: Dict,
        mention_text: str,
        page: int = 0,
        existing_mentions: Optional[List[Dict]] = None,
        chunk_text: Optional[str] = None,
        chunk_start: Optional[int] = None,
    ) -> bool:
        """
        Create a ChunkStakeholder record using database functions.
        Checks for overlapping bounding boxes to prevent duplicates.

        Args:
            chunk_id: ID of the chunk containing this entity mention
            stakeholder_id: ID of the stakeholder
            entity: Entity dictionary with 'confidence', 'start', 'end', etc.
            mention_text: The actual text of the entity as it appears in the chunk
            page: Page number where the chunk/entity is located
            existing_mentions: List of existing mentions for this chunk (to check overlaps)

        Returns:
            True if created, False if skipped due to overlap
        """
        # Try to get bounding box from PDF if available (pass chunk context for better matching)
        mention_bbox = self._get_entity_bbox_from_pdf(mention_text, page, chunk_text, chunk_start)

        # If no PDF bbox found, use unique placeholder based on mention text and position
        if mention_bbox is None:
            # Use hash of mention text and chunk_id to generate unique but consistent coordinates
            mention_hash = hashlib.md5((mention_text + chunk_id).encode()).hexdigest()
            # Use hash to generate unique but reasonable coordinates
            x_offset = (int(mention_hash[:4], 16) % 400) + 100  # 100-500
            y_offset = (int(mention_hash[4:8], 16) % 600) + 100  # 100-700
            mention_bbox = {
                "x": float(x_offset),
                "y": float(y_offset),  # Page-relative coordinates (no offset)
                "width": max(len(mention_text) * 8.0, 80.0),  # Width based on text length
                "height": 20.0,
                "page": page,
            }

        # Check for overlapping bounding boxes with existing mentions
        if existing_mentions:
            for existing in existing_mentions:
                existing_bbox = existing.get("mention_bbox", {})
                if isinstance(existing_bbox, str):
                    import json

                    existing_bbox = json.loads(existing_bbox)

                # Check if same stakeholder and overlapping bbox (same entity mention)
                if existing.get("stakeholder_id") == stakeholder_id and self._bboxes_overlap(
                    mention_bbox, existing_bbox, overlap_threshold=0.5
                ):
                    if self.verbose:
                        self._print(
                            f"  [SKIP] Overlapping mention for '{mention_text}' at page {page} (already exists)"
                        )
                    return False  # Skip duplicate

        # Get confidence from entity dict
        entity_confidence = entity.get("confidence", 0.5)
        if isinstance(entity_confidence, bytes):
            try:
                entity_confidence = float(entity_confidence.decode("utf-8"))
            except:
                entity_confidence = 0.5
        elif entity_confidence is None:
            entity_confidence = 0.5
        else:
            entity_confidence = float(entity_confidence)

        # Create chunk-stakeholder record using database function
        cs_id = f"cs_{uuid.uuid4().hex[:16]}"
        chunk_stakeholder_record = {
            "id": cs_id,
            "chunk_id": chunk_id,
            "stakeholder_id": stakeholder_id,
            "confidence": entity_confidence,
            "mention_text": mention_text,
            "mention_bbox": mention_bbox,  # Will be JSON encoded by create_chunk_stakeholder
            "verified": False,  # verified = False by default
            "created_at": datetime.now().isoformat() + "Z",
        }

        create_chunk_stakeholder(chunk_stakeholder_record)
        return True

    def populate_chunks_and_entities(self) -> Dict[str, int]:
        """
        Create chunks from text and populate ChunkStakeholders table using database functions.
        Prevents overlapping bounding boxes for the same entity.

        Returns:
            Dictionary with 'chunks_created', 'chunk_stakeholders_created' counts
        """
        if not self.entities:
            raise ValueError("No entities found. Run perform_ner() first.")

        # Use PDF text for chunking if available, otherwise use markdown text
        text_to_chunk = self.pdf_text if self.pdf_text else self.full_text
        if not text_to_chunk:
            raise ValueError("No text loaded. Run load_markdown() first.")

        self._print("\n" + "=" * 60)
        self._print("CREATING CHUNKS AND CHUNK-STAKEHOLDER LINKS")
        self._print("=" * 60)

        # Split text into chunks
        if self.pdf_text:
            self._print("\nSplitting PDF text into chunks (using PDF for chunking)...")
            text_chunks = self._split_text_into_chunks(self.pdf_text)
            self._print(f"Created {len(text_chunks)} chunks from PDF text")
        else:
            self._print("\nSplitting markdown text into chunks...")
            text_chunks = self._split_text_into_chunks(self.full_text)
            self._print(f"Created {len(text_chunks)} chunks from markdown text")

        # Determine which page each chunk is on (for PDF)
        def get_chunk_page(chunk_start: int, chunk_end: int) -> int:
            """Determine which PDF page a chunk is on based on character position."""
            if not self.pdf_pages_text:
                return 1  # Return 1 for markdown documents

            current_pos = 0
            for page_info in self.pdf_pages_text:
                page_text_len = len(page_info["text"])
                if chunk_start < current_pos + page_text_len:
                    if self.verbose and False:  # Disable verbose debug per chunk
                        self._print(
                            f"    Chunk [{chunk_start}:{chunk_end}] → Page {page_info['page_num']} (page text range: [{current_pos}:{current_pos + page_text_len}])"
                        )
                    return page_info["page_num"]
                current_pos += page_text_len + 1  # +1 for newline

            # If we're here, chunk is beyond all pages - assign to last page
            last_page = self.pdf_pages_text[-1]["page_num"] if self.pdf_pages_text else 1
            if self.verbose:
                self._print(
                    f"    Warning: Chunk [{chunk_start}:{chunk_end}] exceeds PDF text length, assigning to last page {last_page}"
                )
            return last_page

        # Create chunk records in database
        chunk_records = {}  # chunk index -> {'chunk_id': ..., 'chunk': ..., 'page': ...}

        self._print("\nCreating chunks in database...")
        self._print(
            f"  PDF text available: {bool(self.pdf_text)}, Length: {len(self.pdf_text) if self.pdf_text else 0}"
        )
        self._print(
            f"  PDF pages text available: {bool(self.pdf_pages_text)}, Pages: {len(self.pdf_pages_text) if self.pdf_pages_text else 0}"
        )

        # Debug: show page text length distribution
        if self.pdf_pages_text:
            self._print(
                f"  Page text lengths: {[len(p['text']) for p in self.pdf_pages_text[:5]]}{'...' if len(self.pdf_pages_text) > 5 else ''}"
            )

        page_distribution = {}
        for i, chunk in enumerate(text_chunks):
            # Use PDF text for page detection if available
            if self.pdf_text and self.pdf_pages_text:
                chunk_page = get_chunk_page(chunk.get("start", 0), chunk.get("end", 0))
            else:
                chunk_page = 1

            chunk_id = self._create_chunk(self.document_id, chunk, page=chunk_page)
            chunk_records[i] = {"chunk_id": chunk_id, "chunk": chunk, "page": chunk_page}

            # Track page distribution
            page_distribution[chunk_page] = page_distribution.get(chunk_page, 0) + 1

            # Debug: show first 5 chunks
            if i < 5:
                self._print(f"    Chunk {i}: pos [{chunk.get('start', 0)}:{chunk.get('end', 0)}] → Page {chunk_page}")

        self._print(f"  ✓ Created {len(chunk_records)} chunks in database")
        self._print(f"  Page distribution: {page_distribution}")

        # Map ALL entity occurrences to chunks and create ChunkStakeholder records
        self._print("\nMapping entities to chunks and creating ChunkStakeholder records...")
        cs_count = 0
        skipped_count = 0
        overlap_skipped = 0

        filtered_entities = self._filter_entities_by_stakeholder_type()

        for entity in filtered_entities:
            entity_text = entity.get("text", "").strip()

            if not entity_text:
                continue

            # Get stakeholder type and ID
            ner_label = entity.get("label", "")
            stakeholder_type = self.map_ner_label_to_stakeholder_type(ner_label)
            stakeholder_id = self._get_stakeholder_id(entity_text, stakeholder_type)

            if not stakeholder_id:
                skipped_count += 1
                continue

            # Find all chunks that contain this entity text
            for i, chunk_record in chunk_records.items():
                chunk = chunk_record["chunk"]
                chunk_text = chunk["text"]

                # Check if entity text appears in this chunk (case-insensitive for better matching)
                entity_text_lower = entity_text.lower()
                chunk_text_lower = chunk_text.lower()

                if entity_text_lower in chunk_text_lower:
                    # Get existing mentions for this chunk to check overlaps
                    existing_mentions = get_chunk_stakeholders(chunk_record["chunk_id"])

                    # Find the actual position in the chunk (preserve original case)
                    if entity_text in chunk_text:
                        # Find all occurrences in this chunk
                        start_idx = 0
                        while True:
                            pos = chunk_text.find(entity_text, start_idx)
                            if pos == -1:
                                break

                            # Create a ChunkStakeholder for each occurrence
                            created = self._create_chunk_stakeholder(
                                chunk_id=chunk_record["chunk_id"],
                                stakeholder_id=stakeholder_id,
                                entity=entity,
                                mention_text=entity_text,
                                page=chunk_record["page"],
                                existing_mentions=existing_mentions,
                                chunk_text=chunk["text"],
                                chunk_start=chunk.get("start", 0),
                            )

                            if created:
                                cs_count += 1
                                # Add to existing_mentions to prevent duplicates in same loop
                                existing_mentions.append(
                                    {
                                        "stakeholder_id": stakeholder_id,
                                        "mention_bbox": self._get_entity_bbox_from_pdf(
                                            entity_text, chunk_record["page"]
                                        )
                                        or {"x": 100.0, "y": 100.0, "width": 200.0, "height": 100.0},
                                    }
                                )
                            else:
                                overlap_skipped += 1

                            start_idx = pos + 1
                    else:
                        # Case-insensitive match
                        pos = chunk_text_lower.find(entity_text_lower)
                        if pos != -1:
                            # Extract the actual text from chunk (preserving original case)
                            mention_text = chunk_text[pos : pos + len(entity_text)]
                            created = self._create_chunk_stakeholder(
                                chunk_id=chunk_record["chunk_id"],
                                stakeholder_id=stakeholder_id,
                                entity=entity,
                                mention_text=mention_text,
                                page=chunk_record["page"],
                                existing_mentions=existing_mentions,
                                chunk_text=chunk["text"],
                                chunk_start=chunk.get("start", 0),
                            )

                            if created:
                                cs_count += 1
                            else:
                                overlap_skipped += 1

        self._print(f"\n✓ Created {cs_count} ChunkStakeholder records")
        if skipped_count > 0:
            self._print(f"  [!] Skipped {skipped_count} entities (stakeholder not found in database)")
        if overlap_skipped > 0:
            self._print(f"  [!] Skipped {overlap_skipped} overlapping mentions")

        result = {
            "chunks_created": len(chunk_records),
            "chunk_stakeholders_created": cs_count,
            "entities_skipped": skipped_count,
            "overlaps_skipped": overlap_skipped,
        }

        self._print("=" * 60)
        return result

    def _print_summary(self, stats: Dict[str, int]):
        """Print summary statistics."""
        self._print("\n" + "=" * 60)
        self._print("SUMMARY")
        self._print("=" * 60)
        self._print(f"Created: {stats['created']} stakeholders")
        self._print(f"Skipped: {stats['skipped']} (already exist)")
        self._print(f"Total unique: {stats['total']}")

        # Show breakdown by type
        if self.entities:
            type_counts = defaultdict(int)
            for entity in self.entities:
                ner_label = entity.get("label", "")
                stakeholder_type = self.map_ner_label_to_stakeholder_type(ner_label)
                type_counts[stakeholder_type] += 1

            if type_counts:
                self._print("\nBreakdown by type:")
                for stakeholder_type, count in sorted(type_counts.items()):
                    self._print(f"  {stakeholder_type}: {count}")

        all_stakeholders = get_stakeholders()
        self._print(f"\nTotal stakeholders in database: {len(all_stakeholders)}")
        self._print("=" * 60)

    def process(self, create_chunks: bool = True) -> Dict[str, any]:
        """
        Process the markdown file: load, perform NER, populate stakeholders, and optionally create chunks.

        Args:
            create_chunks: If True, also create chunks and ChunkStakeholder records

        Returns:
            Dictionary with processing results and statistics
        """
        self.load_markdown()
        self.perform_ner()
        stats = self.populate_stakeholders()

        result = {
            "entities_found": len(self.entities),
            "stakeholders_created": stats["created"],
            "stakeholders_skipped": stats["skipped"],
            "stakeholders_total": stats["total"],
        }

        if create_chunks:
            chunk_stats = self.populate_chunks_and_entities()
            result.update(
                {
                    "chunks_created": chunk_stats["chunks_created"],
                    "chunk_stakeholders_created": chunk_stats["chunk_stakeholders_created"],
                    "entities_skipped_for_chunks": chunk_stats["entities_skipped"],
                    "overlaps_skipped": chunk_stats.get("overlaps_skipped", 0),
                }
            )

        return result

    def __del__(self):
        """Clean up resources."""
        if hasattr(self, "pdf_doc") and self.pdf_doc is not None:
            try:
                self.pdf_doc.close()
            except:
                pass
