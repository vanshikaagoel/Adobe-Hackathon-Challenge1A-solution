import fitz  # PyMuPDF
import re
from utils import stitch_text_lines

def _get_sample_pages(doc: fitz.Document):
    """
    Stage 1: Defines the analysis scope by selecting pages.
    Selects a small, representative sample from long documents.
    """
    page_count = doc.page_count
    if page_count <= 3:
        # Analyze all pages for short documents
        return [doc[i] for i in range(page_count)]

    # Strategic sample for long documents as per the algorithm
    sample_indices = {0, 1, page_count // 2, page_count - 1}
    return [doc[i] for i in sorted(list(sample_indices))]

def classify_document(doc: fitz.Document):
    """
    Classifies a PDF as "Regular" or "Flyer" using the high-speed
    Prioritized Two-Stage Process (V2.0).

    Args:
        doc: The PyMuPDF document object.

    Returns:
        A string, either "Regular" or "Flyer".
    """
    print("Step 1: Classifying document with high-speed algorithm V2.0...")
    
    # --- Stage 1: Define Analysis Scope ---
    sample_pages = _get_sample_pages(doc)
    sample_text = ""
    all_lines = []
    for page in sample_pages:
        lines = stitch_text_lines(page)
        all_lines.extend(lines)
        sample_text += page.get_text().lower()

    # --- Stage 2: Apply Prioritized Classification Rules ---

    # *** Priority 1: Identify Transactional Documents (Form Check) ***
    has_input_fields = any(line['text'].strip().endswith(':') or '____' in line['text'] for line in all_lines)
    declaration_keywords = ["i declare that", "i undertake to", "signature:"]
    has_declaration = any(keyword in sample_text for keyword in declaration_keywords)

    if has_input_fields and has_declaration:
        print("Info: Found input fields and declaration. Classified as 'Regular' (Form).")
        return "Regular"

    # *** Priority 2: Score for Flyer Characteristics ***
    print("Info: Document not identified as a form. Proceeding to Flyer scoring.")
    score = 0
    
    if doc.page_count <= 2: score += 1
    if "table of contents" not in sample_text and "appendix" not in sample_text: score += 1

    promo_keywords = ["rsvp", "visit website", "you're invited", "party", "conference and awards"]
    if any(keyword in sample_text for keyword in promo_keywords): score += 2
        
    font_sizes = [line['size'] for line in all_lines if line['size'] > 0]
    if font_sizes and (max(font_sizes) / min(font_sizes) > 3): score += 1

    if score >= 3:
        print(f"Info: Flyer score is {score} (>=3). Classified as 'Flyer'.")
        return "Flyer"
    else:
        print(f"Info: Flyer score is {score} (<3). Classified as 'Regular'.")
        return "Regular"

