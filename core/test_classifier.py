from pathlib import Path

from extractor import extract_text
from classifier import classify_document


folder = Path(
    "data/documents/loan_1"
)


for pdf_file in folder.glob("*.pdf"):

    pages = extract_text(pdf_file)

    full_text = "\n".join(
        page["text"]
        for page in pages
    )

    document_type = classify_document(
        full_text,
        pdf_file.name
    )

    print(
        f"{pdf_file.name} -> {document_type}"
    )