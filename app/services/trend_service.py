import os
import json
from google import genai
from google.genai import types
from datetime import date
from sqlalchemy.orm import Session
from app.database.models import Trend, Article
try:
    from app.utils.config import GOOGLE_API_KEY, GEMINI_MODEL, AVAILABLE_MODELS, get_active_model, set_active_model
except ImportError:
    from app.utils.config import GOOGLE_API_KEY, GEMINI_MODEL
    AVAILABLE_MODELS = [
        "gemini-2.5-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash-lite",
        "gemini-3-flash",
        "gemma-4-26b",
        "gemma-4-31b",
        "gemini-2.5-flash-tts"
    ]
    _active_model = None
    def get_active_model() -> str:
        global _active_model
        return _active_model or GEMINI_MODEL
    def set_active_model(model_name: str):
        global _active_model
        _active_model = model_name
from app.utils.gemini_retry import call_with_retry

def get_trend_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'trend_prompt.txt')
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def generate_daily_trends(db: Session, model: str = None):
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
    
    primary_model = model or get_active_model()
    
    model_sequence = [primary_model]
    for candidate in AVAILABLE_MODELS:
        if candidate not in model_sequence:
            model_sequence.append(candidate)

    response_text = None
    last_error = None
    
    for current_model in model_sequence:
        try:
            print(f"  Calling Gemini for trends with model '{current_model}'...")
            response = call_with_retry(
                client.models.generate_content,
                model=current_model,
                contents=articles_text,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                ),
            )
            
            # Successfully made the call, persist this model
            set_active_model(current_model)
            
            if current_model != primary_model:
                print(f"  ✔ Trends extracted successfully using fallback model '{current_model}' after '{primary_model}' failed.")
            response_text = response.text
            break
        except Exception as e:
            print(f"  ✘ Model '{current_model}' failed to extract trends: {e}")
            last_error = e

    if not response_text:
        print(f"Error extracting trends after trying all models: {last_error}")
        return []

    try:
        trends_data = response_text
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
        print(f"Error parsing trends JSON response: {e}")
        return []
