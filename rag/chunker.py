"""
Hierarchical Chunker — Splits policy PDFs into multi-level chunks.
Level 1: Document metadata
Level 2: Section/chapter splits
Level 3: Paragraph-level chunks with overlap
Each chunk carries parent context for richer retrieval.
"""
import re
import fitz
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from monitoring.logger import get_logger
from config.settings import POLICY_PDFS, CHUNK_SIZE, CHUNK_OVERLAP

log = get_logger("rag.chunker")


def _extract_text_from_pdf(pdf_path: Path) -> str:
    try:
        doc = fitz.open(str(pdf_path))
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as exc:
        log.error("Failed to extract text from %s: %s", pdf_path.name, exc)
        raise


def _split_into_sections(text: str) -> list[dict]:
    section_pattern = re.compile(
        r"(?:^|\n)((?:Chapter|Section|CHAPTER|SECTION|Part|PART)\s+[\dIVXLCDM]+[^\n]*)",
        re.IGNORECASE,
    )
    splits = section_pattern.split(text)

    sections = []
    current_title = "Introduction"

    for i, part in enumerate(splits):
        part = part.strip()
        if not part:
            continue
        if section_pattern.match(part):
            current_title = part[:100]
        else:
            sections.append({"title": current_title, "text": part})

    if not sections:
        sections.append({"title": "Full Document", "text": text})

    return sections


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def hierarchical_chunk(pdf_paths: list[Path] = None) -> list[dict]:
    if pdf_paths is None:
        pdf_paths = POLICY_PDFS

    all_chunks = []
    for pdf_path in pdf_paths:
        log.info("Chunking: %s", pdf_path.name)
        raw_text = _extract_text_from_pdf(pdf_path)
        sections = _split_into_sections(raw_text)

        for section in sections:
            paragraphs = _chunk_text(section["text"], CHUNK_SIZE, CHUNK_OVERLAP)
            for idx, para in enumerate(paragraphs):
                all_chunks.append({
                    "document": pdf_path.name,
                    "section": section["title"],
                    "chunk_index": idx,
                    "text": para,
                    "metadata": {
                        "source": pdf_path.name,
                        "section": section["title"],
                        "level": "paragraph",
                    },
                })

    log.info("Total chunks created: %d", len(all_chunks))
    return all_chunks


if __name__ == "__main__":
    chunks = hierarchical_chunk()
    print(f"Total chunks: {len(chunks)}")
    if chunks:
        print(f"Sample: {chunks[0]['text'][:200]}...")
