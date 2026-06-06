Below is your ready-to-save **`.md` file**. You can copy this directly into your repo as:

`daily_news_briefing_spec.md`

---

```markdown
# 📌 Daily News Briefing Generator (Gemini 2.5 Flash + TTS)

## 1. Objective

Build a Streamlit application that generates a daily ~5-minute spoken news briefing (~700–800 words) from multiple news sources.

The system must also produce a readable text version of the same briefing.

---

## 2. Hard Constraints

### Output constraints
- Max duration: 5 minutes
- Max words: 750 (strict)
- Single continuous narrative (not per-article summaries)
- Spoken-word style output

### Quality constraints
- No hallucinated facts
- No duplicated stories
- No article-by-article structure
- Neutral newsroom tone
- Strict grounding in provided articles

---

## 3. Allowed Models

### 3.1 Text model (ONLY)
- Gemini 2.5 Flash

Used for:
- cleaning
- deduplication
- ranking
- briefing generation

---

### 3.2 Text-to-Speech
- Gemini 2.5 Flash TTS

Used for:
- converting final script into audio

---

## 4. System Architecture

```

RSS / News APIs
↓
Gemini 2.5 Flash (clean + dedupe)
↓
Gemini 2.5 Flash (rank + select top stories)
↓
Gemini 2.5 Flash (generate 750-word briefing script)
↓
Gemini 2.5 Flash TTS (audio generation)
↓
Streamlit UI (text + audio output)

````

---

## 5. Data Flow

### Step 1 — Ingestion

Sources:
- RSS feeds
- News APIs
- Optional curated URLs

Output:
```json
[
  {
    "title": "",
    "content": "",
    "source": "",
    "published_at": "",
    "url": ""
  }
]
````

---

### Step 2 — Cleaning & Deduplication (Flash)

Task:

* remove HTML and noise
* normalize text
* remove duplicates
* standardize structure

Output:

```json
[
  {
    "title": "",
    "clean_content": "",
    "source": "",
    "url": ""
  }
]
```

---

### Step 3 — Ranking & Selection (Flash)

Goal:
Select top 10–15 most relevant stories.

Rules:

* prioritize last 24 hours
* prioritize global relevance
* remove duplicates / near-duplicates

Output:

```json
[
  {
    "title": "",
    "importance": "high | medium | low"
  }
]
```

---

### Step 4 — Briefing Generation (Flash)

This is the core intelligence step.

Input:

* selected news stories

Output:

* single spoken-word script (~750 words max)

---

#### Prompt Template (use exactly)

```
You are a professional news broadcaster.

Create a daily spoken news briefing.

Constraints:
- maximum 750 words
- must be readable aloud in ~5 minutes
- neutral tone
- no speculation
- no hallucinations
- only use provided facts

Structure:
1. Global news overview
2. Major political developments
3. Business and technology updates
4. Human-interest or notable events
5. Closing summary

Rules:
- Do NOT summarize article-by-article
- Merge related stories into coherent narrative
- Remove redundancy
- Keep sentences short and spoken-word friendly

Input news:
{{ARTICLES}}
```

---

#### Output format

```json
{
  "script": "",
  "word_count": 0
}
```

---

## 6. Text-to-Speech (Flash TTS)

Convert final script into audio.

### Input

```json
{
  "text": "<SCRIPT>"
}
```

### Output

* MP3 audio file

---

## 7. Streamlit Application

### Pages

#### Main page

* Button: Generate Daily Briefing
* Output:

  * text briefing
  * audio player
  * download button

---

### Example Streamlit flow

```python
if st.button("Generate Briefing"):

    articles = fetch_news()

    cleaned = gemini_clean(articles)
    ranked = gemini_rank(cleaned)
    script = gemini_generate_script(ranked)

    audio = gemini_tts(script["script"])

    st.subheader("Text Briefing")
    st.write(script["script"])

    st.subheader("Audio Briefing")
    st.audio(audio)
```

---

## 8. Storage (Optional)

Persist daily briefings:

```sql
CREATE TABLE briefings (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP,
    script TEXT,
    audio_url TEXT
);
```

---

## 9. Error Handling

* If no news: fallback to previous briefing
* If API fails: retry once, then fallback cache
* If TTS fails: return text-only version

---

## 10. Performance Rules

* Use Gemini 2.5 Flash for ALL LLM tasks
* One-pass generation only
* Max 15 articles per briefing
* One TTS call per briefing

---

## 11. Cost Optimization

Per briefing:

* 1 call cleaning
* 1 call ranking
* 1 call script generation
* 1 TTS call

Total: 4 calls/day

---

## 12. Explicitly NOT included

* No RAG
* No embeddings
* No vector database
* No clustering
* No multi-agent systems
* No Pro models

Reason:
System is a deterministic daily briefing generator, not a QA system.

---

## 13. Definition of Done

System is complete when:

* generates daily briefing reliably
* script ≤ 750 words
* audio ~ 5 minutes
* no hallucinated facts
* works on Streamlit Community Cloud

---

## 14. Future Enhancements (optional)

* user personalization
* topic filters (tech, finance, politics)
* multilingual briefings
* breaking news mode
* longer podcast mode (10–15 min)

```

---

If you want next step, I can turn this into:
- :contentReference[oaicite:0]{index=0}
- or :contentReference[oaicite:1]{index=1}
- or :contentReference[oaicite:2]{index=2}
```
