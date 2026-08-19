import pandas as pd
from pathlib import Path

DATA_FOLDER = Path("data/loan_dataset")

files = list(DATA_FOLDER.iterdir())

print("Files found:")
for file in files:
    print("-", file.name)

# Find CSV files
csv_files = list(DATA_FOLDER.glob("*.csv"))

if not csv_files:
    print("\n❌ No CSV file found.")
    print("Check whether the dataset file has a .csv extension.")
    exit()

file = csv_files[0]

print("\nReading:", file.name)

df = pd.read_csv(file)

print("\n========== DATASET INFORMATION ==========")

print("\nShape:")
print(df.shape)

print("\nColumns:")
for column in df.columns:
    print("-", column)

print("\nFirst 5 rows:")
print(df.head())

print("\nMissing values:")
print(df.isnull().sum())