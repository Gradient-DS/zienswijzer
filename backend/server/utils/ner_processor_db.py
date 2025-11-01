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
        use_dutch_model: bool = True,
        dutch_model_type: str = "robbert",
        dutch_model_name: str = "pdelobelle/robbert-v2-dutch-ner",
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
            use_dutch_model: If True, also run a Dutch-specific NER model to catch additional entities
            dutch_model_type: Model type for Dutch NER (default: "xlm-roberta")
            dutch_model_name: Model name for Dutch NER (default: "Davlan/xlm-roberta-base-finetuned-dutch-ner")
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
        self.use_dutch_model = use_dutch_model
        self.dutch_model_type = dutch_model_type
        self.dutch_model_name = dutch_model_name

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

    def _merge_entities(self, primary_entities: List[Dict], secondary_entities: List[Dict]) -> List[Dict]:
        """
        Merge entities from two models, keeping unique entities.
        If the same entity (by text and type) is found by both models,
        keep the one with higher confidence.

        Args:
            primary_entities: Entities from the primary model
            secondary_entities: Entities from the secondary model

        Returns:
            Merged list of unique entities
        """
        # Create a dictionary to track unique entities by (normalized_text, label)
        entity_dict = {}

        # Add primary entities first
        for ent in primary_entities:
            text = ent.get("text", "").strip().lower()
            label = ent.get("label", "")
            key = (text, label)

            if key not in entity_dict or ent.get("confidence", 0.0) > entity_dict[key].get("confidence", 0.0):
                entity_dict[key] = ent

        # Add secondary entities, keeping higher confidence if duplicate
        for ent in secondary_entities:
            text = ent.get("text", "").strip().lower()
            label = ent.get("label", "")
            key = (text, label)

            if key not in entity_dict:
                # New entity from secondary model
                entity_dict[key] = ent
            else:
                # Entity exists, keep the one with higher confidence
                existing_conf = entity_dict[key].get("confidence", 0.0)
                new_conf = ent.get("confidence", 0.0)
                if new_conf > existing_conf:
                    entity_dict[key] = ent

        return list(entity_dict.values())

    def _filter_invalid_entities(self, entities: List[Dict]) -> List[Dict]:
        """
        Filter out invalid entities:
        - Entities with less than 3 characters
        - Entities that start with a lowercase letter

        Args:
            entities: List of entity dictionaries

        Returns:
            Filtered list of entities
        """
        filtered = []
        removed_count = 0

        for ent in entities:
            text = ent.get("text", "").strip()

            # Filter 1: Remove entities with less than 3 characters
            if len(text) < 3:
                removed_count += 1
                if self.verbose:
                    self._print(f"  [FILTER] Removed short entity: '{text}' ({len(text)} characters)")
                continue

            # Filter 2: Remove entities that start with a lowercase letter
            if text and text[0].islower():
                removed_count += 1
                if self.verbose:
                    self._print(f"  [FILTER] Removed entity starting with lowercase: '{text}'")
                continue

            filtered.append(ent)

        if removed_count > 0:
            self._print(f"Filtered out {removed_count} invalid entities (short or lowercase)")

        return filtered

    def perform_ner(self) -> List[Dict]:
        """
        Perform Named Entity Recognition on the markdown text.
        If use_dutch_model is True, also runs a Dutch-specific model and merges results.

        Returns:
            List of entity dictionaries with 'text', 'label', 'start', 'end', 'confidence'
        """
        if not self.full_text:
            raise ValueError("Must load markdown file first (call load_markdown())")

        self._print("=" * 60)
        self._print("Performing Named Entity Recognition...")
        self._print(f"Primary model: {self.model_type} ({self.model_name})")

        try:
            # Run primary model
            entities = extract_entities_from_text(
                self.full_text,
                entity_types=self.entity_types,
                min_confidence=self.min_confidence,
                model_type=self.model_type,
                model_name=self.model_name,
            )

            primary_count = len(entities)
            self._print(f"Primary model found {primary_count} entities")

            # Run Dutch model(s) if enabled
            if self.use_dutch_model:
                # Run the primary Dutch model
                self._print(f"\nRunning Dutch-specific model: {self.dutch_model_type} ({self.dutch_model_name})")
                try:
                    dutch_entities = extract_entities_from_text(
                        self.full_text,
                        entity_types=self.entity_types,
                        min_confidence=self.min_confidence,
                        model_type=self.dutch_model_type,
                        model_name=self.dutch_model_name,
                    )

                    dutch_count = len(dutch_entities)
                    self._print(f"Dutch model found {dutch_count} entities")

                    # Merge entities from both models
                    merged_entities = self._merge_entities(entities, dutch_entities)
                    merged_count = len(merged_entities)
                    new_entities_count = merged_count - primary_count

                    if new_entities_count > 0:
                        self._print(
                            f"Merged results: {merged_count} total entities ({new_entities_count} additional from Dutch model)"
                        )
                    else:
                        self._print(f"Merged results: {merged_count} total entities (no new entities from Dutch model)")

                    entities = merged_entities

                except Exception as e:
                    self._print(f"Warning: Could not run Dutch model: {e}")
                    self._print("Continuing with primary model results only...")
                    if self.verbose:
                        import traceback

                        traceback.print_exc()

            # Also run NER on PDF text to catch entities that might differ from markdown
            # This helps when the PDF text extraction differs from markdown parsing
            if self.pdf_text and self.use_dutch_model:
                self._print("\nAlso running NER on PDF text to catch additional entities...")
                try:
                    pdf_entities = extract_entities_from_text(
                        self.pdf_text,
                        entity_types=self.entity_types,
                        min_confidence=self.min_confidence,
                        model_type=self.model_type,
                        model_name=self.model_name,
                    )

                    # Also run Dutch model on PDF text
                    pdf_dutch_entities = extract_entities_from_text(
                        self.pdf_text,
                        entity_types=self.entity_types,
                        min_confidence=self.min_confidence,
                        model_type=self.dutch_model_type,
                        model_name=self.dutch_model_name,
                    )

                    # Merge PDF entities
                    pdf_all_entities = self._merge_entities(pdf_entities, pdf_dutch_entities)
                    pdf_count = len(pdf_all_entities)
                    self._print(f"PDF text NER found {pdf_count} entities")

                    # Merge with markdown entities
                    merged_entities = self._merge_entities(entities, pdf_all_entities)
                    merged_count = len(merged_entities)
                    new_entities_count = merged_count - len(entities)

                    if new_entities_count > 0:
                        self._print(f"Added {new_entities_count} additional entities from PDF text NER")
                        entities = merged_entities
                    else:
                        self._print("No additional entities found in PDF text")

                except Exception as e:
                    self._print(f"Warning: Could not run NER on PDF text: {e}")
                    if self.verbose:
                        import traceback

                        traceback.print_exc()

            # Apply filtering to remove invalid entities
            initial_count = len(entities)
            self._print("\nApplying entity filters...")
            entities = self._filter_invalid_entities(entities)

            filtered_count = initial_count - len(entities)
            if filtered_count > 0:
                self._print(f"Total filtered: {filtered_count} entities removed ({initial_count} -> {len(entities)})")

            self.entities = entities
            self._print(f"\nTotal entities after filtering: {len(entities)}")

            # Debug: Print some example entities for verification
            if self.verbose and entities:
                self._print(f"\nSample entities found (first 10):")
                for i, ent in enumerate(entities[:10]):
                    self._print(
                        f"  {i+1}. '{ent.get('text', '')}' [{ent.get('label', '')}] (confidence: {ent.get('confidence', 0.0):.2f})"
                    )

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
            raise ValueError("No entities found. Run perform_ner() first.")

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

        # Remove stakeholders that are contained in longer stakeholder names
        self._remove_contained_stakeholders()

        # Summary
        result = {"created": created_count, "skipped": skipped_count, "total": len(unique_stakeholders)}

        self._print_summary(result)
        return result

    def _remove_contained_stakeholders(self):
        """
        Remove stakeholders whose names are contained within longer stakeholder names of the same type.
        For example, if "Peter van Laar" is contained in "Peter van Laarhoven", delete "Peter van Laar".

        This handles cases where NER models detect partial names.
        """
        self._print("\nChecking for contained stakeholders...")

        # Get all stakeholders from database
        all_stakeholders = get_stakeholders()

        if len(all_stakeholders) < 2:
            return  # Need at least 2 stakeholders to compare

        # Group stakeholders by type
        stakeholders_by_type = {}
        for stakeholder in all_stakeholders:
            stype = stakeholder.get("type")
            if stype not in stakeholders_by_type:
                stakeholders_by_type[stype] = []
            stakeholders_by_type[stype].append(stakeholder)

        deleted_count = 0
        deleted_mentions_count = 0

        # Check each type separately
        for stype, stakeholders in stakeholders_by_type.items():
            if len(stakeholders) < 2:
                continue

            # Sort by length (longest first) so we check shorter names against longer ones
            stakeholders_sorted = sorted(stakeholders, key=lambda s: len(s.get("name", "")), reverse=True)

            for i, shorter_stakeholder in enumerate(stakeholders_sorted):
                shorter_name = shorter_stakeholder.get("name", "").strip()
                shorter_id = shorter_stakeholder.get("id")

                if not shorter_name or not shorter_id:
                    continue

                # Check if this name is contained in any longer stakeholder name
                is_contained = False
                containing_stakeholder = None

                for j, longer_stakeholder in enumerate(stakeholders_sorted):
                    if i == j:  # Skip self
                        continue

                    longer_name = longer_stakeholder.get("name", "").strip()
                    longer_id = longer_stakeholder.get("id")

                    # Skip if same length or shorter
                    if len(longer_name) <= len(shorter_name):
                        continue

                    # Check if shorter name is contained in longer name (case-insensitive)
                    # Also check that they're not just at word boundaries - they should be proper substrings
                    shorter_lower = shorter_name.lower()
                    longer_lower = longer_name.lower()

                    if shorter_lower in longer_lower:
                        # Additional check: make sure the shorter name appears as a complete word/phrase
                        # For example, "Peter van Laar" should be in "Peter van Laarhoven"
                        # but we want to be careful about false positives
                        is_contained = True
                        containing_stakeholder = longer_stakeholder
                        break

                if is_contained and containing_stakeholder:
                    # Delete the shorter stakeholder
                    from db.database import get_connection

                    with get_connection() as connection:
                        # Delete chunk-stakeholder records for the shorter stakeholder
                        cursor = connection.execute(
                            "DELETE FROM ChunkStakeholders WHERE stakeholder_id = ?", (shorter_id,)
                        )
                        mentions_deleted = cursor.rowcount
                        deleted_mentions_count += mentions_deleted

                        # Delete the shorter stakeholder
                        connection.execute("DELETE FROM Stakeholders WHERE id = ?", (shorter_id,))
                        deleted_count += 1
                        connection.commit()

                        # Remove from cache
                        key = (shorter_name, stype)
                        if key in self.stakeholder_ids:
                            del self.stakeholder_ids[key]

                        if self.verbose:
                            containing_name = containing_stakeholder.get("name", "")
                            self._print(
                                f"  [DELETE] Removed '{shorter_name}' (contained in '{containing_name}', both {stype}) - deleted {mentions_deleted} mentions"
                            )

        if deleted_count > 0:
            self._print(
                f"Removed {deleted_count} contained stakeholders and {deleted_mentions_count} chunk-stakeholder links"
            )

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
                        "width": rect.x1 - rect.x0,
                        "height": rect.y1 - rect.y0,
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
                "x": 0,
                "y": 0,  # Offset by page
                "width": 0,
                "height": 0,
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

    def _validate_bbox_text(self, bbox: Dict, expected_text: str, pdf_page: any) -> bool:
        """
        Validate that a bounding box contains the expected text and is not empty.

        Args:
            bbox: Bounding box dict with x, y, width, height
            expected_text: The expected entity text
            pdf_page: PyMuPDF page object

        Returns:
            True if bbox contains expected text, False otherwise
        """
        try:
            import fitz  # PyMuPDF

            # Create a rectangle from the bbox
            rect = fitz.Rect(
                bbox["x"],
                bbox["y"],
                bbox["x"] + bbox["width"],
                bbox["y"] + bbox["height"],
            )

            # Extract text from within the rectangle
            extracted_text = pdf_page.get_textbox(rect).strip()

            # Check if bbox is in empty area
            if not extracted_text:
                return False

            # Normalize both texts for comparison (remove spaces, convert to lowercase)
            extracted_normalized = extracted_text.replace(" ", "").lower()
            expected_normalized = expected_text.strip().replace(" ", "").lower()

            # Check if extracted text matches or contains expected text
            # Also check reverse (expected contains extracted) to handle partial matches
            if (
                expected_normalized == extracted_normalized
                or expected_normalized in extracted_normalized
                or extracted_normalized in expected_normalized
            ):
                # Additional check: require at least 70% of expected text length to prevent partial matches
                min_length = max(2, int(len(expected_normalized) * 0.7))
                if len(extracted_normalized) >= min_length:
                    return True

            return False

        except Exception as e:
            if hasattr(self, "verbose") and self.verbose:
                self._print(f"  Warning: Error validating bbox text: {e}")
            return False

    def _get_entity_bbox_from_pdf(
        self, mention_text: str, page: int, chunk_text: Optional[str] = None, chunk_start: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Get bounding box for an entity mention from PDF using PyMuPDF.

        This finds the exact bounding box of the entity text in the PDF using word-level bboxes.
        If chunk_text and chunk_start are provided, it searches within that chunk's region first.
        Validates that the bbox contains the expected text and is not empty.
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
            mention_words = mention_text_clean.split()
            mention_normalized = mention_text_clean.lower().replace(" ", "")

            # Get chunk bbox for filtering if available
            chunk_bbox = None
            if chunk_text and chunk_start is not None:
                chunk_bbox = self._get_chunk_bbox_from_pdf(chunk_text, chunk_start, chunk_start + len(chunk_text), page)

            # Method 1: Use word-level bboxes (most accurate for individual words/phrases)
            # get_text("words") returns: (x0, y0, x1, y1, "word", block_no, line_no, word_no)
            words = pdf_page.get_text("words")

            if words:
                # Find consecutive words that match the entity
                for i, word_info in enumerate(words):
                    word_bbox = word_info[:4]  # (x0, y0, x1, y1)
                    word_text = word_info[4] if len(word_info) > 4 else ""

                    # Check if this word is part of the entity
                    # For single-word entities, exact match
                    if len(mention_words) == 1:
                        if word_text.lower() == mention_words[0].lower():
                            # Verify within chunk area if provided
                            if chunk_bbox:
                                word_center_x = (word_bbox[0] + word_bbox[2]) / 2
                                word_center_y = (word_bbox[1] + word_bbox[3]) / 2
                                if not (
                                    chunk_bbox["x"] <= word_center_x <= chunk_bbox["x"] + chunk_bbox["width"]
                                    and chunk_bbox["y"] <= word_center_y <= chunk_bbox["y"] + chunk_bbox["height"]
                                ):
                                    continue

                            # Found exact word match - validate bbox contains expected text
                            candidate_bbox = {
                                "x": word_bbox[0],
                                "y": word_bbox[1],
                                "width": word_bbox[2] - word_bbox[0],
                                "height": word_bbox[3] - word_bbox[1],
                            }

                            if self._validate_bbox_text(candidate_bbox, mention_text_clean, pdf_page):
                                return candidate_bbox
                    else:
                        # Multi-word entity: find consecutive words matching the entity
                        if i + len(mention_words) <= len(words):
                            matched_words = []
                            for j, expected_word in enumerate(mention_words):
                                if i + j < len(words):
                                    check_word = words[i + j][4] if len(words[i + j]) > 4 else ""
                                    if check_word.lower() == expected_word.lower():
                                        matched_words.append(words[i + j])
                                    else:
                                        break

                            if len(matched_words) == len(mention_words):
                                # All words matched, calculate combined bbox
                                all_x0 = [w[0] for w in matched_words]
                                all_y0 = [w[1] for w in matched_words]
                                all_x1 = [w[2] for w in matched_words]
                                all_y1 = [w[3] for w in matched_words]

                                # Verify within chunk area if provided
                                if chunk_bbox:
                                    combined_center_x = (min(all_x0) + max(all_x1)) / 2
                                    combined_center_y = (min(all_y0) + max(all_y1)) / 2
                                    if not (
                                        chunk_bbox["x"] <= combined_center_x <= chunk_bbox["x"] + chunk_bbox["width"]
                                        and chunk_bbox["y"]
                                        <= combined_center_y
                                        <= chunk_bbox["y"] + chunk_bbox["height"]
                                    ):
                                        continue

                                # Return combined bbox for all words - validate bbox contains expected text
                                candidate_bbox = {
                                    "x": min(all_x0),
                                    "y": min(all_y0),
                                    "width": max(all_x1) - min(all_x0),
                                    "height": max(all_y1) - min(all_y0),
                                }

                                if self._validate_bbox_text(candidate_bbox, mention_text_clean, pdf_page):
                                    return candidate_bbox

            # Method 2: Fallback to direct page search (good for exact text matches)
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

                        # Verify within chunk area if provided
                        if chunk_bbox:
                            rect_center_x = (rect.x0 + rect.x1) / 2
                            rect_center_y = (rect.y0 + rect.y1) / 2
                            if not (
                                chunk_bbox["x"] <= rect_center_x <= chunk_bbox["x"] + chunk_bbox["width"]
                                and chunk_bbox["y"] <= rect_center_y <= chunk_bbox["y"] + chunk_bbox["height"]
                            ):
                                continue

                        # Validate bbox contains expected text
                        candidate_bbox = {
                            "x": rect.x0,
                            "y": rect.y0,
                            "width": rect.x1 - rect.x0,
                            "height": rect.y1 - rect.y0,
                        }

                        if self._validate_bbox_text(candidate_bbox, mention_text_clean, pdf_page):
                            return candidate_bbox

            # Method 3: Fallback to span matching (less accurate but better than nothing)
            text_dict = pdf_page.get_text("dict")
            for block in text_dict.get("blocks", []):
                if "lines" not in block:
                    continue

                for line in block["lines"]:
                    for span in line["spans"]:
                        span_text = span.get("text", "").strip()
                        span_text_normalized = span_text.replace(" ", "").lower()

                        if (
                            mention_text_clean.lower() in span_text.lower()
                            or span_text.lower() in mention_text_clean.lower()
                            or mention_normalized == span_text_normalized
                        ):
                            span_bbox = span.get("bbox", [])

                            if len(span_bbox) == 4:
                                # If chunk bbox exists, verify this span is within it
                                if chunk_bbox:
                                    span_center_x = (span_bbox[0] + span_bbox[2]) / 2
                                    span_center_y = (span_bbox[1] + span_bbox[3]) / 2

                                    if not (
                                        chunk_bbox["x"] <= span_center_x <= chunk_bbox["x"] + chunk_bbox["width"]
                                        and chunk_bbox["y"] <= span_center_y <= chunk_bbox["y"] + chunk_bbox["height"]
                                    ):
                                        continue  # Skip if outside chunk area

                                # Calculate character position within span to get more precise bbox
                                mention_pos = span_text.lower().find(mention_text_clean.lower())
                                if mention_pos >= 0 and len(span_text) > 0:
                                    # Estimate bbox based on character position (proportional)
                                    span_width = span_bbox[2] - span_bbox[0]
                                    char_width = span_width / len(span_text) if span_text else span_width

                                    estimated_x0 = span_bbox[0] + (mention_pos * char_width)
                                    estimated_x1 = estimated_x0 + (len(mention_text_clean) * char_width)

                                    # Validate estimated bbox contains expected text
                                    candidate_bbox = {
                                        "x": estimated_x0,
                                        "y": span_bbox[1],
                                        "width": estimated_x1 - estimated_x0,
                                        "height": span_bbox[3] - span_bbox[1],
                                    }

                                    if self._validate_bbox_text(candidate_bbox, mention_text_clean, pdf_page):
                                        return candidate_bbox

                        if self._validate_bbox_text(candidate_bbox, mention_text_clean, pdf_page):
                            return candidate_bbox

            # Method 3: Fallback to span matching (less accurate but better than nothing)
            text_dict = pdf_page.get_text("dict")
            for block in text_dict.get("blocks", []):
                if "lines" not in block:
                    continue

                for line in block["lines"]:
                    for span in line["spans"]:
                        span_text = span.get("text", "").strip()
                        span_text_normalized = span_text.replace(" ", "").lower()

                        if (
                            mention_text_clean.lower() in span_text.lower()
                            or span_text.lower() in mention_text_clean.lower()
                            or mention_normalized == span_text_normalized
                        ):
                            span_bbox = span.get("bbox", [])

                            if len(span_bbox) == 4:
                                # If chunk bbox exists, verify this span is within it
                                if chunk_bbox:
                                    span_center_x = (span_bbox[0] + span_bbox[2]) / 2
                                    span_center_y = (span_bbox[1] + span_bbox[3]) / 2

                                    if not (
                                        chunk_bbox["x"] <= span_center_x <= chunk_bbox["x"] + chunk_bbox["width"]
                                        and chunk_bbox["y"] <= span_center_y <= chunk_bbox["y"] + chunk_bbox["height"]
                                    ):
                                        continue  # Skip if outside chunk area

                                # Calculate character position within span to get more precise bbox
                                mention_pos = span_text.lower().find(mention_text_clean.lower())
                                if mention_pos >= 0 and len(span_text) > 0:
                                    # Estimate bbox based on character position (proportional)
                                    span_width = span_bbox[2] - span_bbox[0]
                                    char_width = span_width / len(span_text) if span_text else span_width

                                    estimated_x0 = span_bbox[0] + (mention_pos * char_width)
                                    estimated_x1 = estimated_x0 + (len(mention_text_clean) * char_width)

                                    # Validate estimated bbox contains expected text
                                    candidate_bbox = {
                                        "x": estimated_x0,
                                        "y": span_bbox[1],
                                        "width": estimated_x1 - estimated_x0,
                                        "height": span_bbox[3] - span_bbox[1],
                                        "page": page,
                                    }

                                    if self._validate_bbox_text(candidate_bbox, mention_text_clean, pdf_page):
                                        return candidate_bbox
                                else:
                                    # Fallback to full span bbox - validate it contains expected text
                                    candidate_bbox = {
                                        "x": span_bbox[0],
                                        "y": span_bbox[1],
                                        "width": span_bbox[2] - span_bbox[0],
                                        "height": span_bbox[3] - span_bbox[1],
                                        "page": page,
                                    }

                                    if self._validate_bbox_text(candidate_bbox, mention_text_clean, pdf_page):
                                        return candidate_bbox

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
                "x": 0,
                "y": 0,  # Offset by page
                "width": 0,  # Width based on text length
                "height": 0,
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
                    return page_info["page_num"]
                current_pos += page_text_len + 1  # +1 for newline

            return self.pdf_pages_text[-1]["page_num"] if self.pdf_pages_text else 1

        # Create chunk records in database
        chunk_records = {}  # chunk index -> {'chunk_id': ..., 'chunk': ..., 'page': ...}

        self._print("\nCreating chunks in database...")
        for i, chunk in enumerate(text_chunks):
            chunk_page = get_chunk_page(chunk.get("start", 0), chunk.get("end", 0)) if self.pdf_text else 1
            chunk_id = self._create_chunk(self.document_id, chunk, page=chunk_page)
            chunk_records[i] = {"chunk_id": chunk_id, "chunk": chunk, "page": chunk_page}

        self._print(f"  ✓ Created {len(chunk_records)} chunks in database")

        # Map ALL entity occurrences to chunks and create ChunkStakeholder records
        self._print("\nMapping entities to chunks and creating ChunkStakeholder records...")
        cs_count = 0
        skipped_count = 0
        overlap_skipped = 0

        filtered_entities = self._filter_entities_by_stakeholder_type()

        # Track entities that only appear in lowercase - these should be filtered out
        entities_with_lowercase_only = set()

        # Debug: Track entities that are being checked
        entities_not_found_in_chunks = []

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
                if self.verbose and entity_text.lower() in ["anja koeleman", "koeleman"]:
                    self._print(
                        f"  [DEBUG] Entity '{entity_text}' found by NER but stakeholder_id not found (label: {ner_label}, type: {stakeholder_type})"
                    )
                continue

            # Track if entity was found in any chunk
            entity_found_in_chunk = False
            # Track mentions across all chunks for this entity
            found_valid_mention_for_entity = False
            found_lowercase_mention_for_entity = False
            lowercase_mention_count = 0
            valid_mention_count = 0

            # Find all chunks that contain this entity text
            for i, chunk_record in chunk_records.items():
                chunk = chunk_record["chunk"]
                chunk_text = chunk["text"]

                # Check if entity text appears in this chunk (case-insensitive for better matching)
                entity_text_lower = entity_text.lower()
                chunk_text_lower = chunk_text.lower()

                if entity_text_lower in chunk_text_lower:
                    entity_found_in_chunk = True
                    # Get existing mentions for this chunk to check overlaps
                    existing_mentions = get_chunk_stakeholders(chunk_record["chunk_id"])

                    if entity_text in chunk_text:
                        # Find all occurrences in this chunk
                        start_idx = 0
                        while True:
                            pos = chunk_text.find(entity_text, start_idx)
                            if pos == -1:
                                break

                            # Check the actual mention text in the chunk
                            mention_text = chunk_text[pos : pos + len(entity_text)]

                            # Filter: Skip if mention is short (< 3 chars) or starts with lowercase
                            if len(mention_text) < 3:
                                start_idx = pos + 1
                                continue

                            if mention_text and mention_text[0].islower():
                                # Track lowercase mention for this entity
                                found_lowercase_mention_for_entity = True
                                lowercase_mention_count += 1
                                start_idx = pos + 1
                                continue

                            # Valid mention (capitalized and >= 3 chars)
                            found_valid_mention_for_entity = True
                            valid_mention_count += 1

                            # Create a ChunkStakeholder for each occurrence
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

                            # Filter: Skip if mention is short (< 3 chars)
                            if len(mention_text) < 3:
                                continue

                            if mention_text and mention_text[0].islower():
                                # Track lowercase mention for this entity
                                found_lowercase_mention_for_entity = True
                                lowercase_mention_count += 1
                                continue

                            # Valid mention (capitalized and >= 3 chars)
                            found_valid_mention_for_entity = True
                            valid_mention_count += 1

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

            # After checking all chunks for this entity, if we found ANY lowercase mentions, mark for removal
            # Real entities should always be capitalized - if we see lowercase, it's likely a false positive
            # (like "ver" from "over" or "verder")
            if found_lowercase_mention_for_entity:
                entities_with_lowercase_only.add(entity_text)
                if self.verbose:
                    self._print(
                        f"  [FILTER] Entity '{entity_text}' has lowercase mentions ({lowercase_mention_count} lowercase, {valid_mention_count} capitalized) - will be removed"
                    )

            # Track entities that weren't found in any chunk
            if not entity_found_in_chunk:
                entities_not_found_in_chunks.append(
                    {
                        "text": entity_text,
                        "type": stakeholder_type,
                        "label": ner_label,
                    }
                )
                if self.verbose and entity_text.lower() in ["anja koeleman", "koeleman"]:
                    self._print(
                        f"  [DEBUG] Entity '{entity_text}' (stakeholder_id: {stakeholder_id}) not found in any PDF chunk"
                    )

        self._print(f"\n✓ Created {cs_count} ChunkStakeholder records")

        # Report and delete stakeholders for entities that only appeared in lowercase
        if entities_with_lowercase_only:
            self._print(
                f"  [!] Found {len(entities_with_lowercase_only)} entities that only appear in lowercase (will delete stakeholders)"
            )
            if self.verbose:
                self._print(f"  Entities with lowercase-only mentions (first 10):")
                for ent in list(entities_with_lowercase_only)[:10]:
                    self._print(f"    - '{ent}'")

            # Delete stakeholders and their chunk-stakeholder links for these entities
            deleted_stakeholders = 0
            deleted_mentions = 0

            for entity_text in entities_with_lowercase_only:
                # Get stakeholder type for this entity
                # We need to find it from the filtered_entities
                entity_obj = None
                for ent in filtered_entities:
                    if ent.get("text", "").strip() == entity_text:
                        entity_obj = ent
                        break

                if entity_obj:
                    ner_label = entity_obj.get("label", "")
                    stakeholder_type = self.map_ner_label_to_stakeholder_type(ner_label)
                    stakeholder_id = self._get_stakeholder_id(entity_text, stakeholder_type)

                    if stakeholder_id:
                        # Delete chunk-stakeholder links
                        from db.database import get_connection

                        with get_connection() as connection:
                            # Delete chunk-stakeholder records
                            cursor = connection.execute(
                                "DELETE FROM ChunkStakeholders WHERE stakeholder_id = ?", (stakeholder_id,)
                            )
                            deleted_mentions += cursor.rowcount

                            # Delete stakeholder
                            connection.execute("DELETE FROM Stakeholders WHERE id = ?", (stakeholder_id,))
                            deleted_stakeholders += 1
                            connection.commit()

                            # Remove from cache
                            if (entity_text, stakeholder_type) in self.stakeholder_ids:
                                del self.stakeholder_ids[(entity_text, stakeholder_type)]

            if deleted_stakeholders > 0:
                self._print(
                    f"  Deleted {deleted_stakeholders} stakeholders and {deleted_mentions} chunk-stakeholder links for lowercase-only entities"
                )

            # Remove these entities from self.entities
            filtered_entity_list = []
            for ent in self.entities:
                ent_text = ent.get("text", "").strip()
                if ent_text not in entities_with_lowercase_only:
                    filtered_entity_list.append(ent)

            removed_count = len(self.entities) - len(filtered_entity_list)
            if removed_count > 0:
                self._print(f"  Removed {removed_count} entities with lowercase-only mentions from entity list")
                self.entities = filtered_entity_list

        # Report entities not found in chunks
        if entities_not_found_in_chunks:
            self._print(
                f"  [!] {len(entities_not_found_in_chunks)} entities were found by NER but not found in any PDF chunks"
            )
            if self.verbose:
                self._print(f"  Entities not found in chunks (first 10):")
                for ent in entities_not_found_in_chunks[:10]:
                    self._print(f"    - '{ent['text']}' ({ent['type']}, label: {ent['label']})")
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
