@echo off
echo =========================================
echo Starting AI Intelligence Hub Daily Update
echo =========================================

echo.
echo [1/2] Running Daily Pipeline (Ingestion ^& Summarization)...
python app/scheduler/daily_pipeline.py

echo.
echo [2/2] Launching Streamlit Dashboard...
streamlit run app/main.py

pause
