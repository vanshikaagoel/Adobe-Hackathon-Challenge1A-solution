import fitz  # PyMuPDF

def extract_from_metadata(doc: fitz.Document):
    """
    Extracts the title from the PDF's hidden metadata.
    This is used as a last-resort fallback.

    Args:
        doc: The PyMuPDF document object.

    Returns:
        The title string if found, otherwise an empty string.
    """
    # Filter out common non-titles or filenames.
    generic_titles = ['untitled', 'title']
    bad_extensions = ['.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.cdr']
    title = doc.metadata.get('title', '').strip()
    title_lower = title.lower()

    if title_lower in generic_titles or any(ext in title_lower for ext in bad_extensions):
        print(f"Info: Ignoring generic or filename-based metadata title: '{title}'")
        return ""

    if title:
        print(f"Success: Found valid metadata title: '{title}'")
    else:
        print("Info: No title found in metadata.")
        
    return title

