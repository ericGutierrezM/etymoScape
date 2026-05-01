import json
import os
import glob
from tqdm import tqdm

def extract_lexical_data(entry):
    """Extracts plurals, countability, and pronunciation from the main entry."""
    info = {
        "part_of_speech": entry.get("pos"),
        "main_definition": entry.get("senses", [{}])[0].get("glosses", [""])[0] if entry.get("senses") else "",
        "tags": entry.get("senses", [{}])[0].get("tags", []) if entry.get("senses") else [],
        "inflections": [],
        "pronunciation": []
    }
    
    # Get plurals/inflections
    for form in entry.get("forms", []):
        if "plural" in form.get("tags", []):
            info["inflections"].append(form.get("form"))
            
    # Get IPA pronunciation
    for sound in entry.get("sounds", []):
        if "ipa" in sound:
            info["pronunciation"].append(sound.get("ipa"))
            
    return info

def process_word(input_filepath, output_dir="data/processed_data"):
    os.makedirs(output_dir, exist_ok=True)
    
    with open(input_filepath, "r", encoding="utf-8") as f:
        entries = json.load(f)
        
    if not entries:
        return False

    word = entries[0].get("word", "unknown")
    lang_code = entries[0].get("lang_code", "en")
    language = entries[0].get("lang", "English")
    
    # --- THE FIX: AGGREGATE ALL ETYMOLOGY DATA ---
    all_etym_texts = set()
    all_templates = []
    
    for entry in entries:
        # 1. Grab all unique text paragraphs
        text = entry.get("etymology_text")
        if text:
            all_etym_texts.add(text.strip())
            
        # 2. Grab all raw templates (so the LLM can see the explicit language codes)
        for t in entry.get("etymology_templates", []):
            if t not in all_templates: # Prevent massive duplication
                all_templates.append(t)
                
    # If we found absolutely no etymology data across all entries, skip it
    if not all_etym_texts and not all_templates:
        return False

    # Find the best entry to pull our baseline lexical info from (Noun > Adj > Verb)
    target_entry = next((e for e in entries if e.get("pos") in ["noun", "adj", "verb"]), entries[0])

    draft_schema = {
        "id": f"{lang_code}:{word}",
        "query_word": word,
        "language": language,
        "title": word,
        "lexical_info": extract_lexical_data(target_entry),
        "raw_etymology": {
            # Join all the found texts with double line breaks
            "text": "\n\n".join(list(all_etym_texts)),
            # Feed the raw templates to the LLM as structured backup evidence!
            "templates": all_templates,
            "source": "Kaikki (Wiktionary extraction)",
            "url": f"https://en.wiktionary.org/wiki/{word}"
        },
        "forms": [],
        "edges": []
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