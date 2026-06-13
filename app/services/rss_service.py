import feedparser
from datetime import datetime
from email.utils import parsedate_to_datetime
import urllib.parse

# Mapping of Topics to their respective RSS sources
# Keys are stored as-is in the DB (category field) — do NOT rename them.
TOPIC_SOURCES = {
    "Data engineering and archtiecture": [
        "https://news.google.com/rss/search?q=Data+Engineering+OR+Data+Architecture&hl=en-US&gl=US&ceid=US:en",
        "https://www.dataengineeringweekly.com/feed",
        "https://startdataengineering.com/rss/",
        "https://towardsdatascience.com/feed",
        "https://aws.amazon.com/blogs/big-data/feed/",
        "https://databricks.com/blog/feed.xml"
    ],
    "Cloud engineering and archtiecture": [
        "https://news.google.com/rss/search?q=Cloud+Engineering+OR+Cloud+Architecture+OR+AWS+OR+Azure+OR+GCP&hl=en-US&gl=US&ceid=US:en",
        "https://cloudcomputing-news.net/feed/",
        "https://techrepublic.com/rssfeeds/topic/cloud",
        "https://www.crn.com/news/cloud/rss.xml",
        "https://aws.amazon.com/blogs/aws/feed/",
        "https://azure.microsoft.com/en-us/blog/feed/",
        "https://cloud.google.com/blog/rss/",
        "https://blog.cloudflare.com/rss/"
    ],
    "AI AI Adoption Gen AI and agentic AI": [
        "https://openai.com/news/rss.xml",
        "https://www.anthropic.com/news/rss",
        "https://hnrss.org/frontpage",
        "https://www.reddit.com/r/LocalLLaMA/.rss",
        "https://news.google.com/rss/search?q=Generative+AI+OR+Agentic+AI+OR+AI+Adoption&hl=en-US&gl=US&ceid=US:en",
        "https://www.marktechpost.com/feed/",
        "https://artificialintelligence-news.com/feed/",
        "https://aiweekly.co/issues.rss",
        "https://theaiinsider.tech/feed",
        "https://newsletter.genai.works/feed",
        "https://importai.net/rss.xml",
        "https://www.lastweekin.ai/feed",
        "https://blogs.microsoft.com/ai/feed/",
        "https://huggingface.co/blog/feed.xml",
        "https://ai.googleblog.com/feeds/posts/default",
        "https://www.producthunt.com/feed"
    ],
    "Global news including wars economical and financial news weather events and EU regulations impacting cloud data and AI": [
        "https://news.google.com/rss/search?q=Global+News+OR+Economy+OR+War+OR+Weather+OR+EU+Regulations&hl=en-US&gl=US&ceid=US:en",
        "https://www.theverge.com/rss/index.xml",
        "https://feeds.arstechnica.com/arstechnica/index/",
        "https://techcrunch.com/feed/",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://feeds.skynews.com/feeds/rss/world.xml",
        "https://www.france24.com/en/rss",
        "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
        "https://world.einnews.com/all_rss"
    ],
    "Research and science news": [
        "https://news.google.com/rss/search?q=Research+OR+Science+News+OR+Scientific+Discovery&hl=en-US&gl=US&ceid=US:en",
        "https://rss.arxiv.org/rss/cs.AI",
        "https://news.mit.edu/rss/topic/artificial-intelligence"
    ]
}

# Short, human-readable labels for the UI.
# Maps internal DB category key → display name shown in tabs/filters.
TOPIC_DISPLAY_NAMES = {
    "Data engineering and archtiecture": "🏗️ Data & Architecture",
    "Cloud engineering and archtiecture": "☁️ Cloud & Infrastructure",
    "AI AI Adoption Gen AI and agentic AI": "🤖 AI & GenAI",
    "Global news including wars economical and financial news weather events and EU regulations impacting cloud data and AI": "🌍 Global News & EU Policy",
    "Research and science news": "🔬 Research & Science",
}

def parse_date(date_string):
    try:
        return parsedate_to_datetime(date_string)
    except Exception:
        return datetime.utcnow()

def fetch_rss_feeds():
    """
    Fetches RSS feeds for all topics and returns a list of article dictionaries.
    The category of each article is set to its topic.
    """
    articles = []
    
    for topic, urls in TOPIC_SOURCES.items():
        for url in urls:
            try:
                feed = feedparser.parse(url)
                source_title = feed.feed.title if hasattr(feed.feed, 'title') else url
                
                for entry in feed.entries:
                    # Extract basic info
                    title = entry.get('title', 'No Title')
                    link = entry.get('link', '')
                    
                    # Content can be in summary, content, or description
                    content = ''
                    if hasattr(entry, 'content'):
                        content = entry.content[0].value
                    elif hasattr(entry, 'summary'):
                        content = entry.summary
                    elif hasattr(entry, 'description'):
                        content = entry.description
                    
                    # Fallback publication date
                    pub_date_str = entry.get('published', entry.get('updated', ''))
                    pub_date = parse_date(pub_date_str) if pub_date_str else datetime.utcnow()
                    
                    articles.append({
                        "source": source_title,
                        "title": title,
                        "link": link,
                        "content": content,
                        "category": topic, # Save the broad topic as the category
                        "published_at": pub_date
                    })
            except Exception as e:
                print(f"Error fetching RSS from {url} for topic '{topic}': {e}")
            
    return articles
