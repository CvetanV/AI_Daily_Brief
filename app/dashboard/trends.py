import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from app.database.connection import SessionLocal
from app.database.models import Trend

st.title("📈 Trends Dashboard")

db = SessionLocal()
try:
    st.write("Recent AI Trends extracted from daily news.")
    
    # Get last 50 trends
    trends = db.query(Trend).order_by(Trend.created_at.desc()).limit(50).all()
    
    if not trends:
        st.info("No trend data available yet.")
    else:
        # Prepare data for visualization
        data = []
        for t in trends:
            data.append({
                "Date": t.created_at.strftime('%Y-%m-%d') if t.created_at else "Unknown",
                "Topic": t.topic,
                "Score": t.score,
                "Reasoning": t.reasoning
            })
        
        df = pd.DataFrame(data)
        
        # Display top topics
        st.subheader("Latest Trending Topics")
        latest_date = df['Date'].iloc[0]
        latest_trends = df[df['Date'] == latest_date]
        
        # Create a bar chart for latest trends
        st.bar_chart(latest_trends.set_index('Topic')['Score'])
        
        st.divider()
        
        st.subheader("Trend History")
        st.dataframe(
            df,
            column_config={
                "Date": st.column_config.TextColumn("Date"),
                "Topic": st.column_config.TextColumn("Topic", width="medium"),
                "Score": st.column_config.ProgressColumn("Score (0-100)", min_value=0, max_value=100),
                "Reasoning": st.column_config.TextColumn("Reasoning", width="large")
            },
            hide_index=True,
            use_container_width=True
        )

except Exception as e:
    st.error(f"Error loading trends: {e}")
finally:
    db.close()
