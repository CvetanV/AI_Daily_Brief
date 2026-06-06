import os
import json
from google import genai
from google.genai import types
from app.utils.config import GOOGLE_API_KEY, GEMINI_MODEL

def get_ranking_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'ranking_prompt.txt')
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def rank_articles(cleaned_articles):
    """
    Takes cleaned articles, asks Gemini to rank and select the top 10-15 stories.
    Returns a filtered list of article dictionaries.
    """
    if not GOOGLE_API_KEY:
        print("GOOGLE_API_KEY is not set. Cannot rank articles.")
        return cleaned_articles[:15]
    if not cleaned_articles:
        return []

    articles_text = "\n\n".join([f"Title: {a['title']}\nContent: {a.get('clean_content', '')[:500]}..." for a in cleaned_articles])
    
    system_instruction = get_ranking_prompt()
    client = genai.Client(api_key=GOOGLE_API_KEY)
    
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=articles_text,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
            ),
        )
        
        output_text = response.text
        if output_text.startswith("```json"):
            output_text = output_text.replace("```json\n", "").replace("```", "")
            
        ranked_list = json.loads(output_text)
        
        # Filter original cleaned articles based on the ranked list
        ranked_titles = [r.get("title", "") for r in ranked_list]
        selected_articles = []
        for article in cleaned_articles:
            # Simple matching, LLM sometimes slightly alters titles
            if any(rt.lower() in article['title'].lower() for rt in ranked_titles) or any(article['title'].lower() in rt.lower() for rt in ranked_titles):
                selected_articles.append(article)
                
        # Limit to 15 just in case
        return selected_articles[:15]
        
    except Exception as e:
        print(f"Error ranking articles: {e}")
        return cleaned_articles[:15]
