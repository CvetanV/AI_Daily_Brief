# AI Daily Brief

An automated AI intelligence platform that collects, processes, and summarizes news from multiple categories, providing daily briefings with audio playback capabilities.

## Features

- **Multi-Topic News Aggregation**: Automatically fetches news from RSS feeds across different categories
- **AI-Powered Summaries**: Uses Google Gemini to generate comprehensive daily briefings per topic
- **Audio Briefings**: Text-to-speech functionality for listening to daily summaries
- **Trend Analysis**: Extracts and displays trending topics across all categories
- **Responsive Dashboard**: Mobile-friendly Streamlit interface
- **Automated Pipeline**: Scheduled daily updates via GitHub Actions
- **Category Management**: Easy addition of new topics and RSS sources

## Technology Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.12, FastAPI
- **Database**: Neon PostgreSQL
- **AI Provider**: Google Gemini 2.5 Flash
- **ORM**: SQLAlchemy
- **Task Scheduling**: GitHub Actions

## Quick Start

### Prerequisites

- Python 3.12+
- Neon PostgreSQL database
- Google Gemini API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AI_Daily_Brief
```

2. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your DATABASE_URL and GOOGLE_API_KEY
```

5. Initialize the database:
```bash
python app/database/models.py
```

### Running the Application

#### Local Development

```bash
streamlit run app/main.py
```

The dashboard will be available at `http://localhost:8501`

#### Using the Batch File (Windows)

```bash
run.bat
```

## Adding New Categories/Topics

### Understanding the Category System

The application uses a two-level system for managing topics:

1. **Internal Category Keys**: Stored in the database (used programmatically)
2. **Display Names**: Human-readable labels shown in the UI

### Step-by-Step Guide to Add New Categories

#### 1. Edit RSS Sources Configuration

File: `app/services/rss_service.py`

Add your new topic to the `TOPIC_SOURCES` dictionary:

```python
TOPIC_SOURCES = {
    # ... existing topics ...
    "Your New Category Name": [
        "https://example.com/rss.xml",
        "https://another-source.com/feed"
    ]
}
```

**Important**: The key (e.g., "Your New Category Name") is stored in the database. Do not rename existing keys as this will break historical data.

#### 2. Add Display Name

In the same file, add a display name to `TOPIC_DISPLAY_NAMES`:

```python
TOPIC_DISPLAY_NAMES = {
    # ... existing mappings ...
    "Your New Category Name": "🏷️ Your Display Name"
}
```

The display name can include emojis and will be shown in tabs, filters, and throughout the UI.

#### 3. Test the New Category

Run the RSS fetch to verify your new sources work:

```bash
python -c "from app.services.rss_service import fetch_rss_feeds; print(fetch_rss_feeds())"
```

#### 4. Database Changes (Optional)

The existing database schema automatically supports new categories through the flexible `category` field in the `articles` table and `topic` field in the `summaries` table. No schema changes are typically needed.

#### 5. Update Daily Pipeline (Automatic)

The daily pipeline in `app/scheduler/daily_pipeline.py` automatically processes all topics defined in `TOPIC_SOURCES`. No code changes are needed - it will:
- Fetch RSS feeds for your new topic
- Generate briefings for your new topic
- Extract trends from articles in your new topic

### Example: Adding a Cybersecurity Category

```python
# In app/services/rss_service.py

TOPIC_SOURCES = {
    # ... existing topics ...
    "Cybersecurity and privacy news": [
        "https://news.google.com/rss/search?q=Cybersecurity+OR+Privacy+OR+Data+Breach",
        "https://krebsonsecurity.com/feed/"
    ]
}

TOPIC_DISPLAY_NAMES = {
    # ... existing mappings ...
    "Cybersecurity and privacy news": "🔒 Cybersecurity & Privacy"
}
```

### Best Practices for New Categories

1. **Use Descriptive Keys**: Make internal keys descriptive but consistent
2. **Multiple Sources**: Add 2-3 RSS sources per category for better coverage
3. **Test Sources**: Verify RSS feeds are valid and regularly updated
4. **Consider Overlap**: Avoid too much overlap with existing categories
5. **Display Names**: Use emojis to make categories visually distinct

## Architecture

### Directory Structure

