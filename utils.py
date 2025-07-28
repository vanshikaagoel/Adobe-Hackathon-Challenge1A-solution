import fitz  # PyMuPDF
from collections import Counter
import re

def is_coherent_text(text: str) -> bool:
    """
    Performs a lightweight, language-agnostic sanity check to see if a string
    is likely to be coherent language rather than random characters or junk.

    Args:
        text: The string to check.

    Returns:
        True if the text seems coherent, False otherwise.
    """
    text = text.strip()
    if len(text) < 3:
        return True # Too short to judge, assume it's okay (e.g., "A.")

    words = text.split()
    num_words = len(words)

    # 1. Check for unnatural repetition of short words
    if num_words > 2:
        short_words = [w for w in words if len(w) <= 3]
        if len(short_words) > 0:
            short_word_counts = Counter(short_words)
            most_common = short_word_counts.most_common(1)[0]
            if most_common[1] / num_words > 0.5: # If one short word is >50% of all words
                return False

    # 2. Check average word length
    avg_word_len = sum(len(w) for w in words) / num_words
    if avg_word_len < 2.5 and num_words > 4:
        return False

    # 3. Check for a reasonable vowel-to-consonant ratio (works for many languages)
    vowels = "aeiouAEIOU"
    num_vowels = sum(1 for char in text if char in vowels)
    num_consonants = sum(1 for char in text if char.isalpha() and char not in vowels)
    if num_consonants > 0 and num_vowels / num_consonants < 0.1:
        return False

    return True


def stitch_text_lines(page: fitz.Page):
    """
    Robustly stitches text spans into coherent lines, now with a final
    linguistic sanity check to filter out junk.
    """
    lines = []
    blocks = page.get_text("dict")["blocks"]
    for b in blocks:
        if b['type'] == 0:  # This is a text block
            for l in b["lines"]:
                line_text = "".join(s["text"] for s in l["spans"]).strip()
                if not line_text:
                    continue
                
                # *** NEW: Apply the linguistic sanity check ***
                if not is_coherent_text(line_text):
                    print(f"Info: Filtering out incoherent line: '{line_text}'")
                    continue

                bbox = fitz.Rect(l['bbox'])
                font_sizes = [s["size"] for s in l["spans"]]
                avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 0
                is_bold = any('bold' in s['font'].lower() for s in l['spans'])
                page_width = page.rect.width
                center_x = (bbox.x0 + bbox.x1) / 2
                is_centered = abs(center_x - page_width / 2) < (page_width * 0.1)

                lines.append({
                    "text": line_text,
                    "bbox": bbox,
                    "size": avg_font_size,
                    "bold": is_bold,
                    "centered": is_centered,
                })
    return lines


def detect_repeating_headers_footers(doc: fitz.Document, sample_pages=5):
    """Detects repeating text elements that are likely headers or footers."""
    if doc.page_count <= 3:
        return []

    num_pages_to_check = min(sample_pages, doc.page_count)
    
    page_lines = {}
    for i in range(num_pages_to_check):
        page = doc[i]
        page_lines[i] = stitch_text_lines(page)

    all_text = [line['text'].strip() for lines in page_lines.values() for line in lines if line['text'].strip()]
    text_counts = Counter(all_text)
    
    common_texts = {text for text, count in text_counts.items() if count > num_pages_to_check / 2}
    
    ignored_bboxes = []
    for text in common_texts:
        if not re.search(r'[a-zA-Z]', text):
            continue
            
        for lines in page_lines.values():
            for line in lines:
                if line['text'].strip() == text:
                    ignored_bboxes.append(line['bbox'])
    
    if ignored_bboxes:
        print(f"Info: Detected {len(set(common_texts))} potential header/footer text(s) to ignore.")

    return ignored_bboxes

