import json
import os
from tqdm import tqdm

def extract_test_words_fast(jsonl_filepath, target_words, output_dir="data/raw_data"):
    os.makedirs(output_dir, exist_ok=True)
    extracted_data = {word: [] for word in target_words}
    words_to_find = set(target_words)
    
    # 1. Get the total file size in bytes instantly
    file_size = os.path.getsize(jsonl_filepath)
    
    # 2. Set up tqdm to track bytes (B) instead of iterations
    with tqdm(total=file_size, unit='B', unit_scale=True, desc="Scanning Kaikki") as pbar:
        with open(jsonl_filepath, "r", encoding="utf-8") as f:
            for line in f:
                # Update the progress bar by the byte-size of the current line
                pbar.update(len(line.encode('utf-8')))
                
                # FAST CHECK
                if any(f'"word": "{w}"' in line for w in words_to_find):
                    data = json.loads(line)
                    current_word = data.get("word")
                    
                    if current_word in words_to_find:
                        extracted_data[current_word].append(data)
                        
                        # Use pbar.write so the progress bar doesn't break
                        pbar.write(f"✅ Found: '{current_word}' (POS: {data.get('pos')})")

    # Save logic remains the same...
    for word, entries in extracted_data.items():
        if entries:
            output_file = os.path.join(output_dir, f"{word}_raw.json")
            with open(output_file, "w", encoding="utf-8") as out_f:
                json.dump(entries, out_f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    # Update this path if your downloaded file is named differently
    KAIKKI_DUMP_FILE = "data/raw-wiktextract-data.jsonl" 
    
    # Your MVP testing batch
    TEST_WORDS = [
        "sugar", 
        "school", 
        "algorithm", 
    ]
    
    extract_test_words_fast(KAIKKI_DUMP_FILE, TEST_WORDS)