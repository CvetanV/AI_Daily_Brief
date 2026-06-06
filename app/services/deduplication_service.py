from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.database.models import Article

def deduplicate_and_store(db: Session, fetched_articles: list[dict]):
    """
    Takes raw fetched articles, removes duplicates (by URL/Link),
    and stores new ones into the database.

    Uses a PostgreSQL-native INSERT ... ON CONFLICT DO NOTHING so that
    duplicates within the same fetched batch (same article appearing across
    multiple RSS feeds/topics) and duplicates already in the DB are both
    silently skipped without raising a UniqueViolation.
    """
    if not fetched_articles:
        return 0

    # De-duplicate within the fetched batch itself (keep first occurrence per link)
    seen_links = {}
    for article_data in fetched_articles:
        link = article_data.get("link", "")
        if link and link not in seen_links:
            seen_links[link] = article_data

    unique_articles = list(seen_links.values())

    # Build the list of dicts matching the Article column names
    rows = [
        {
            "source": a["source"],
            "title": a["title"],
            "link": a["link"],
            "content": a["content"],
            "category": a["category"],
            "published_at": a["published_at"],
        }
        for a in unique_articles
    ]

    # Single bulk INSERT ... ON CONFLICT (link) DO NOTHING
    stmt = (
        pg_insert(Article)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["link"])
    )
    result = db.execute(stmt)
    db.commit()

    # rowcount reflects how many rows were actually inserted
    new_articles_count = result.rowcount if result.rowcount is not None else 0
    return new_articles_count
