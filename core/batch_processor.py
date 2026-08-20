import re
import sys
from pathlib import Path
from difflib import SequenceMatcher

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CORE_DIR = Path(__file__).resolve().parent
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from extractor import extract_text
from classifier import classify_document
from claims import extract_claims


def normalize_name_key(name: str) -> str:
    """
    Normalizes borrower names for exact/fuzzy grouping key.
    e.g. 'Applicant 1' -> 'applicant 1', 'Jane Doe' -> 'jane doe'
    """
    if not name:
        return "unknown_applicant"
    clean = re.sub(r"[^\w\s]", "", str(name).lower())
    return " ".join(clean.split())


def find_matching_applicant_key(grouped_dict: dict, name: str) -> str:
    """
    Matches normalized name to an existing applicant key using fuzzy matching or direct equality.
    Ensures applicants with different numerical IDs (e.g., Applicant 1 vs Applicant 4) are separated.
    """
    target_key = normalize_name_key(name)
    if not target_key or target_key == "unknown_applicant":
        return None

    target_digits = re.findall(r"\d+", target_key)

    for existing_key in grouped_dict.keys():
        if existing_key == target_key:
            return existing_key
            
        existing_digits = re.findall(r"\d+", existing_key)
        # If both keys contain numeric identifiers and they differ, do NOT merge
        if target_digits and existing_digits and target_digits != existing_digits:
            continue
            
        ratio = SequenceMatcher(None, existing_key, target_key).ratio()
        if ratio >= 0.88:
            return existing_key

    return None


def group_documents_by_applicant(file_items: list) -> dict:
    """
    Groups a batch list of PDF files into separate applicant document bundles.
    file_items: list of dicts with {"path": str_or_path, "filename": str, "bytes": bytes_opt}
    Returns dictionary mapping applicant_id -> applicant bundle info.
    """
    grouped = {}
    unnamed_counter = 1

    for item in file_items:
        fpath = Path(item["path"])
        fname = item.get("filename", fpath.name)

        # 1. Extract text and classify document
        try:
            pages = extract_text(fpath)
            full_text = "\n".join([page.get("text", "") for page in pages])
            doc_type = classify_document(full_text, filename=fname)
        except Exception as e:
            full_text = ""
            doc_type = classify_document("", filename=fname)

        # Fallback doc_type by filename
        if doc_type == "unknown":
            fn_low = fname.lower()
            if "payslip" in fn_low:
                doc_type = "payslip"
            elif "bank" in fn_low:
                doc_type = "bank_statement"
            elif "tax" in fn_low:
                doc_type = "tax_return"
            elif "kyc" in fn_low:
                doc_type = "kyc"

        # 2. Extract claims and borrower name
        claims = extract_claims(full_text, doc_type) if full_text else {}
        extracted_name = claims.get("borrower_name")

        # Fallback name from filename patterns (e.g. loan_1_payslip.pdf -> Applicant 1)
        if not extracted_name:
            match_loan = re.search(r"loan[_\s-]*(\d+)", fname, re.IGNORECASE)
            match_app = re.search(r"applicant[_\s-]*(\d+)", fname, re.IGNORECASE)
            if match_app:
                extracted_name = f"Applicant {match_app.group(1)}"
            elif match_loan:
                extracted_name = f"Applicant {match_loan.group(1)}"

        # 3. Find or create applicant key
        app_key = find_matching_applicant_key(grouped, extracted_name) if extracted_name else None

        if not app_key:
            if extracted_name:
                app_key = normalize_name_key(extracted_name)
                display_name = extracted_name.strip().title()
            else:
                app_key = f"applicant_unidentified_{unnamed_counter}"
                display_name = f"Unidentified Applicant {unnamed_counter}"
                unnamed_counter += 1

            grouped[app_key] = {
                "client_name": display_name,
                "uploaded_files": {},
                "claims_by_doc": {},
                "file_names": []
            }

        # 4. Store document path and claims in applicant bundle
        grouped[app_key]["uploaded_files"][doc_type] = str(fpath)
        grouped[app_key]["claims_by_doc"][doc_type] = claims
        grouped[app_key]["file_names"].append(fname)

    return grouped


if __name__ == "__main__":
    # Test batch grouping with test documents from loan_1 and loan_4
    docs_base = Path(__file__).resolve().parent.parent / "data" / "documents"
    test_files = []
    
    for loan_folder in [docs_base / "loan_1", docs_base / "loan_4"]:
        if loan_folder.exists():
            for pdf in loan_folder.glob("*.pdf"):
                test_files.append({"path": str(pdf), "filename": f"{loan_folder.name}_{pdf.name}"})

    print(f"Testing batch processor with {len(test_files)} PDF files...")
    batch_grouped = group_documents_by_applicant(test_files)
    
    print(f"\nDiscovered {len(batch_grouped)} distinct applicants in batch:")
    for app_id, data in batch_grouped.items():
        print(f"\n👤 Applicant: {data['client_name']} (Key: '{app_id}')")
        print(f"   Documents ({len(data['uploaded_files'])}): {list(data['uploaded_files'].keys())}")
