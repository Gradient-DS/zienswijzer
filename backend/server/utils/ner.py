from typing import List, Dict, Tuple, Optional
import spacy
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
def extract_entities_xlm_roberta(
    text: str,
    entity_types: Optional[List[str]],
    min_confidence: float,
    model_name: str = "Davlan/xlm-roberta-base-ner-hrl"
) -> List[Dict]:
    # Read the text file
    # Perform NER
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(model_name)
    # Create NER pipeline
    ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple", device=-1)
    ner_results = ner_pipeline(text)
    # Convert results to desired format
    entities = []
    for ent in ner_results:
        entity_dict = {
            "text": ent["word"],
            "label": ent["entity_group"],  # entity_group is used when aggregation_strategy="simple"
            "start": ent["start"],
            "end": ent["end"],
            "confidence": ent["score"]
        }
        entities.append(entity_dict)
    return entities
def extract_entities_bert(
    text: str,
    entity_types: Optional[List[str]],
    min_confidence: float,
    model_name: str = "dslim/bert-base-NER"
) -> List[Dict]:
    # Perform NER using BERT
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(model_name)
    # Create NER pipeline
    ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple", device=-1)
    ner_results = ner_pipeline(text)
    # Convert results to desired format
    entities = []
    for ent in ner_results:
        entity_dict = {
            "text": ent["word"],
            "label": ent["entity_group"],  # entity_group is used when aggregation_strategy="simple"
            "start": ent["start"],
            "end": ent["end"],
            "confidence": ent["score"]
        }
        entities.append(entity_dict)
    return entities
def extract_entities_spacy(
    text: str,
    entity_types: Optional[List[str]],
    min_confidence: float,
    model_name: str = "en_core_web_trf"
) -> List[Dict]:
    nlp = spacy.load(model_name)
    print(f"Loaded spaCy model: {model_name}")
    doc = nlp(text)
    entities: List[Dict] = []
    for ent in doc.ents:
        if entity_types and ent.label_ not in entity_types:
            continue
        confidence = 0.6
        entities.append({
            'text': ent.text.strip(),
            'label': ent.label_,
            'start': ent.start_char,
            'end': ent.end_char,
            'confidence': float(confidence),
        })
    return entities
# optional: split very long paragraphs into ~100 word chunks
def split_long_chunk(chunk, max_words=100):
    words = chunk.split()
    for i in range(0, len(words), max_words):
        yield " ".join(words[i:i+max_words])
def extract_entities_robbert(
    text: str,
    entity_types: Optional[List[str]],
    min_confidence: float,
    model_name: str = "pdelobelle/robbert-v2-dutch-ner"
) -> List[Dict]:
    """
    Extract entities using RobBERT model with text chunking to handle long documents.
    This method specifically handles the tensor size mismatch issues that occur with RobBERT.
    """
    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
    model = AutoModelForTokenClassification.from_pretrained(model_name)
    # Create NER pipeline
    ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple", device=-1)
    # Handle long texts by chunking
    max_length = 512  # Standard BERT/RoBERTa max length
    entities = []
    # Estimate chunk size (roughly 4 characters per token)
    chunk_size = max_length * 4
    if len(text) <= chunk_size:
        # Process entire text at once
        try:
            ner_results = ner_pipeline(text)
            for ent in ner_results:
                entity_dict = {
                    "text": ent["word"],
                    "label": ent["entity_group"],
                    "start": ent["start"],
                    "end": ent["end"],
                    "confidence": ent["score"]
                }
                entities.append(entity_dict)
        except Exception as e:
            print(f"Error processing full text with RobBERT: {e}")
            print("Falling back to chunked processing...")
            # Fall back to chunking
            text_chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            for chunk_idx, chunk in enumerate(text_chunks):
                try:
                    ner_results = ner_pipeline(chunk)
                    offset = chunk_idx * chunk_size
                    for ent in ner_results:
                        # Handle None values for start/end positions
                        start_pos = ent["start"] + offset if ent["start"] is not None else None
                        end_pos = ent["end"] + offset if ent["end"] is not None else None
                        entity_dict = {
                            "text": ent["word"],
                            "label": ent["entity_group"],
                            "start": start_pos,
                            "end": end_pos,
                            "confidence": ent["score"]
                        }
                        entities.append(entity_dict)
                except Exception as chunk_e:
                    print(f"Error processing chunk {chunk_idx}: {chunk_e}")
                    continue
    else:
        # Process in chunks from the start
        print(f"Text too long ({len(text)} chars), processing in chunks...")
        text_chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        for chunk_idx, chunk in enumerate(text_chunks):
            try:
                ner_results = ner_pipeline(chunk)
                offset = chunk_idx * chunk_size
                for ent in ner_results:
                    # Handle None values for start/end positions
                    start_pos = ent["start"] + offset if ent["start"] is not None else None
                    end_pos = ent["end"] + offset if ent["end"] is not None else None
                    entity_dict = {
                        "text": ent["word"],
                        "label": ent["entity_group"],
                        "start": start_pos,
                        "end": end_pos,
                        "confidence": ent["score"]
                    }
                    entities.append(entity_dict)
            except Exception as chunk_e:
                print(f"Error processing chunk {chunk_idx}: {chunk_e}")
                continue
    print(f"RobBERT extracted {len(entities)} entities")
    return entities
def extract_entities_from_text(
    text: str,
    entity_types: Optional[List[str]] = None,
    min_confidence: float = 0.5,
    model_type: str = "spacy",
    model_name: str = "en_core_web_trf"
) -> List[Dict]:
    if model_type == "spacy":
        return extract_entities_spacy(text, entity_types, min_confidence, model_name)
    elif model_type == "bert":
        return extract_entities_bert(text, entity_types, min_confidence, model_name)
    elif model_type == "xlm-roberta":
        return extract_entities_xlm_roberta(text, entity_types, min_confidence, model_name)
    elif model_type == "robbert":
        return extract_entities_robbert(text, entity_types, min_confidence, model_name)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")