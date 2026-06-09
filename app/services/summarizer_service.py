import os
from google import genai
from google.genai import types
from datetime import date
from sqlalchemy.orm import Session
from app.database.models import Summary
from app.utils.config import GOOGLE_API_KEY, GEMINI_MODEL, AVAILABLE_MODELS, get_active_model, set_active_model
from app.utils.gemini_retry import call_with_retry

def get_summary_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'summary_prompt.txt')
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def generate_topic_briefing(topic_name: str, articles: list, model: str = None) -> str:
    """
    Takes up to 10 raw Article objects for a specific topic,
    and generates a complete ~1000-word spoken briefing script using a single Gemini API call.
    The LLM handles cleaning, ranking, and generation internally.
    Returns the script as a string.
    """
    if not GOOGLE_API_KEY:
        print("GOOGLE_API_KEY is not set. Cannot generate briefing.")
        return None

    if not articles:
        print(f"No articles provided for topic: {topic_name}. Skipping.")
        return None

    # Limit to 10 articles per topic to control token usage
    articles_to_use = articles[:10]

    # Build the articles block
    articles_text = "\n\n".join([
        f"[{i+1}] Title: {a.title if hasattr(a, 'title') else a.get('title', '')}\n"
        f"    Source: {a.source if hasattr(a, 'source') else a.get('source', '')}\n"
        f"    Content: {(a.content if hasattr(a, 'content') else a.get('content', '') or '')[:800]}..."
        for i, a in enumerate(articles_to_use)
    ])

    # Fill the prompt template
    prompt_template = get_summary_prompt()
    filled_prompt = prompt_template.replace("{{TOPIC}}", topic_name).replace("{{ARTICLES}}", articles_text)

    client = genai.Client(api_key=GOOGLE_API_KEY)

    # Start with explicit model parameter, or the last globally working/active model
    primary_model = model or get_active_model()
    
    # Build fallback sequence prioritizing the current primary model, then other user models
    model_sequence = [primary_model]
    for candidate in AVAILABLE_MODELS:
        if candidate not in model_sequence:
            model_sequence.append(candidate)

    last_error = None
    for current_model in model_sequence:
        try:
            print(f"  Calling Gemini with model '{current_model}'...")
            response = call_with_retry(
                client.models.generate_content,
                model=current_model,
                contents=filled_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                ),
            )
            
            # Successfully made the call, persist this model so remaining summaries use it
            set_active_model(current_model)
            
            if current_model != primary_model:
                print(f"  ✔ Briefing generated successfully using fallback model '{current_model}' after '{primary_model}' failed.")
            return response.text
        except Exception as e:
            print(f"  ✘ Model '{current_model}' failed to generate briefing: {e}")
            last_error = e

    print(f"Error generating briefing for '{topic_name}' after trying all models: {last_error}")
    return None

def save_daily_script(db: Session, script_text: str, topic_name: str = "General"):
    """
    Saves or updates today's generated script for a specific topic in the database.
    """
    today = date.today()
    existing_summary = db.query(Summary).filter(
        Summary.summary_date == today,
        Summary.topic == topic_name
    ).first()

    if existing_summary:
        existing_summary.content = script_text
    else:
        new_summary = Summary(
            summary_date=today,
            topic=topic_name,
            content=script_text
        )
        db.add(new_summary)

    db.commit()
