import pandas as pd

file = "data/loan_dataset/loan_approval_dataset.csv"

df = pd.read_csv(file)

# Remove accidental spaces from column names
df.columns = df.columns.str.strip()

print("\n========== DATASET SUMMARY ==========")

print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\n========== NUMERIC SUMMARY ==========")

print(
    df[
        [
            "income_annum",
            "loan_amount",
            "loan_term",
            "cibil_score",
            "bank_asset_value"
        ]
    ].describe()
)

print("\n========== CATEGORICAL VALUES ==========")

print("\nEducation:")
print(df["education"].value_counts())

print("\nSelf Employed:")
print(df["self_employed"].value_counts())

print("\nLoan Status:")
print(df["loan_status"].value_counts())

print("\n========== FIRST 10 APPLICANTS ==========")

print(
    df[
        [
            "loan_id",
            "income_annum",
            "loan_amount",
            "cibil_score",
            "bank_asset_value",
            "loan_status"
        ]
    ].head(10).to_string(index=False)
)