```
AI_Daily_Brief/
├── app/
│   ├── main.py                 # Streamlit application entry point
│   ├── dashboard/              # UI pages
│   │   ├── home.py            # Home dashboard with briefings
│   │   ├── news.py            # News explorer with filters
│   │   ├── trends.py          # Trends visualization
│   │   └── tools.py           # Resources and tools page
│   ├── services/               # Business logic
│   │   ├── rss_service.py     # RSS feed fetching
│   │   ├── summarizer_service.py  # AI summarization
│   │   ├── trend_service.py   # Trend extraction
│   │   ├── deduplication_service.py  # Article deduplication
│   │   ├── cleaning_service.py  # Content cleaning
│   │   └── ranking_service.py  # Article ranking
│   ├── database/              # Database configuration
│   │   ├── connection.py      # Database connection
│   │   └── models.py          # SQLAlchemy models
│   ├── prompts/               # AI prompts
│   │   ├── summary_prompt.txt  # Summarization prompt
│   │   ├── trend_prompt.txt    # Trend extraction prompt
│   │   ├── cleaning_prompt.txt # Content cleaning prompt
│   │   └── ranking_prompt.txt  # Article ranking prompt
│   ├── scheduler/             # Automated tasks
│   │   └── daily_pipeline.py  # Daily update pipeline
│   └── utils/                 # Utilities
├── .github/
│   └── workflows/
│       └── daily_update.yml   # GitHub Actions workflow
├── requirements.txt
├── .env.example
└── README.md
```

### Database Schema

- **articles**: Raw news articles with categorization
- **summaries**: Generated daily briefings per topic
- **trends**: Extracted trending topics
- **resources**: AI tools and resources

## Daily Pipeline

The automated daily process runs at 6 AM UTC via GitHub Actions:

1. **RSS Ingestion**: Fetches articles from all configured RSS sources
2. **Deduplication**: Removes duplicate articles
3. **Storage**: Stores unique articles in PostgreSQL
4. **Briefing Generation**: Creates AI summaries for each topic
5. **Trend Extraction**: Identifies trending topics across all categories
6. **Rate Limiting**: Spaces API calls to avoid hitting Gemini limits

Total API calls per day: `N topics + 1 trend extraction = N + 1 calls`

### Manual Pipeline Execution

```bash
python app/scheduler/daily_pipeline.py
```

## Maintenance

### Regular Tasks

1. **Monitor RSS Sources**: Check if feeds are still active and updated
2. **Review API Usage**: Monitor Gemini API usage and costs
3. **Database Maintenance**: Clean up old articles periodically
4. **Update Dependencies**: Keep packages updated with security patches

### Updating RSS Sources

Edit `app/services/rss_service.py` to add, remove, or update RSS feed URLs. Changes take effect on the next pipeline run.

### Modifying AI Prompts

Edit files in `app/prompts/` to adjust how the AI processes and summarizes content. Changes affect the next briefing generation.

### Performance Optimization

- Adjust `INTER_CALL_DELAY` in `daily_pipeline.py` if needed
- Limit article count per topic in queries
- Consider caching strategies for frequently accessed data

## Deployment

### Streamlit Community Cloud (Phase 1)

1. Connect your GitHub repository to Streamlit Community Cloud
2. Add environment variables in Streamlit settings:
   - `DATABASE_URL`
   - `GOOGLE_API_KEY`
3. Deploy automatically on push to main branch

### GitHub Actions Configuration

The workflow is configured in `.github/workflows/daily_update.yml`. To modify the schedule:

```yaml
on:
  schedule:
    - cron: '0 6 * * *'  # Runs daily at 6 AM UTC
```

### Alternative Hosting (Phase 2)

Consider migrating to:
- Railway
- Render
- Azure App Service

## Troubleshooting

### Common Issues

**Pipeline fails with database errors**
- Verify `DATABASE_URL` is correct in `.env`
- Check database connectivity
- Ensure tables are initialized

**No articles being fetched**
- Verify RSS feed URLs are valid
- Check network connectivity
- Review feedparser output for specific errors

**Gemini API errors**
- Verify `GOOGLE_API_KEY` is valid
- Check API quota and billing
- Review rate limiting configuration

**Audio not playing**
- Verify `gTTS` dependency is installed
- Check browser audio permissions
- Ensure internet connectivity for TTS service

### Logs and Debugging

- Pipeline logs are available in GitHub Actions
- Local development: Check terminal output
- Database queries: Add logging in `database/connection.py`

## Contributing

1. Test changes locally before committing
2. Add new categories following the guide above
3. Update documentation for significant changes
4. Ensure all existing categories still work after modifications

## License

[Add your license information here]

## Support

For issues or questions:
- Check troubleshooting section above
- Review GitHub Issues
- Contact: [Add contact information]