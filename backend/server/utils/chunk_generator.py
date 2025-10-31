import random
import uuid
from typing import List, Dict, Any
from datetime import datetime


DEFAULT_PDF_WIDTH = 612
DEFAULT_PDF_HEIGHT = 792


FAKE_CONTEXTS = [
    "De gemeente heeft besloten om een nieuwe vergunning te verlenen voor de bouw van een windmolenpark.",
    "Tijdens de openbare raadpleging hebben verschillende belanghebbenden hun zorgen geuit over het milieu.",
    "Het project zal naar verwachting worden voltooid in de tweede helft van 2024.",
    "Stakeholders uit de lokale gemeenschap hebben aangegeven graag betrokken te willen zijn bij de besluitvorming.",
    "De impactstudie toont aan dat er minimale gevolgen zijn voor de omgeving.",
    "De ontwikkelaar heeft beloofd om compenserende maatregelen te treffen voor natuurbehoud.",
    "Er zijn verschillende opties overwogen voordat de definitieve keuze is gemaakt.",
    "De vergadering werd bijgewoond door vertegenwoordigers van verschillende organisaties.",
    "Het voorstel zal worden voorgelegd aan de gemeenteraad voor goedkeuring.",
    "Feedback van burgers is verzameld via een online platform en openbare bijeenkomsten.",
]


STAKEHOLDER_TYPES = [
    "organization",
    "individual",
    "government",
    "community",
    "environmental",
]


STAKEHOLDER_NAMES = [
    "Gemeente Amsterdam",
    "Provincie Noord-Holland",
    "Natuurmonumenten",
    "Omgevingsdienst",
    "Bewonersvereniging",
    "Milieudefensie",
    "Bouwbedrijf BV",
    "Architectenbureau",
    "Waterschap",
    "Tegenwind Collectief",
    "Lokale ondernemers",
    "Scholenvereniging",
]


CONTACT_INFO_TEMPLATES = [
    "info@{name}.nl",
    "contact@{name}.nl",
    "post@{name}.org",
]


def generate_fake_chunks(document_id: str, num_pages: int = 1) -> List[Dict[str, Any]]:
    """
    Generate fake chunks with random bounding boxes for a document.

    Args:
        document_id: The document ID to associate chunks with
        num_pages: Number of pages in the document (default: 1)

    Returns:
        List of chunk dictionaries ready for database insertion
    """
    chunks = []
    now = datetime.now().isoformat() + "Z"

    for page_num in range(1, num_pages + 1):
        num_chunks = random.randint(3, 5)

        for _ in range(num_chunks):
            chunk_id = f"chunk_{uuid.uuid4().hex[:8]}"

            x = random.randint(50, int(DEFAULT_PDF_WIDTH * 0.6))
            y = random.randint(50, int(DEFAULT_PDF_HEIGHT * 0.7))
            width = random.randint(200, int(DEFAULT_PDF_WIDTH * 0.8))
            height = random.randint(50, 150)

            if x + width > DEFAULT_PDF_WIDTH:
                width = DEFAULT_PDF_WIDTH - x - 10
            if y + height > DEFAULT_PDF_HEIGHT:
                height = DEFAULT_PDF_HEIGHT - y - 10

            chunk = {
                "id": chunk_id,
                "document_id": document_id,
                "page": page_num,
                "context": random.choice(FAKE_CONTEXTS),
                "bbox": {
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                },
                "created_at": now,
            }
            chunks.append(chunk)

    return chunks


def generate_fake_stakeholders(num_stakeholders: int = 5) -> List[Dict[str, Any]]:
    """
    Generate fake stakeholders.

    Args:
        num_stakeholders: Number of stakeholders to generate (default: 5)

    Returns:
        List of stakeholder dictionaries ready for database insertion
    """
    stakeholders = []
    now = datetime.now().isoformat() + "Z"

    used_names = set()

    for _ in range(num_stakeholders):
        stakeholder_id = f"stakeholder_{uuid.uuid4().hex[:8]}"

        name = random.choice(STAKEHOLDER_NAMES)
        while name in used_names:
            name = random.choice(STAKEHOLDER_NAMES)
        used_names.add(name)

        stakeholder_type = random.choice(STAKEHOLDER_TYPES)

        contact_name = name.lower().replace(" ", "").replace("bv", "")
        contact_info = random.choice(CONTACT_INFO_TEMPLATES).format(name=contact_name)

        stakeholder = {
            "id": stakeholder_id,
            "type": stakeholder_type,
            "name": name,
            "contact_info": contact_info,
            "created_at": now,
            "updated_at": now,
        }
        stakeholders.append(stakeholder)

    return stakeholders


def generate_fake_chunk_stakeholders(
    chunks: List[Dict[str, Any]],
    stakeholders: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Generate fake chunk-stakeholder relationships.

    Each chunk can have 0-3 stakeholder mentions, and stakeholders can appear
    in multiple chunks.

    Args:
        chunks: List of chunk dictionaries
        stakeholders: List of stakeholder dictionaries

    Returns:
        List of chunk-stakeholder relationship dictionaries ready for database insertion
    """
    chunk_stakeholders = []
    now = datetime.now().isoformat() + "Z"

    if not stakeholders:
        return chunk_stakeholders

    for chunk in chunks:
        num_mentions = random.randint(0, 3)

        selected_stakeholders = random.sample(stakeholders, min(num_mentions, len(stakeholders)))

        for stakeholder in selected_stakeholders:
            mention_id = f"mention_{uuid.uuid4().hex[:8]}"

            chunk_bbox = chunk["bbox"]
            mention_x = chunk_bbox["x"] + random.randint(0, max(0, chunk_bbox["width"] - 100))
            mention_y = chunk_bbox["y"] + random.randint(0, max(0, chunk_bbox["height"] - 20))
            mention_width = random.randint(80, min(150, chunk_bbox["width"]))
            mention_height = random.randint(15, 25)

            if mention_x + mention_width > chunk_bbox["x"] + chunk_bbox["width"]:
                mention_width = (chunk_bbox["x"] + chunk_bbox["width"]) - mention_x
            if mention_y + mention_height > chunk_bbox["y"] + chunk_bbox["height"]:
                mention_height = (chunk_bbox["y"] + chunk_bbox["height"]) - mention_y

            chunk_stakeholder = {
                "id": mention_id,
                "chunk_id": chunk["id"],
                "stakeholder_id": stakeholder["id"],
                "confidence": round(random.uniform(0.6, 0.95), 2),
                "mention_text": stakeholder["name"],
                "mention_bbox": {
                    "x": mention_x,
                    "y": mention_y,
                    "width": mention_width,
                    "height": mention_height,
                },
                "verified": random.choice([True, False]),
                "created_at": now,
            }
            chunk_stakeholders.append(chunk_stakeholder)

    return chunk_stakeholders
