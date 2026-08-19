from pathlib import Path

from extractor import extract_text
from classifier import classify_document
from claims import extract_claims


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

    claims = extract_claims(
        full_text,
        document_type
    )

    print("\n==============================")
    print(pdf_file.name)
    print("Type:", document_type)
    print("Claims:")
    print(claims)