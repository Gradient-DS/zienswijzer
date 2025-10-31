"""
Markdown NER Processor and Stakeholder Populator

This module provides a class to process markdown files, perform Named Entity Recognition,
and populate the Stakeholders database table with found entities.
"""

import json
import sys
import uuid
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Tuple, Optional



# Add parent directory to path for imports
server_dir = Path(__file__).parent.parent
sys.path.insert(0, str(server_dir))

from db.database import init_db, create_stakeholder, get_stakeholders, get_connection, create_document
from utils.ner import extract_entities_from_text


class MarkdownNERProcessor:
    """
    Processes markdown files, performs NER, and populates the Stakeholders database.
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
        pdf_path: Optional[str] = None
    ):
        """
        Initialize the Markdown NER Processor.
        
        Args:
            markdown_path: Path to the markdown file to process
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
        self.pdf_text = None  # Text extracted from PDF (if PDF provided)
        self.pdf_pages_text = []  # List of {page_num, text} for each PDF page
        self.entities = []
        self.stakeholder_ids = {}  # Cache: (name, type) -> stakeholder_id
        
        # Open PDF if provided (for chunking and extracting bounding boxes)
        if pdf_path and Path(pdf_path).exists():
            try:
                import fitz  # PyMuPDF
                self.pdf_doc = fitz.open(pdf_path)
                if self.verbose:
                    self._print(f"Opened PDF: {pdf_path} ({len(self.pdf_doc)} pages)")
                # Extract text from PDF
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
        """Extract text from PDF and store it for chunking."""
        if not hasattr(self, 'pdf_doc') or self.pdf_doc is None:
            return
        
        try:
            import fitz  # PyMuPDF
            self.pdf_text = ""
            self.pdf_pages_text = []
            
            for page_num in range(len(self.pdf_doc)):
                page = self.pdf_doc[page_num]
                page_text = page.get_text()
                self.pdf_text += page_text + "\n"
                self.pdf_pages_text.append({
                    'page_num': page_num,
                    'text': page_text,
                    'page': page
                })
            
            if self.verbose:
                self._print(f"Extracted {len(self.pdf_text)} characters from PDF ({len(self.pdf_pages_text)} pages)")
        except Exception as e:
            if self.verbose:
                self._print(f"Error extracting PDF text: {e}")
    
    def load_markdown(self) -> str:
        """
        Load and return the markdown file content.
        
        Note: If PDF is provided, NER will be performed on markdown,
        but chunking will use PDF text for better layout-based chunking.
        """
        if not self.markdown_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {self.markdown_path}")
        
        with open(self.markdown_path, 'r', encoding='utf-8') as f:
            self.full_text = f.read()
        
        self._print(f"Loaded {len(self.full_text)} characters from {self.markdown_path}")
        
        # If PDF text is available, inform user that chunking will use PDF
        if self.pdf_text:
            self._print(f"Note: NER will use markdown text, but chunking will use PDF text ({len(self.pdf_text)} chars)")
        
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
                model_name=self.model_name
            )
            
            # Filter out very short entities and None values
            entities = [
                ent for ent in entities 
                if ent is not None and len(ent.get('text', '').strip()) > 2
            ]
            
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
    
    def _check_stakeholder_exists(self, name: str, type: str) -> bool:
        """Check if a stakeholder with this name and type already exists."""
        with get_connection() as connection:
            cursor = connection.execute("""
                SELECT id FROM Stakeholders
                WHERE name = ? AND type = ?
            """, (name, type))
            return cursor.fetchone() is not None
    
    def _get_stakeholder_id(self, name: str, type: str) -> Optional[str]:
        """Get stakeholder ID by name and type. Caches results."""
        key = (name, type)
        if key in self.stakeholder_ids:
            return self.stakeholder_ids[key]
        
        with get_connection() as connection:
            cursor = connection.execute("""
                SELECT id FROM Stakeholders
                WHERE name = ? AND type = ?
            """, (name, type))
            row = cursor.fetchone()
            if row:
                self.stakeholder_ids[key] = row[0]
                return row[0]
        return None
    
    def _filter_entities_by_stakeholder_type(self) -> List[Dict]:
        """Filter entities by stakeholder types to save."""
        if self.stakeholder_types_to_save is None:
            return self.entities
        
        self._print(f"\nFiltering entities to only save: {self.stakeholder_types_to_save}")
        initial_count = len(self.entities)
        
        filtered = []
        for entity in self.entities:
            ner_label = entity.get('label', '')
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
            name = entity.get('text', '').strip()
            if not name or len(name) < 2:
                continue
            
            ner_label = entity.get('label', '')
            stakeholder_type = self.map_ner_label_to_stakeholder_type(ner_label)
            key = (name, stakeholder_type)
            
            # Keep entity with highest confidence if duplicates exist
            if key not in unique_stakeholders:
                unique_stakeholders[key] = entity
            else:
                current_confidence = unique_stakeholders[key].get('confidence', 0.0)
                new_confidence = entity.get('confidence', 0.0)
                if new_confidence > current_confidence:
                    unique_stakeholders[key] = entity
        
        return unique_stakeholders
    
    def populate_stakeholders(self) -> Dict[str, int]:
        """
        Populate the Stakeholders table with entities found in the markdown file.
        
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
        now = datetime.now().isoformat()
        created_count = 0
        skipped_count = 0
        
        self._print("\nPopulating Stakeholders table...")
        for (name, stakeholder_type), entity in unique_stakeholders.items():
            # Check if already exists
            if self._check_stakeholder_exists(name, stakeholder_type):
                self._print(f"  [SKIP] {name} ({stakeholder_type}) - already exists")
                skipped_count += 1
                continue
            
            # Create stakeholder
            stakeholder_id = f"stakeholder_{datetime.now().timestamp()}"
            stakeholder = {
                "id": stakeholder_id,
                "type": stakeholder_type,
                "name": name,
                "contact_info": "Werk nou eens joh",
                "created_at": now,
                "updated_at": now
            }
            
            try:
                create_stakeholder(stakeholder)
                self.stakeholder_ids[(name, stakeholder_type)] = stakeholder_id  # Cache ID
                self._print(f"  [✓] Created: {name} ({stakeholder_type})")
                created_count += 1
            except Exception as e:
                self._print(f"  [✗] Error creating {name}: {e}")
        
        # Summary
        result = {
            "created": created_count,
            "skipped": skipped_count,
            "total": len(unique_stakeholders)
        }
        
        self._print_summary(result)
        return result
    
    def _split_text_into_chunks(self, text: str, chunk_size: int = 500) -> List[Dict]:
        """
        Split text into chunks (paragraph-based for markdown).
        Returns list of chunks with 'text', 'start', 'end' positions.
        """
        chunks = []
        
        # Split by double newlines (paragraphs)
        paragraphs = text.split('\n\n')
        
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
                    chunk_text = ' '.join(current_chunk_words)
                    
                    if len(chunk_text) >= chunk_size:
                        chunk_end = current_pos + len(chunk_text)
                        chunks.append({
                            'text': chunk_text,
                            'start': chunk_start,
                            'end': chunk_end
                        })
                        current_pos = chunk_end
                        current_chunk_words = []
                        chunk_start = chunk_end
                
                if current_chunk_words:
                    chunk_text = ' '.join(current_chunk_words)
                    chunk_end = current_pos + len(chunk_text)
                    chunks.append({
                        'text': chunk_text,
                        'start': chunk_start,
                        'end': chunk_end
                    })
                    current_pos = chunk_end
            else:
                # Find paragraph in original text
                para_start = text.find(para, current_pos)
                if para_start == -1:
                    para_start = current_pos
                para_end = para_start + len(para)
                
                chunks.append({
                    'text': para,
                    'start': para_start,
                    'end': para_end
                })
                current_pos = para_end
        
        return chunks
    
    # def _create_or_get_document(self) -> str:
    #     """Create or get document record. Returns document_id."""
    #     file_path = str(self.markdown_path.absolute())
        
    #     # Check if document exists
    #     with get_connection() as connection:
    #         cursor = connection.execute("""
    #             SELECT id FROM Documents WHERE file_path = ?
    #         """, (file_path,))
    #         row = cursor.fetchone()
    #         if row:
    #             return row[0]
        
    #     # Create new document
    #     document_id = f"doc_{uuid.uuid4().hex[:16]}"
    #     document = {
    #         "id": document_id,
    #         "title": self.markdown_path.stem,
    #         "description": f"Markdown document: {self.markdown_path.name}",
    #         "type": "markdown",
    #         "file_path": file_path,
    #         "file_size": len(self.full_text.encode('utf-8')),
    #         "page_count": 1,
    #         "processing_status": "completed",
    #         "uploaded_at": datetime.now().isoformat(),
    #         "processed_at": datetime.now().isoformat(),
    #         "created_at": datetime.now().isoformat(),
    #         "updated_at": datetime.now().isoformat()
    #     }
    #     create_document(document)
    #     return document_id
    
    def _get_chunk_bbox_from_pdf(self, chunk_text: str, chunk_start: int, chunk_end: int) -> Optional[Dict]:
        """
        Get bounding box for a chunk from PDF using PyMuPDF.
        

        This finds the full bounding box of the text block containing the chunk.
        Returns None if not a PDF or if chunk not found.
        """
        # Check if we're processing a PDF file
        if not hasattr(self, 'pdf_doc') or self.pdf_doc is None:
            return None
        
        try:
            import fitz  # PyMuPDF
        except ImportError:
            return None
        
        if not chunk_text or len(chunk_text.strip()) < 5:
            return None
        
        # Normalize chunk text for matching (remove extra whitespace)
        chunk_text_normalized = ' '.join(chunk_text.strip().split())
        
        # Search through all pages
        for page_num in range(len(self.pdf_doc)):
            page = self.pdf_doc[page_num]
            
            # Method 1: Get full text blocks and match by content
            # This is more accurate as it gets the entire paragraph bounding box
            text_dict = page.get_text("dict")
            for block in text_dict.get("blocks", []):
                if "lines" not in block:  # Skip image blocks
                    continue
                
                # Reconstruct full block text
                block_text_parts = []
                block_lines = []
                min_x, min_y = float('inf'), float('inf')
                max_x, max_y = float('-inf'), float('-inf')
                
                for line in block["lines"]:
                    line_text = ""
                    for span in line["spans"]:
                        span_text = span.get("text", "")
                        line_text += span_text
                        
                        # Track bounding box
                        bbox = span.get("bbox", [])
                        if len(bbox) == 4:
                            min_x = min(min_x, bbox[0])
                            min_y = min(min_y, bbox[1])
                            max_x = max(max_x, bbox[2])
                            max_y = max(max_y, bbox[3])
                    
                    block_text_parts.append(line_text)
                
                block_text = ' '.join(block_text_parts)
                block_text_normalized = ' '.join(block_text.strip().split())
                
                # Check if chunk text appears in this block (use at least 50% of chunk text)
                chunk_len = len(chunk_text_normalized)
                if chunk_len > 0:
                    # Check if significant portion of chunk is in block
                    if chunk_text_normalized[:max(50, chunk_len // 2)] in block_text_normalized:
                        # Use the block's bbox from the dict, or calculate from spans
                        block_bbox = block.get("bbox", [min_x, min_y, max_x, max_y])
                        
                        if len(block_bbox) == 4 and (block_bbox[2] > block_bbox[0] and block_bbox[3] > block_bbox[1]):
                            return {
                                "x": block_bbox[0],
                                "y": block_bbox[1],
                                "width": block_bbox[2] - block_bbox[0],
                                "height": block_bbox[3] - block_bbox[1],
                                "page": page_num
                            }
            
            # Method 2: Fallback - search for chunk text directly
            # Use first ~100 chars for searching
            search_text = chunk_text_normalized[:100]
            if len(search_text) >= 10:
                text_instances = page.search_for(search_text)
                if text_instances:
                    # Get the bounding box of the first occurrence
                    rect = text_instances[0]
                    return {
                        "x": rect.x0,
                        "y": rect.y0,
                        "width": rect.x1 - rect.x0,
                        "height": rect.y1 - rect.y0,
                        "page": page_num
                    }
        
        return None
    
    def _create_chunk(self, document_id: str, chunk_data: Dict, page: int = 0) -> str:
        """
        Create a chunk in the database. Returns chunk_id.
        
        Stores the chunk's bounding box in Chunks.bbox (for highlighting the entire chunk).
        For PDFs, tries to get real bounding boxes using PyMuPDF if available.
        """
        chunk_id = f"chunk_{uuid.uuid4().hex[:16]}"
        
        # Try to get bounding box from PDF if available
        chunk_bbox = self._get_chunk_bbox_from_pdf(
            chunk_data['text'], 
            chunk_data.get('start', 0), 
            chunk_data.get('end', 0)
        )
        
        # If no PDF bbox found, use placeholder
        if chunk_bbox is None:
            chunk_bbox = {
                "x": 100.0,
                "y": 100.0,
                "width": 100.0,
                "height": 200.0,
                "page": page
            }
        
        bbox = json.dumps(chunk_bbox)
        
        with get_connection() as connection:
            connection.execute("""
                INSERT INTO Chunks (id, document_id, page, context, bbox, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                chunk_id,
                document_id,
                page,
                chunk_data['text'],  # The text content of the chunk
                bbox,  # Bounding box of the CHUNK (for highlighting the entire chunk with PyMuPDF)
                datetime.now().isoformat()
            ))
            connection.commit()
        
        return chunk_id
    
    def _get_entity_bbox_from_pdf(self, mention_text: str, page: int) -> Optional[Dict]:
        """
        Get bounding box for an entity mention from PDF using PyMuPDF.
        
        This finds the exact bounding box of the entity text in the PDF.
        Returns None if not a PDF or if entity not found.
        """
        if not hasattr(self, 'pdf_doc') or self.pdf_doc is None:
            return None
        
        try:
            import fitz  # PyMuPDF
        except ImportError:
            return None
        
        if not mention_text or len(mention_text.strip()) < 2:
            return None
        
        try:
            if page >= len(self.pdf_doc):
                return None
            
            pdf_page = self.pdf_doc[page]
            
            # Clean and normalize mention text
            mention_text_clean = mention_text.strip()
            
            # Method 1: Direct search for exact text
            text_instances = pdf_page.search_for(mention_text_clean)
            
            if text_instances:
                # Get the first occurrence (most accurate)
                rect = text_instances[0]
                return {
                    "x": rect.x0,
                    "y": rect.y0,
                    "width": rect.x1 - rect.x0,
                    "height": rect.y1 - rect.y0,
                    "page": page
                }
            
            # Method 2: Search for text in spans (more precise for exact matches)
            text_dict = pdf_page.get_text("dict")
            for block in text_dict.get("blocks", []):
                if "lines" not in block:
                    continue
                
                for line in block["lines"]:
                    for span in line["spans"]:
                        span_text = span.get("text", "").strip()
                        
                        # Check if mention text is in this span (exact or case-insensitive)
                        if (mention_text_clean in span_text or 
                            mention_text_clean.lower() == span_text.lower() or
                            span_text in mention_text_clean):
                            
                            span_bbox = span.get("bbox", [])
                            if len(span_bbox) == 4:
                                return {
                                    "x": span_bbox[0],
                                    "y": span_bbox[1],
                                    "width": span_bbox[2] - span_bbox[0],
                                    "height": span_bbox[3] - span_bbox[1],
                                    "page": page
                                }
                            
        except Exception as e:
            if hasattr(self, 'verbose') and self.verbose:
                print(f"  Warning: Error getting entity bbox: {e}")
        
        return None
    
    def _create_chunk_stakeholder(
        self, 
        chunk_id: str, 
        stakeholder_id: str, 
        entity: Dict, 
        mention_text: str,
        chunk_bbox: Optional[Dict] = None,
        page: int = 0
    ) -> None:
        """
        Create a ChunkStakeholder record.
        
        Each entry represents one occurrence of an entity in a chunk.
        Multiple occurrences of the same entity in the same chunk create multiple entries.
        
        Stores:
        - chunk_id: Links to the chunk (which has its own bbox in Chunks.bbox)
        - mention_bbox: Bounding box of THIS SPECIFIC ENTITY MENTION (for highlighting the entity)
        - Both bounding boxes are needed: chunk bbox for the paragraph, entity bbox for the entity itself
        
        Args:
            chunk_id: ID of the chunk containing this entity mention
            stakeholder_id: ID of the stakeholder
            entity: Entity dictionary with 'confidence', 'start', 'end', etc.
            mention_text: The actual text of the entity as it appears in the chunk
            chunk_bbox: Bounding box of the chunk (for reference, but stored separately in Chunks table)
            page: Page number where the chunk/entity is located
        """
        cs_id = f"cs_{uuid.uuid4().hex[:16]}"
        
        # Try to get bounding box from PDF if available
        mention_bbox = self._get_entity_bbox_from_pdf(mention_text, page)
        
        # If no PDF bbox found, use placeholder
        if mention_bbox is None:
            mention_bbox = {
                "x": 100.0,      # Left coordinate (placeholder)
                "y": 100.0,      # Top coordinate (placeholder)
                "width": 200,    # Right coordinate (placeholder)
                "height": 100.0,     # Bottom coordinate (placeholder)
                "page": page  # Page number where entity is located
            }
        
        mention_bbox_json = json.dumps(mention_bbox)
        
        # Get confidence from entity dict (should be from NER model)
        # Ensure it's a float and handle None/bytes cases
        entity_confidence = entity.get('confidence', 0.5)
        if isinstance(entity_confidence, bytes):
            try:
                entity_confidence = float(entity_confidence.decode('utf-8'))
            except:
                entity_confidence = 0.5
        elif entity_confidence is None:
            entity_confidence = 0.5
        else:
            entity_confidence = float(entity_confidence)
        
        with get_connection() as connection:
            connection.execute("""
                INSERT INTO ChunkStakeholders (
                    id, chunk_id, stakeholder_id, confidence, mention_text, mention_bbox, verified, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cs_id,
                chunk_id,
                stakeholder_id,
                entity_confidence,  # NER confidence score from model (correctly extracted)
                mention_text,  # The actual text of the entity mention in this chunk
                mention_bbox_json,  # Bounding box for the entity (for highlighting with PyMuPDF)
                0,  # verified = False by default
                datetime.now().isoformat()
            ))
            connection.commit()
    
    def populate_chunks_and_entities(self) -> Dict[str, int]:
        """
        Create chunks from text and populate ChunkStakeholders table.
        
        Each entity occurrence in a chunk creates a separate ChunkStakeholder entry.
        Multiple occurrences of the same entity in the same chunk will create multiple entries.
        Each entry stores:
        - chunk_id: The chunk containing the entity
        - stakeholder_id: The stakeholder mentioned
        - confidence: NER confidence score
        - mention_text: The actual text of the entity as it appears in the chunk
        - mention_bbox: Bounding box for highlighting (placeholder for markdown, PyMuPDF coordinates for PDFs)
        - created_at: When the entry was created
        
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
        
        # Split text into chunks (use PDF text if available, otherwise markdown)
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
                return 0
            
            current_pos = 0
            for page_info in self.pdf_pages_text:
                page_text_len = len(page_info['text'])
                if chunk_start < current_pos + page_text_len:
                    return page_info['page_num']
                current_pos += page_text_len + 1  # +1 for newline
            
            return self.pdf_pages_text[-1]['page_num'] if self.pdf_pages_text else 0
        
        # Create chunk records in database
        chunk_records = {}  # chunk index -> {'chunk_id': ..., 'chunk': ..., 'bbox': ..., 'page': ...}
        
        self._print("\nCreating chunks in database...")
        for i, chunk in enumerate(text_chunks):
            # Determine page number (for PDF) or use 0 (for markdown)
            chunk_page = get_chunk_page(chunk.get('start', 0), chunk.get('end', 0)) if self.pdf_text else 0
            chunk_id = self._create_chunk(self.document_id, chunk, page=chunk_page)
            chunk_records[i] = {
                'chunk_id': chunk_id,
                'chunk': chunk,
                'bbox': None,  # Will be extracted from PDF if available
                'page': chunk_page
            }
        
        self._print(f"  ✓ Created {len(chunk_records)} chunks in database")
        
        # Map ALL entity occurrences to chunks and create ChunkStakeholder records
        # Important: We process ALL entities (not just unique ones) to capture every occurrence
        # Note: Entities are from markdown text, but chunks are from PDF text
        # We need to search for entity text in the chunked text
        self._print("\nMapping entities from markdown to PDF chunks and creating ChunkStakeholder records...")
        cs_count = 0
        skipped_count = 0
        
        filtered_entities = self._filter_entities_by_stakeholder_type()
        
        for entity in filtered_entities:
            entity_text = entity.get('text', '').strip()
            
            if not entity_text:
                continue
            
            # Get stakeholder type and ID
            ner_label = entity.get('label', '')
            stakeholder_type = self.map_ner_label_to_stakeholder_type(ner_label)
            stakeholder_id = self._get_stakeholder_id(entity_text, stakeholder_type)
            
            if not stakeholder_id:
                skipped_count += 1
                continue  # Skip if stakeholder not found in database
            
            # Find all chunks that contain this entity text
            # Since we're using PDF for chunking but entities from markdown,
            # we search for entity text in each chunk
            for i, chunk_record in chunk_records.items():
                chunk = chunk_record['chunk']
                chunk_text = chunk['text']
                
                # Check if entity text appears in this chunk (case-insensitive for better matching)
                entity_text_lower = entity_text.lower()
                chunk_text_lower = chunk_text.lower()
                
                if entity_text_lower in chunk_text_lower:
                    # Find the actual position in the chunk (preserve original case)
                    # Try to find exact match first, then case-insensitive
                    if entity_text in chunk_text:
                        # Find all occurrences in this chunk
                        start_idx = 0
                        while True:
                            pos = chunk_text.find(entity_text, start_idx)
                            if pos == -1:
                                break
                            
                            # Create a ChunkStakeholder for each occurrence
                            try:
                                self._create_chunk_stakeholder(
                                    chunk_id=chunk_record['chunk_id'],
                                    stakeholder_id=stakeholder_id,
                                    entity=entity,  # Contains confidence score
                                    mention_text=entity_text,  # The text of the entity in this chunk
                                    chunk_bbox=chunk_record.get('bbox'),
                                    page=chunk_record['page']
                                )
                                cs_count += 1
                            except Exception as e:
                                self._print(f"  [!] Error creating ChunkStakeholder for '{entity_text}': {e}")
                            
                            start_idx = pos + 1
                    else:
                        # Case-insensitive match - find the actual text in chunk
                        pos = chunk_text_lower.find(entity_text_lower)
                        if pos != -1:
                            # Extract the actual text from chunk (preserving original case)
                            mention_text = chunk_text[pos:pos+len(entity_text)]
                            try:
                                self._create_chunk_stakeholder(
                                    chunk_id=chunk_record['chunk_id'],
                                    stakeholder_id=stakeholder_id,
                                    entity=entity,
                                    mention_text=mention_text,
                                    chunk_bbox=chunk_record.get('bbox'),
                                    page=chunk_record['page']
                                )
                                cs_count += 1
                            except Exception as e:
                                self._print(f"  [!] Error creating ChunkStakeholder for '{entity_text}': {e}")
        
        self._print(f"\n✓ Created {cs_count} ChunkStakeholder records")
        if skipped_count > 0:
            self._print(f"  [!] Skipped {skipped_count} entities (stakeholder not found in database)")
        
        result = {
            "chunks_created": len(chunk_records),
            "chunk_stakeholders_created": cs_count,
            "entities_skipped": skipped_count
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
                ner_label = entity.get('label', '')
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
            "stakeholders_total": stats["total"]
        }
        
        if create_chunks:
            chunk_stats = self.populate_chunks_and_entities()
            result.update({
                "chunks_created": chunk_stats["chunks_created"],
                "chunk_stakeholders_created": chunk_stats["chunk_stakeholders_created"],
                "entities_skipped_for_chunks": chunk_stats["entities_skipped"]
            })
        
        return result
    
    def __del__(self):
        """Clean up resources."""
        if hasattr(self, 'pdf_doc') and self.pdf_doc is not None:
            try:
                self.pdf_doc.close()
            except:
                pass


def main():
    """Example usage of the MarkdownNERProcessor class."""
    
    file_path = "news_en.md"
    
    # Create processor instance
    processor = MarkdownNERProcessor(
        markdown_path=file_path,
        entity_types=None,  # Extract all entity types
        stakeholder_types_to_save=["person", "organization"],  # Only save persons and organizations
        min_confidence=0.5,
        model_type="xlm-roberta",
        model_name="Davlan/xlm-roberta-base-ner-hrl",
        verbose=True,
        # pdf_path="path/to/corresponding.pdf"  # Optional: provide PDF for bounding boxes
    )
    
    # Process the markdown file
    results = processor.process()
    
    print("\nProcessing complete!")
    print(f"Results: {results}")


if __name__ == "__main__":
    main()

