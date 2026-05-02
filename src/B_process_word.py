import json
import os
import glob
from datetime import date
from tqdm import tqdm

def extract_lexical_data(entry):
    """Formats the Kaikki lexical data to exactly match the target schema."""
    senses = entry.get("senses", [{}])
    first_sense = senses[0] if senses else {}
    
    # 1. Format Tags into noun_type (e.g., ["countable", "uncountable"] -> "countable and uncountable")
    tags = first_sense.get("tags", [])
    noun_type = " and ".join(tags) if tags else ""
    
    # 2. Extract the first available Plural
    plural = ""
    for form in entry.get("forms", []):
        if "plural" in form.get("tags", []):
            plural = form.get("form")
            break
            
    # 3. Extract the first available IPA Pronunciation
    pronunciation = ""
    for sound in entry.get("sounds", []):
        if "ipa" in sound:
            pronunciation = sound.get("ipa")
            break
            
    return {
        "part_of_speech": entry.get("pos", "unknown"),
        "noun_type": noun_type,
        "plural": plural,
        "pronunciation": pronunciation,
        "main_definition": first_sense.get("glosses", [""])[0] if first_sense.get("glosses") else "",
        "usage_note": "" # Left blank as a placeholder for manual curation or future NLP extraction
    }

def process_word(input_filepath, output_dir="data/processed_data"):
    os.makedirs(output_dir, exist_ok=True)
    
    with open(input_filepath, "r", encoding="utf-8") as f:
        entries = json.load(f)
        
    if not entries:
        return False

    # STRICTLY FILTER FOR ENGLISH ENTRIES ONLY
    english_entries = [e for e in entries if e.get("lang") == "English"]
    if not english_entries:
        return False

    word = english_entries[0].get("word", "unknown")
    lang_code = english_entries[0].get("lang_code", "en")
    language = english_entries[0].get("lang", "English")
    
    all_etym_texts = set()
    all_templates = []
    
    # Aggregate all English etymology data (The "Vacuum Cleaner")
    for entry in english_entries:
        text = entry.get("etymology_text")
        if text:
            all_etym_texts.add(text.strip())
            
        for t in entry.get("etymology_templates", []):
            if t not in all_templates:
                all_templates.append(t)
                
    if not all_etym_texts and not all_templates:
        return False

    # Isolate the main noun path
    target_entry = next((e for e in english_entries if e.get("pos") == "noun"), english_entries[0])

    # Build the Draft Schema
    draft_schema = {
        "id": f"{lang_code}:{word}",
        "query_word": word,
        "language": language,
        "title": word,
        "story_type": "migration_word", # Added to match your target schema
        "lexical_info": extract_lexical_data(target_entry),
        "raw_etymology": {
            "text": "\n\n".join(list(all_etym_texts)),
            "templates": all_templates
        },
        "sources": [
            {
                "name": "Wiktionary",
                "url": f"https://en.wiktionary.org/wiki/{word}",
                "type": "dictionary",
                "via": "Kaikki.org",
                "retrieval_date": date.today().isoformat()
            }
        ],
        "forms": [],
        "edges": [],
        "map_route": [],
        "semantic_stages": []
    }

    out_file = os.path.join(output_dir, f"{word}_processed.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(draft_schema, f, indent=2, ensure_ascii=False)
        
    return True

def process_directory(input_dir="data/raw_data", output_dir="data/processed_data"):
    search_pattern = os.path.join(input_dir, "*.json")
    raw_files = glob.glob(search_pattern)
    
    if not raw_files:
        print(f"❌ No raw JSON files found in: '{input_dir}'")
        return
        
    print(f"Found {len(raw_files)} files. Starting batch parsing...")
    success_count = 0
    
    for filepath in tqdm(raw_files, desc="Extracting Drafts"):
        if process_word(filepath, output_dir):
            success_count += 1
            
    print("\n" + "="*40)
    print(f"🎯 DRAFTING COMPLETE: {success_count}/{len(raw_files)} drafted.")
    print("="*40)

if __name__ == "__main__":
    process_directory()