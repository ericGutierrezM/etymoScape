import json
import os
import glob
from tqdm import tqdm

# Import the new SDK components
from google import genai
from google.genai import types

# Helper function to read the key from your file
def load_api_key(filepath="data/google_api.txt"):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"⚠️ Could not find {filepath}. Please ensure it is in the same folder.")
    with open(filepath, "r", encoding="utf-8") as f:
        # .strip() removes any accidental spaces or hidden newlines
        return f.read().strip()

# Load the key and initialize the new GenAI Client
API_KEY = load_api_key()
client = genai.Client(api_key=API_KEY)

SYSTEM_PROMPT = """You are an expert historical linguist and data structurer. Your job is to read a draft etymology JSON file containing raw dictionary text, structured word forms, and graph edges. 

Using ONLY the information provided in the input, you must generate four specific enrichment fields to complete the final JSON schema. Do not invent historical connections or forms that are not present in the input text or nodes.

You must output a valid JSON object with EXACTLY these four keys:
1. "short_summary": (string) 1-2 sentence human-readable narrative explaining the word's journey.
2. "confidence_summary": (string) 1-sentence assessment of how certain this etymology is.
3. "semantic_stages": (array of objects) [{"label": "...", "meaning": "...", "language": "..."}]. Only include if the meaning clearly shifted.
4. "map_route": (array of objects) [{"label": "Language word", "lat": float, "lon": float}]. Order chronologically from oldest to newest.
"""

def enrich_word(draft_filepath, output_dir="data/final_data"):
    os.makedirs(output_dir, exist_ok=True)
    
    with open(draft_filepath, "r", encoding="utf-8") as f:
        draft_data = json.load(f)
        
    word = draft_data.get("query_word", "unknown")
    
    # 1. Call the Gemini API using the new Client
    try:
        # Combine the system instructions and the JSON data into one prompt
        full_prompt = f"{SYSTEM_PROMPT}\n\nDraft Data to process:\n{json.dumps(draft_data, indent=2)}"
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0, # Zero creativity to prevent hallucinations
            )
        )
        
        # Parse the JSON response
        llm_output = json.loads(response.text)
        
    except Exception as e:
        return False, f"API Error: {str(e)}"
        
    # 2. Merge the LLM output with the original Draft Schema
    final_schema = draft_data.copy()
    final_schema["short_summary"] = llm_output.get("short_summary", "")
    final_schema["confidence_summary"] = llm_output.get("confidence_summary", "")
    final_schema["semantic_stages"] = llm_output.get("semantic_stages", [])
    final_schema["map_route"] = llm_output.get("map_route", [])
    final_schema["status"] = "published"
    
    # 3. Save the final, presentation-ready JSON
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