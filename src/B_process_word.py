import json
import os
import glob
from tqdm import tqdm

def load_metadata(filepath="data/lang_metadata.json"):
    """Loads the geographic and temporal lookup table from an external JSON file."""
    if not os.path.exists(filepath):
        print(f"⚠️ Warning: {filepath} not found. Nodes will lack coordinates.")
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

# Load the external metadata once when the script starts
LANGUAGE_METADATA = load_metadata()

# Map Kaikki template names to our Graph Edge relations
RELATION_MAP = {
    "bor": "borrowed_from",
    "inh": "inherited_from",
    "der": "derived_from",
    "cog": "cognate_with"
}

def create_form_node(lang_code, word, meaning=None):
    """Creates a standardized node using our metadata dictionary."""
    meta = LANGUAGE_METADATA.get(lang_code, {})
    return {
        "id": f"{lang_code}:{word}",
        "lemma": word,
        "language": meta.get("language", lang_code), # Fallback to code if not in DB
        "period": meta.get("period"),
        "region_label": meta.get("region"),
        "lat": meta.get("lat"),
        "lon": meta.get("lon"),
        "meaning": meaning
    }

def process_word(input_filepath, output_dir="data/processed_data"):
    """Parses a single Kaikki JSON file into our Draft Graph Schema."""
    with open(input_filepath, "r", encoding="utf-8") as f:
        entries = json.load(f)
        
    # Find the first entry that actually has etymology data
    entry = next((e for e in entries if "etymology_templates" in e), None)
    if not entry:
        return False # Signal that we skipped this file

    word = entry.get("word")
    if not word:
        return False
        
    base_lang = entry.get("lang_code", "en")
    
    # Initialize the Draft Schema
    draft_schema = {
        "id": f"{base_lang}:{word}",
        "query_word": word,
        "language": entry.get("lang", "English"),
        "title": word,
        "lexical_info": {
            "part_of_speech": entry.get("pos"),
            "main_definition": entry.get("senses", [{}])[0].get("glosses", [""])[0]
        },
        "raw_etymology": {
            "text": entry.get("etymology_text", ""),
            "source": "Wiktionary via Kaikki"
        },
        "forms": [],
        "edges": []
    }

    # 1. Add the starting root node (e.g., English: sugar)
    seen_forms = set()
    root_node = create_form_node(base_lang, word)
    draft_schema["forms"].append(root_node)
    seen_forms.add(root_node["id"])

    # 2. Iterate through templates to build the chain
    current_target_id = root_node["id"]
    
    for template in entry.get("etymology_templates", []):
        t_name = template.get("name")
        args = template.get("args", {})
        
        # We only care about derivation/borrowing templates for the main chain
        if t_name in RELATION_MAP:
            source_lang = args.get("2")
            source_word = args.get("3")
            source_meaning = args.get("t")
            
            if not source_lang or not source_word:
                continue
                
            source_node = create_form_node(source_lang, source_word, source_meaning)
            source_id = source_node["id"]
            
            # Add node to graph if we haven't seen it
            if source_id not in seen_forms:
                draft_schema["forms"].append(source_node)
                seen_forms.add(source_id)
                
            # Create the Edge
            draft_schema["edges"].append({
                "from": current_target_id,
                "to": source_id,
                "relation": RELATION_MAP[t_name],
                "confidence": "high",
                "note": template.get("expansion", "")
            })
            
            # Move the pointer!
            current_target_id = source_id

    # 3. Save the Draft
    out_file = os.path.join(output_dir, f"{word}_processed.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(draft_schema, f, indent=2, ensure_ascii=False)
        
    return True # Signal success

def process_directory(input_dir="data/raw_data", output_dir="data/processed_data"):
    """Scans a directory and processes all JSON files found inside."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Use glob to find all .json files in the target directory
    search_pattern = os.path.join(input_dir, "*.json")
    json_files = glob.glob(search_pattern)
    
    if not json_files:
        print(f"❌ No JSON files found in directory: '{input_dir}'")
        return

    print(f"Found {len(json_files)} files. Starting batch extraction...")
    
    success_count = 0
    skip_count = 0
    
    # Wrap the file list in tqdm for a progress bar
    for filepath in tqdm(json_files, desc="Parsing Etymologies"):
        success = process_word(filepath, output_dir)
        if success:
            success_count += 1
        else:
            skip_count += 1
            
    print("\n" + "="*40)
    print("🎯 BATCH PROCESSING COMPLETE")
    print("="*40)
    print(f"✅ Successfully drafted: {success_count} words")
    if skip_count > 0:
        print(f"⚠️ Skipped (no etymology templates): {skip_count} words")
    print(f"📂 Output saved to: '{output_dir}/'")

if __name__ == "__main__":
    # Point this to the folder containing the raw Kaikki outputs
    INPUT_FOLDER = "data/raw_data"
    OUTPUT_FOLDER = "data/processed_data"
    
    process_directory(INPUT_FOLDER, OUTPUT_FOLDER)