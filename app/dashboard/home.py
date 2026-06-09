import streamlit as st
from datetime import date
import sys
import os
import io
import re
from gtts import gTTS

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from app.database.connection import SessionLocal
from app.database.models import Summary, Trend, Article
from app.services.summarizer_service import generate_topic_briefing, save_daily_script
from app.services.rss_service import TOPIC_SOURCES, TOPIC_DISPLAY_NAMES

# All 5 topics in defined order (DB keys)
ALL_TOPICS = list(TOPIC_SOURCES.keys())

st.title("🏠 AI Daily Brief")

@st.cache_data(show_spinner=False)
def generate_audio_summary(text: str):
    """Convert text to audio bytes using gTTS."""
    clean_text = re.sub(r'[*#_`\~]', '', text)
    tts = gTTS(text=clean_text, lang='en', slow=False)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    return fp.getvalue()

db = SessionLocal()
try:
    today = date.today()
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.header(f"Today's Briefings — {today.strftime('%B %d, %Y')}")
    with col2:
        from app.utils.config import GEMINI_MODEL, AVAILABLE_MODELS
        available_models = list(AVAILABLE_MODELS)
        if GEMINI_MODEL not in available_models:
            available_models.insert(0, GEMINI_MODEL)
        selected_model = st.selectbox(
            "🤖 Model for generation / fallback start",
            options=available_models,
            index=available_models.index(GEMINI_MODEL) if GEMINI_MODEL in available_models else 0,
            help="Choose the starting model for manual generation. If it encounters a quota limit or transient error, the system will fall back to other models automatically."
        )

    # Create one tab per topic
    tab_labels = [TOPIC_DISPLAY_NAMES.get(t, t) for t in ALL_TOPICS]
    tabs = st.tabs(tab_labels)

    for i, topic_name in enumerate(ALL_TOPICS):
        with tabs[i]:
            # Look for an already-generated summary for this topic
            summary = db.query(Summary).filter(
                Summary.summary_date == today,
                Summary.topic == topic_name
            ).first()

            if summary:
                with st.container(border=True):
                    display = TOPIC_DISPLAY_NAMES.get(topic_name, topic_name)
                    st.markdown(f"🔊 **Listen to today's {display} briefing:**")
                    with st.spinner("Preparing audio..."):
                        audio_bytes = generate_audio_summary(summary.content)
                    st.audio(audio_bytes, format='audio/mp3')
                    st.divider()
                    st.markdown(summary.content)
            else:
                st.info(f"No briefing available yet for **{TOPIC_DISPLAY_NAMES.get(topic_name, topic_name)}** today.")

                if st.button(f"🔄 Generate Now", key=f"gen_{topic_name}"):
                    # Fetch today's articles for just this topic (max 10)
                    topic_articles = db.query(Article).filter(
                        Article.fetched_at >= today,
                        Article.category == topic_name
                    ).order_by(Article.published_at.desc()).limit(10).all()

                    if not topic_articles:
                        st.error(
                             f"No articles were fetched for **{topic_name}** today. "
                             "Please run the ingestion pipeline first."
                        )
                    else:
                        with st.spinner(
                            f"Calling Gemini ({selected_model}) once to clean, rank, and generate the **{topic_name}** briefing..."
                        ):
                            script = generate_topic_briefing(topic_name, topic_articles, model=selected_model)

                        if script:
                            save_daily_script(db, script, topic_name)
                            st.success("Briefing generated! Reloading...")
                            st.rerun()
                        else:
                            st.error("Gemini returned an empty response or all fallback models failed. Please try again.")

    st.divider()

    # Key trends across all topics
    st.subheader("Key Highlights Across All Topics")
    trends = db.query(Trend).order_by(Trend.created_at.desc(), Trend.score.desc()).limit(3).all()

    if trends:
        cols = st.columns(len(trends))
        for i, col in enumerate(cols):
            with col:
                st.metric(label=trends[i].topic, value=f"{trends[i].score}/100")
                st.caption(trends[i].reasoning)
    else:
        st.write("No trend data available yet.")

    st.divider()

    # Article count summary
    articles_count = db.query(Article).filter(Article.fetched_at >= today).count()
    st.write(
        f"**📰 {articles_count} articles ingested today.** "
        "Go to the News Explorer to browse and filter them."
    )

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
finally:
    db.close()
