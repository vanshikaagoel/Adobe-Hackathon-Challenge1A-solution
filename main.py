import fitz  # PyMuPDF
import json
import os
import time
from multiprocessing import Pool, cpu_count

# Import all our modules
from utils import detect_repeating_headers_footers
from classifier import classify_document
from toc_extractor import extract_from_toc
from metadata_extractor import extract_from_metadata
from title_extractor import extract_title as extract_title_by_prominence
from outline_extractor import extract_outline as extract_outline_by_rules

# Define the fixed directories for Docker
INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"

def process_pdf(pdf_path: str):
    """
    Main execution function for a single PDF file.
    It now returns the final JSON data instead of writing it to a file.
    """
    print(f"--- Starting PDF Extraction for: {os.path.basename(pdf_path)} ---")
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"CRITICAL ERROR opening {pdf_path}: {e}")
        return None

    # Phase 1: Classification and Pre-processing
    doc_type = classify_document(doc)
    ignored_bboxes = detect_repeating_headers_footers(doc)
    
    # Phase 2: Adaptive Extraction
    final_outline = extract_from_toc(doc)
    prominent_title = extract_title_by_prominence(doc, ignored_bboxes)
    
    if not final_outline:
        final_outline = extract_outline_by_rules(doc, ignored_bboxes, prominent_title)

    if doc_type == "Regular":
        final_title = prominent_title or extract_from_metadata(doc)
    else:
        final_title = ""

    # Phase 3: Post-Processing and Cleanup
    if doc_type == "Flyer" and not final_title and len(final_outline) == 1:
        final_title = final_outline.pop(0)['text']
    
    if final_outline and prominent_title and (final_outline[0]['text'].lower().strip() == prominent_title.lower().strip()):
        final_outline.pop(0)
    
    doc.close()

    return {
        "title": final_title.strip(),
        "outline": final_outline
    }

def process_file_wrapper(pdf_filename):
    """
    A wrapper function for the multiprocessing pool. It handles the full
    process for one file, from reading to writing the final JSON.
    """
    input_pdf_path = os.path.join(INPUT_DIR, pdf_filename)
    output_json_path = os.path.join(OUTPUT_DIR, os.path.splitext(pdf_filename)[0] + ".json")

    start_time = time.time()
    result_data = process_pdf(input_pdf_path)
    end_time = time.time()

    if result_data:
        try:
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=4)
            print(f"SUCCESS: Processed {pdf_filename} in {end_time - start_time:.2f}s. Output saved to {output_json_path}")
        except Exception as e:
            print(f"ERROR: Could not write JSON for {pdf_filename}. Reason: {e}")
    else:
        print(f"FAILURE: Processing failed for {pdf_filename}.")

if __name__ == '__main__':
    print("--- PDF Batch Processing Container Initialized ---")
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Find all PDF files in the input directory
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files found in /app/input. Exiting.")
    else:
        print(f"Found {len(pdf_files)} PDF(s) to process.")
        
        # Use a process pool to process files in parallel, using all available cores
        num_processes = cpu_count()
        print(f"Starting parallel processing with {num_processes} cores.")
        
        with Pool(processes=num_processes) as pool:
            pool.map(process_file_wrapper, pdf_files)
            
        print("--- All files processed. Container shutting down. ---")

