from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader


def extract_text(pdf_path):
    """
    Extract text from a PDF file.
    """

    reader = PdfReader(str(pdf_path))

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        text = page.extract_text() or ""

        pages.append(
            {
                "page": page_number,
                "text": text.strip()
            }
        )

    return pages


if __name__ == "__main__":

    documents_folder = Path(
        "data/documents/loan_1"
    )

    for pdf_file in documents_folder.glob("*.pdf"):

        print("\n" + "=" * 60)

        print(
            f"FILE: {pdf_file.name}"
        )

        print("=" * 60)

        pages = extract_text(pdf_file)

        for page in pages:

            print(
                f"\n--- Page {page['page']} ---"
            )

            print(
                page["text"]
            )