import fitz  # PyMuPDF
import re
import json
from collections import Counter
from utils import stitch_text_lines

def _parse_visual_toc(page: fitz.Page):
    """
    Parses a page that is visually identified as a Table of Contents using a more
    flexible regex that handles different separators.
    """
    outline = []
    lines = stitch_text_lines(page)
    
    # More flexible regex: looks for section, text, then a wide gap or many dots, then a page number.
    toc_pattern = re.compile(
        r"^(?P<section>[\d\.]*\s*)?"       # Optional section number
        r"(?P<text>.+?)"                  # The heading text
        r"(?:\s*\.{3,}\s*|\s{4,})"         # Separator: 3+ dots OR 4+ spaces
        r"(?P<page>\d+)\s*$"              # The page number
    )

    for line in lines:
        match = toc_pattern.match(line['text'])
        if match:
            data = match.groupdict()
            section_str = (data.get('section') or "").strip()
            level = section_str.count('.') + 1 if section_str else 1
            
            outline.append({
                "level": f"H{level}",
                "text": data['text'].strip(),
                "page": int(data['page'])
            })
            
    if outline:
        print(f"Success: Parsed {len(outline)} entries from visual Table of Contents.")
    return outline


def _extract_by_rule_based_scoring(doc: fitz.Document, ignored_bboxes=None, title_text=""):
    """
    Extracts an outline using a more nuanced scoring model with negative filters.
    """
    all_lines = []
    if ignored_bboxes is None:
        ignored_bboxes = []

    for page_num, page in enumerate(doc):
        page_lines = stitch_text_lines(page)
        for line in page_lines:
            is_ignored = any(line['bbox'].intersects(ignored_box) for ignored_box in ignored_bboxes)
            if not is_ignored and line['text'].strip().lower() != title_text.lower().strip():
                line['page'] = page_num + 1
                all_lines.append(line)

    if not all_lines: return []

    font_sizes = [line['size'] for line in all_lines if line['text'].strip()]
    if not font_sizes: return []
    body_size = Counter(round(s) for s in font_sizes).most_common(1)[0][0]

    scored_lines = []
    for line in all_lines:
        score = 0
        text = line['text'].strip()
        
        # --- Negative Filters (what is NOT a heading) ---
        if 'www.' in text.lower() or '.com' in text.lower() or re.match(r'^-+$', text):
            continue
        if text.endswith(":") and len(text) < 30: # Likely a form field
            continue

        # --- Positive Scoring ---
        if line['size'] > body_size + 0.5:
            score += (line['size'] - body_size)
            if line['bold']: score += 5
            if line['centered']: score += 5
            if re.match(r"^(?:[IVX\d]+[\.\)]|\w\.)", text, re.IGNORECASE): score += 10 # "1.", "A.", "IV."
            if text.isupper() and len(text.split()) < 7: score += 5
            if len(text) > 120 or text.endswith('.'): score -= 10

        if score > 5:
            line['score'] = score
            scored_lines.append(line)

    if not scored_lines: return []

    scores = sorted(list(set([line['score'] for line in scored_lines])), reverse=True)
    score_to_level = {score: f"H{i+1}" for i, score in enumerate(scores[:4])}

    final_outline = []
    for line in scored_lines:
        if line['score'] in score_to_level:
            final_outline.append({
                "level": score_to_level[line['score']],
                "text": line['text'].strip(),
                "page": line['page']
            })
            
    print(f"Success: Extracted {len(final_outline)} headings using rule-based scoring.")
    return final_outline


def extract_outline(doc: fitz.Document, ignored_bboxes=None, title_text=""):
    """Main outline extraction orchestrator."""
    print("Step 5a: Searching for a visual Table of Contents page...")
    for i in range(min(doc.page_count, 10)):
        page = doc[i]
        if "table of contents" in page.get_text().lower():
            print(f"Info: Found 'Table of Contents' on page {i+1}. Attempting to parse.")
            visual_outline = _parse_visual_toc(page)
            if visual_outline:
                return visual_outline
    
    print("Step 5b: No visual ToC found. Falling back to rule-based heading detection...")
    return _extract_by_rule_based_scoring(doc, ignored_bboxes, title_text)

