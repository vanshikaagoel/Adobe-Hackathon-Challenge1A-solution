import fitz  # PyMuPDF
from utils import stitch_text_lines

def extract_title(doc: fitz.Document, ignored_bboxes=None):
    """
    Detects the document title using prominence-based heuristics on the first page.
    It now uses robust stitched lines and aggressively combines prominent,
    vertically-stacked lines into a single title.
    """
    print("Step 4: Trying to extract title by prominence (heuristic)...")
    if doc.page_count == 0:
        return ""

    first_page = doc[0]
    lines = stitch_text_lines(first_page)
    
    if ignored_bboxes:
        lines = [
            line for line in lines 
            if not any(line['bbox'].intersects(ignored_box) for ignored_box in ignored_bboxes)
        ]

    # Score each line for prominence
    scored_lines = []
    for line in lines:
        text = line['text'].strip()
        if not text or len(text) < 4:
            continue

        score = line['size']
        if line['bold']:
            score *= 1.5
        
        page_height = first_page.rect.height
        if line['bbox'].y1 < page_height * 0.5: # Bonus for being in top half
            score *= 1.5
        
        line['score'] = score
        scored_lines.append(line)

    if not scored_lines:
        return ""

    scored_lines.sort(key=lambda x: x['score'], reverse=True)
    
    # Group the top 3 most prominent lines if they are stacked together
    top_lines = scored_lines[:3]
    top_lines.sort(key=lambda x: x['bbox'].y0) # Sort by vertical position

    final_title_lines = []
    if top_lines:
        final_title_lines.append(top_lines[0])
        last_line = top_lines[0]
        
        for i in range(1, len(top_lines)):
            current_line = top_lines[i]
            vertical_gap = current_line['bbox'].y0 - last_line['bbox'].y1
            # If gap is small, it's likely part of the same title block
            if vertical_gap < (last_line['size']):
                final_title_lines.append(current_line)
                last_line = current_line

    potential_title = " ".join([line['text'] for line in final_title_lines])

    print(f"Success: Found potential title by prominence: '{potential_title}'")
    return potential_title

