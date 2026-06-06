import os
import json
from google import genai
from google.genai import types
from datetime import date
from sqlalchemy.orm import Session
from app.database.models import Trend, Article
from app.utils.config import GOOGLE_API_KEY, GEMINI_MODEL
from app.utils.gemini_retry import call_with_retry

def get_trend_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'trend_prompt.txt')
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def generate_daily_trends(db: Session):
    """
    Fetches today's articles, asks Gemini to extract trends,
    and stores them in the database.
    """
    if not GOOGLE_API_KEY:
        print("GOOGLE_API_KEY is not set. Cannot extract trends.")
        return []

    # Fetch today's articles
    today = date.today()
    articles = db.query(Article).filter(
        Article.fetched_at >= today
    ).all()

    if not articles:
        return []

    articles_text = "\n\n".join([f"Title: {a.title}\nSource: {a.source}\nContent: {a.content[:500]}..." for a in articles])
    system_instruction = get_trend_prompt()
    
    client = genai.Client(api_key=GOOGLE_API_KEY)
    
    try:
        response = call_with_retry(
            client.models.generate_content,
            model=GEMINI_MODEL,
            contents=articles_text,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
            ),
        )
        
        trends_data = response.text
        # Clean up if markdown code block is returned
        if trends_data.startswith("```json"):
            trends_data = trends_data.replace("```json\n", "").replace("```", "")
        
        trends_list = json.loads(trends_data)
        
        stored_trends = []
        for trend_item in trends_list:
            new_trend = Trend(
                topic=trend_item.get("topic", "Unknown"),
                score=trend_item.get("score", 0),
                reasoning=trend_item.get("reasoning", "")
            )
            db.add(new_trend)
            stored_trends.append(new_trend)
            
        db.commit()
        return stored_trends
        
    except Exception as e:
        print(f"Error extracting trends: {e}")
        return []
