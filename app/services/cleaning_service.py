import os
import json
from google import genai
from google.genai import types
from app.utils.config import GOOGLE_API_KEY, GEMINI_MODEL

def get_cleaning_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'cleaning_prompt.txt')
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def clean_articles(raw_articles):
    """
    Takes raw Article objects, asks Gemini to clean and deduplicate them,
    and returns a list of dictionaries with clean_content.
    """
    if not GOOGLE_API_KEY:
        print("GOOGLE_API_KEY is not set. Cannot clean articles.")
        return []
    if not raw_articles:
        return []

    # Send a maximum of 50 articles to Gemini for cleaning to prevent hitting output limits
    articles_to_clean = raw_articles[:50]
    
    articles_text = "\n\n".join([f"Title: {a.title}\nSource: {a.source}\nURL: {a.link}\nContent: {a.content[:800]}..." for a in articles_to_clean])
    
    system_instruction = get_cleaning_prompt()
    client = genai.Client(api_key=GOOGLE_API_KEY)
    
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=articles_text,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1,
            ),
        )
        
        output_text = response.text
        if output_text.startswith("```json"):
            output_text = output_text.replace("```json\n", "").replace("```", "")
            
        cleaned_list = json.loads(output_text)
        return cleaned_list
        
    except Exception as e:
        print(f"Error cleaning articles: {e}")
        # Fallback to basic dictionary format if LLM fails
        return [{"title": a.title, "clean_content": str(a.content)[:500], "source": a.source, "url": a.link} for a in articles_to_clean]
