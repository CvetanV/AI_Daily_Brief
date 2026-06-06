import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from app.database.connection import SessionLocal
from app.database.models import Article
from app.services.rss_service import TOPIC_DISPLAY_NAMES

st.title("📰 News Explorer")

db = SessionLocal()
try:
    # Filters in sidebar (or expander for mobile)
    with st.expander("Filters & Search", expanded=False):
        search_query = st.text_input("Search articles:", "")
        
        # Get unique sources
        sources = [s[0] for s in db.query(Article.source).distinct().all()]
        selected_sources = st.multiselect("Filter by Source:", sources, default=sources)
        
        # Get unique categories and show pretty display names
        categories = [c[0] for c in db.query(Article.category).distinct().all() if c[0]]
        category_labels = {TOPIC_DISPLAY_NAMES.get(c, c): c for c in categories}
        selected_labels = st.multiselect("Filter by Category:", list(category_labels.keys()), default=list(category_labels.keys()))
        selected_categories = [category_labels[l] for l in selected_labels]

    # Build query
    query = db.query(Article)
    if search_query:
        query = query.filter(Article.title.ilike(f"%{search_query}%") | Article.content.ilike(f"%{search_query}%"))
    if selected_sources:
        query = query.filter(Article.source.in_(selected_sources))
    if selected_categories:
        query = query.filter(Article.category.in_(selected_categories))
        
    articles = query.order_by(Article.published_at.desc()).limit(100).all()

    st.write(f"Found {len(articles)} articles.")
    
    # Display Articles
    for a in articles:
        with st.container(border=True):
            st.markdown(f"### [{a.title}]({a.link})")
            
            # Using columns for metadata
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                st.caption(f"**Source:** {a.source}")
            with col2:
                st.caption(f"**Category:** {TOPIC_DISPLAY_NAMES.get(a.category, a.category)}")
            with col3:
                st.caption(f"**Published:** {a.published_at.strftime('%Y-%m-%d %H:%M') if a.published_at else 'Unknown'}")
            
            # Snippet
            if a.content:
                st.write(a.content[:300] + "..." if len(a.content) > 300 else a.content)
            
except Exception as e:
    st.error(f"Error loading news: {e}")
finally:
    db.close()
