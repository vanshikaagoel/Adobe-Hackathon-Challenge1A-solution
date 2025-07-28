import fitz  # PyMuPDF
import json

def extract_from_toc(doc: fitz.Document):
    """
    Extracts the outline from the PDF's machine-readable Table of Contents (bookmarks).
    This is the most reliable method if available.

    Args:
        doc: The PyMuPDF document object.

    Returns:
        A list of outline items if a TOC is found, otherwise an empty list.
    """
    toc = doc.get_toc()

    if not toc:
        return []

    print(f"Success: Found a machine-readable Table of Contents with {len(toc)} entries.")
    
    outline = []
    for level, title, page_num in toc:
        outline.append({
            "level": f"H{level}",
            "text": title,
            "page": page_num - 1
        })
        
    return outline

