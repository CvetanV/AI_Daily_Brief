import sys
import os
import time
from datetime import date

# Add the root project directory to the python path so imports work correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.database.connection import SessionLocal
from app.database.models import init_db, Article
from app.services.rss_service import fetch_rss_feeds, TOPIC_SOURCES
from app.services.deduplication_service import deduplicate_and_store
from app.services.summarizer_service import generate_topic_briefing, save_daily_script
from app.services.trend_service import generate_daily_trends

# Seconds to pause between consecutive Gemini API calls.
# Pipeline runs at 6 AM UTC; results are consumed at 7-8 AM, so there is
# no urgency — spreading calls 1 minute apart keeps us well under rate limits.
INTER_CALL_DELAY = 60

def run_pipeline():
    print("Starting Daily AI Update Pipeline...")

    # 1. Initialize DB tables
    print("Initializing Database...")
    init_db()

    db = SessionLocal()
    try:
        # 2. Fetch RSS articles for all topics and store new ones
        print("Fetching RSS Feeds for all topics...")
        articles = fetch_rss_feeds()
        print(f"Fetched {len(articles)} raw articles.")

        new_count = deduplicate_and_store(db, articles)
        print(f"Stored {new_count} new unique articles.")

        # 3. For each topic, make ONE Gemini call to generate the briefing
        today = date.today()
        all_topics = list(TOPIC_SOURCES.keys())
        print(f"\nGenerating briefings for {len(all_topics)} topics ({len(all_topics)} total Gemini API calls)...")

        for i, topic_name in enumerate(all_topics):
            print(f"\n[{i+1}/{len(all_topics)}] Processing topic: '{topic_name}'")

            # Fetch today's articles for this specific topic (max 10)
            topic_articles = db.query(Article).filter(
                Article.fetched_at >= today,
                Article.category == topic_name
            ).order_by(Article.published_at.desc()).limit(10).all()

            if not topic_articles:
                print(f"  No articles found for '{topic_name}'. Skipping.")
                continue

            # Pause between calls to avoid triggering rate limits
            if i > 0:
                print(f"  Spacing call — waiting {INTER_CALL_DELAY}s...")
                time.sleep(INTER_CALL_DELAY)

            print(f"  Found {len(topic_articles)} articles. Calling Gemini (1 call)...")
            script = generate_topic_briefing(topic_name, topic_articles)

            if script:
                save_daily_script(db, script, topic_name)
                word_count = len(script.split())
                print(f"  ✔ Briefing saved successfully ({word_count} words).")
            else:
                print(f"  ✘ Failed to generate briefing for '{topic_name}'.")

        # 4. Extract Trends (pause first to space out from last briefing call)
        print(f"\nSpacing call — waiting {INTER_CALL_DELAY}s...")
        time.sleep(INTER_CALL_DELAY)
        print("Extracting Trends (1 additional Gemini call)...")
        trends = generate_daily_trends(db)
        print(f"Extracted {len(trends)} trends.")

        print("\n✔ Pipeline finished successfully.")
        print(f"  Total Gemini API calls made: {len(all_topics)} briefings + 1 trends = {len(all_topics)+1} calls.")

    except Exception as e:
        print(f"Pipeline failed with error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_pipeline()
