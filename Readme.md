````markdown
# Adobe Hackathon: Connecting the Dots - Part 1A

## Project: Intelligent PDF Outline Extractor

This project is a solution for Round 1A of the "Connecting the Dots" challenge. Its mission is to analyze any given PDF document, intelligently understand its structure, and extract a high-quality outline consisting of the document's title and hierarchical headings (H1, H2, H3).

The entire solution is containerized with Docker for seamless, dependency-free execution and is designed to meet the strict performance and resource constraints of the challenge.

---

## The Approach: An Intelligent, Adaptive Pipeline

To achieve high accuracy across diverse document types (reports, forms, flyers, etc.), this solution uses a sophisticated, multi-stage pipeline that adapts its strategy based on the document's characteristics. It avoids a "one-size-fits-all" approach and instead mimics a human's ability to understand context.

The pipeline operates in four phases:

1.  **Foundational Pre-processing:** Before any analysis can occur, the pipeline ensures data integrity. It uses a robust text-stitching algorithm to reconstruct complete lines of text from fragmented PDF data and identifies/ignores repeating headers and footers to prevent noise.

2.  **High-Speed Document Classification:** Using a lightweight, two-stage algorithm, the pipeline classifies the document as either **"Regular"** (e.g., report, form) or **"Flyer"** (e.g., invitation, brochure). This classification is critical as it dictates the entire subsequent extraction strategy. For long documents, this step uses "Strategic Sampling" to ensure it completes in under a second.

3.  **Adaptive Extraction:**
    * **For "Regular" Documents:** The pipeline prioritizes the most reliable sources first. It checks for machine-readable bookmarks, then searches for a visual "Table of Contents" page. Only if both are absent does it fall back to a rule-based scoring model that analyzes font size, weight, and text patterns to identify headings.
    * **For "Flyer" Documents:** The pipeline assumes a less formal structure. It defaults to an empty title and uses the rule-based scoring model to find the most prominent text elements.

4.  **Post-Processing & Cleanup:** A final set of rules ensures the output is logical and clean. This includes promoting a single heading to a title for simple forms/flyers and de-duplicating a title that also appears as the first heading.

---

## Tech Stack & Libraries

* **Language:** Python 3.11
* **Core Library:** `PyMuPDF` - A high-performance, lightweight library for all PDF parsing and text extraction tasks. No other external libraries are required, keeping the solution lean and fast.
* **Containerization:** Docker

This solution is language-agnostic by design and does not use any NLP or machine learning models, ensuring it meets the multilingual bonus criteria and the strict size/offline constraints.

---

## How to Build and Run

The entire solution is containerized, so no local installation of Python or any libraries is required.

### Prerequisites

* Docker installed and running.

### Step 1: Build the Docker Image

Navigate to the project's root directory (where the `Dockerfile` is located) in your terminal and run the build command.

```bash
docker build -t mysolutionname:somerandomidentifier .
````

### Step 2: Prepare Input Files

Place all the PDF files you want to process into an `input` directory in the project's root folder.

```
.
├── sample_dataset/
│   ├── pdfs/
│   └── outputs/
├── Readme.md
├── Dockerfile
└── ... (all .py files)
```

### Step 3: Run the Container

Execute the following command in your terminal. This will automatically process all PDFs from the `input` directory and save the corresponding JSON files to the `output` directory.

```bash
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none mysolutionname:somerandomidentifier
```

The container will use multiprocessing to process files in parallel, maximizing the use of available CPU cores and ensuring compliance with the 10-second time limit per document.

```
