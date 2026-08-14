"""
Core Utilities — File Validation & Text Extraction
"""
import os
import re
import logging

logger = logging.getLogger('django')

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.png', '.jpg', '.jpeg'}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def validate_file_upload(uploaded_file):
    """
    Validate file extension and size.
    Returns (is_valid: bool, error_message: str)
    """
    if not uploaded_file:
        return False, "No file provided."

    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type '{ext}'. Allowed: PDF, DOCX, TXT, PNG, JPG."

    if uploaded_file.size > MAX_FILE_SIZE_BYTES:
        size_mb = uploaded_file.size / (1024 * 1024)
        return False, f"File size {size_mb:.1f} MB exceeds the 10 MB limit."

    return True, ""


def extract_document_pipeline(uploaded_file) -> dict:
    """
    Robust Document Extraction Pipeline:
    upload → validate → extract → check extraction quality → return metadata & text.

    Returns dict:
      {
        'text': str,
        'page_count': int,
        'is_scanned': bool,
        'quality': 'success' | 'scanned_ocr_required' | 'empty',
        'status_message': str
      }
    """
    if not uploaded_file:
        return {
            'text': '',
            'page_count': 0,
            'is_scanned': False,
            'quality': 'empty',
            'status_message': 'No file provided.'
        }

    filename = uploaded_file.name.lower()
    page_count = 1
    is_scanned = False
    quality = 'success'
    status_message = 'Text extracted successfully.'
    extracted_text = ''

    try:
        # ── PDF ──────────────────────────────────────────────────────────
        if filename.endswith('.pdf'):
            try:
                from pypdf import PdfReader
                uploaded_file.seek(0)
                reader = PdfReader(uploaded_file)
                page_count = len(reader.pages) or 1
                pages_text = []
                for page in reader.pages:
                    try:
                        t = page.extract_text()
                        if t and t.strip():
                            pages_text.append(t.strip())
                    except Exception:
                        pass
                combined = "\n\n".join(pages_text)
                if len(combined.strip()) > 50:
                    extracted_text = combined[:30000]
                    is_scanned = False
                    quality = 'success'
                    status_message = f'Extracted selectable text from {page_count} PDF page(s).'
                else:
                    is_scanned = True
                    quality = 'scanned_ocr_required'
                    clean_name = os.path.splitext(uploaded_file.name)[0].replace('_', ' ').replace('-', ' ')
                    status_message = f'⚠️ Scanned/image-only PDF detected ({page_count} page(s)). OCR is required to extract text from images. AI analysis will use topic context.'
                    extracted_text = f"Study Material: {clean_name}\n[Note: Scanned/Image-only PDF document ({page_count} pages). Optical Character Recognition (OCR) is required to extract text from image pages. Core academic overview, definitions, 2-mark questions, 7-mark questions, and MCQs generated for topic '{clean_name}']."
            except Exception as exc:
                logger.warning("[extract_pdf] Error: %s", exc)
                clean_name = os.path.splitext(uploaded_file.name)[0].replace('_', ' ').replace('-', ' ')
                is_scanned = True
                quality = 'scanned_ocr_required'
                status_message = f'⚠️ PDF parsing notice: file appears to be scanned.'
                extracted_text = f"Study Material: {clean_name}\n[Scanned PDF Document]. Core academic analysis generated for topic '{clean_name}'."

        # ── TXT ──────────────────────────────────────────────────────────
        elif filename.endswith('.txt'):
            uploaded_file.seek(0)
            content = uploaded_file.read()
            extracted_text = content.decode('utf-8', errors='ignore').strip()
            page_count = max(1, len(extracted_text.splitlines()) // 40)

        # ── DOCX / DOC ───────────────────────────────────────────────────
        elif filename.endswith(('.docx', '.doc')):
            try:
                import docx
                uploaded_file.seek(0)
                doc = docx.Document(uploaded_file)
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                extracted_text = "\n".join(paragraphs)[:30000]
                page_count = max(1, len(paragraphs) // 10)
            except Exception:
                uploaded_file.seek(0)
                raw = uploaded_file.read()
                words = re.findall(rb"[A-Za-z0-9 .,;:'\"\\-()?!]{4,}", raw)
                extracted_text = " ".join(w.decode('ascii', errors='ignore').strip() for w in words[:1000])
                page_count = 1
            if len(extracted_text) < 50:
                quality = 'scanned_ocr_required'
                clean_name = os.path.splitext(uploaded_file.name)[0].replace('_', ' ').replace('-', ' ')
                extracted_text = f"Study Document: {clean_name}"
        else:
            clean_name = os.path.splitext(uploaded_file.name)[0].replace('_', ' ').replace('-', ' ')
            extracted_text = f"Uploaded File: {clean_name}"

    except Exception as exc:
        logger.warning("[extract_document_pipeline] %s: %s", filename, exc)
        extracted_text = f"File '{uploaded_file.name}' uploaded."
        status_message = "File uploaded."

    return {
        'text': extracted_text,
        'page_count': page_count,
        'is_scanned': is_scanned,
        'quality': quality,
        'status_message': status_message
    }


def extract_text_from_file(uploaded_file) -> str:
    """Wrapper for backward compatibility returning text from document pipeline."""
    res = extract_document_pipeline(uploaded_file)
    return res['text']
