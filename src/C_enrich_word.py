import json
import os
import glob
import time
from datetime import date
from tqdm import tqdm
from google import genai
from google.genai import types

def load_api_key(filepath="data/google_api.txt"):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read().strip()

client = genai.Client(api_key=load_api_key())

# The Ultimate Few-Shot System Prompt
SYSTEM_PROMPT = """You are an expert historical linguist and geographer. You will receive a draft JSON for an English word. 

Your task is to parse the `raw_etymology` text and templates (especially the "etymon" tree if present) to extract the SINGLE, primary chronological chain of the main noun/root. 
CRITICAL INSTRUCTION: Ignore derivations from other languages, side-branches, doublets, or verb forms (e.g., if the main word is a noun, ignore its verb descendant). 

You must return a single valid JSON object. Use the following structure as your EXACT template, filling it with the data extracted from the prompt. Ensure the `sources` array explicitly mentions Kaikki as the extractor.

EXPECTED OUTPUT TEMPLATE:
{
  "short_summary": "The English word “sugar” entered through French and medieval Latin...",
  "confidence_summary": "The broad route is well established...",
  "story_type": "migration_word",
  "forms": [
    {
      "id": "eng:sugar",
      "lemma": "sugar",
      "language": "English",
      "period": "Modern English",
      "approx_start_year": 1200,
      "approx_end_year": 2026,
      "region_label": "England",
      "lat": 52.0,
      "lon": -1.5,
      "meaning": "sweet crystalline substance"
    }
  ],
  "edges": [
    {
      "from": "eng:sugar",
      "to": "fro:sucre",
      "relation": "borrowed_from",
      "confidence": "high",
      "note": "English borrowed the word through French."
    }
  ],
  "semantic_stages": [
    {
      "label": "Granular material",
      "meaning": "gravel, grit, or small particles",
      "language": "Sanskrit",
      "period": "Ancient",
      "approx_year": -500
    }
  ],
  "map_route": [
    {
      "label": "Sanskrit śárkarā",
      "lat": 25.3,
      "lon": 82.9
    }
  ],
  "sources": [
    {
      "name": "Wiktionary",
      "url": "https://en.wiktionary.org/wiki/sugar",
      "type": "dictionary",
      "via": "Kaikki.org",
      "retrieval_date": "2026-05-01"
    }
  ],
  "status": "auto_parsed_needs_review"
}
"""

def enrich_word(draft_filepath, output_dir="data/final_data", max_retries=3):
    os.makedirs(output_dir, exist_ok=True)
    
    with open(draft_filepath, "r", encoding="utf-8") as f:
        draft_data = json.load(f)
        
    word = draft_data.get("query_word", "unknown")
    full_prompt = f"{SYSTEM_PROMPT}\n\nDraft Data to process:\n{json.dumps(draft_data, indent=2)}"
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                )
            )
            llm_output = json.loads(response.text)
            break 
            
        except Exception as e:
            error_str = str(e)
            if "503" in error_str or "429" in error_str:
                if attempt < max_retries - 1:
                    sleep_time = 2 ** attempt * 5
                    tqdm.write(f"⏳ Server busy. Retrying '{word}' in {sleep_time}s...")
                    time.sleep(sleep_time)
                    continue
            return False, f"API Error after {attempt+1} attempts: {error_str}"
            
    final_schema = draft_data.copy()
    final_schema.update(llm_output) 
    
    # Force the status flag to be safe
    final_schema["status"] = "auto_parsed_needs_review"
    
    # Inject today's date dynamically into the sources if the LLM hallucinated the template date
    if "sources" in final_schema and len(final_schema["sources"]) > 0:
         final_schema["sources"][0]["retrieval_date"] = date.today().isoformat()
    
    out_file = os.path.join(output_dir, f"{word}_final.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(final_schema, f, indent=2, ensure_ascii=False)
        
    return True, ""

def process_enrichment_batch(input_dir="data/processed_data", output_dir="data/final_data"):
    search_pattern = os.path.join(input_dir, "*.json")
    draft_files = glob.glob(search_pattern)
    if not draft_files:
        print(f"❌ No draft JSON files found in: '{input_dir}'")
        return
    print(f"Found {len(draft_files)} drafts. Starting Gemini enrichment...")
    success_count = 0
    for filepath in tqdm(draft_files, desc="Enriching Summaries"):
        success, error_msg = enrich_word(filepath, output_dir)
        if success:
            success_count += 1
        else:
            tqdm.write(f"⚠️ Failed to enrich {os.path.basename(filepath)}: {error_msg}")
            
    print("\n" + "="*40)
    print(f"🎯 ENRICHMENT COMPLETE: {success_count}/{len(draft_files)} words finalized.")
    print("="*40)

if __name__ == "__main__":
    process_enrichment_batch()