import pandas as pd
import numpy as np
import sqlite3
import requests
import zipfile
import io

# ── 1. EXTRACT ──────────────────────────────────────────────
print("Downloading dataset...")
url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00296/dataset_diabetes.zip"
response = requests.get(url)
zip_file = zipfile.ZipFile(io.BytesIO(response.content))
df = pd.read_csv(zip_file.open('dataset_diabetes/diabetic_data.csv'))
print(f"Extracted: {df.shape[0]:,} rows, {df.shape[1]} columns")

# ── 2. TRANSFORM ─────────────────────────────────────────────
print("\nCleaning data...")

# Replace '?' with NaN
df.replace('?', np.nan, inplace=True)

# Drop high-null columns
df.drop(columns=['weight', 'payer_code', 'medical_specialty'], inplace=True)

# Drop duplicates (keep first encounter per patient)
df.drop_duplicates(subset='patient_nbr', keep='first', inplace=True)

# Simplify readmission column to binary
df['readmitted'] = df['readmitted'].apply(lambda x: 1 if x == '<30' else 0)

# Convert age ranges to numeric midpoints
age_map = {
    '[0-10)': 5, '[10-20)': 15, '[20-30)': 25, '[30-40)': 35,
    '[40-50)': 45, '[50-60)': 55, '[60-70)': 65, '[70-80)': 75,
    '[80-90)': 85, '[90-100)': 95
}
df['age'] = df['age'].map(age_map)

# Keep only key columns
cols = ['encounter_id', 'patient_nbr', 'race', 'gender', 'age',
        'time_in_hospital', 'num_lab_procedures', 'num_procedures',
        'num_medications', 'number_diagnoses', 'readmitted']
df = df[cols]

print(f"Cleaned: {df.shape[0]:,} rows, {df.shape[1]} columns")
print(f"Readmission rate: {df['readmitted'].mean():.1%}")

# ── 3. LOAD ───────────────────────────────────────────────────
print("\nLoading into database...")
conn = sqlite3.connect('hospital.db')
df.to_sql('readmissions', conn, if_exists='replace', index=False)
conn.close()
print("Saved to hospital.db")

# ── 4. VERIFY WITH SQL ────────────────────────────────────────
print("\nRunning SQL queries...")
conn = sqlite3.connect('hospital.db')

query = (
    "SELECT "
    "CASE "
    "WHEN age < 40 THEN 'Under 40' "
    "WHEN age BETWEEN 40 AND 60 THEN '40-60' "
    "ELSE 'Over 60' "
    "END as age_group, "
    "COUNT(*) as total_patients, "
    "ROUND(AVG(time_in_hospital), 2) as avg_days, "
    "ROUND(AVG(readmitted) * 100, 2) as readmission_rate_pct "
    "FROM readmissions "
    "GROUP BY age_group "
    "ORDER BY readmission_rate_pct DESC"
)

results = pd.read_sql_query(query, conn)
conn.close()
print(results)
print("\nPipeline complete!")