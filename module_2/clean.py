import json
import os
from tqdm import tqdm

INPUT_FILE = "applicant_data.json"
OUTPUT_FILE = "llm_extend_applicant_data.json"
BATCH_SIZE = 500  # Save every 500 records

# 1. Load input data
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    records = json.load(f)

# 2. Load existing progress if available (for resumption)
processed_records = []
processed_ids = set()

if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        try:
            processed_records = json.load(f)
            # Assuming each record has a unique identifier or index; 
            # if not, you can track by index or a unique URL/id field.
            processed_ids = {r.get("id") or i for i, r in enumerate(processed_records)}
            print(f"Resuming from checkpoint: Found {len(processed_records)} already processed records.")
        except json.JSONDecodeError:
            print("Checkpoint file was empty or corrupted. Starting fresh.")

# 3. Processing loop with batch saving
for idx, record in enumerate(tqdm(records, desc="Cleaning Records")):
    record_id = record.get("id") or idx
    
    if record_id in processed_ids:
        continue  # Skip already processed items

    # --- YOUR LLM CLEANING / EXTRACTION LOGIC HERE ---
    # cleaned_data = call_local_llm(record)
    
    # Example placeholder for cleaned record:
    cleaned_record = record.copy()
    cleaned_record["cleaned_status"] = "Processed via GPU"
    
    processed_records.append(cleaned_record)
    processed_ids.add(record_id)

    # Periodic checkpoint save
    if (idx + 1) % BATCH_SIZE == 0:
        temp_file = OUTPUT_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(processed_records, f, indent=2)
        os.replace(temp_file, OUTPUT_FILE)

# Final save
temp_file = OUTPUT_FILE + ".tmp"
with open(temp_file, "w", encoding="utf-8") as f:
    json.dump(processed_records, f, indent=2)
os.replace(temp_file, OUTPUT_FILE)

print("Data cleaning complete and saved successfully!")