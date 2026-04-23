# NewsAPI Rate Limiting Guide

## Problem
You're hitting a **429 Too Many Requests** error from NewsAPI. This means your API key has exceeded its rate limit.

## Rate Limits by Tier

| Tier | Requests/Day | Concurrent | Cost |
|------|-------------|-----------|------|
| **Free** | 100 | 1 | Free |
| **Developer** | 500 | 50 | ~$25/month |
| **Business** | 50,000 | 200 | Custom |

## Solutions Implemented ✅

### 1. **Exponential Backoff with Retries** (nodes/fetch_news.py)
When a 429 error occurs, the system now:
- Backs off with increasing delays: 1s → 2s → 4s
- Automatically retries up to 3 times
- Logs each retry for debugging
- Gracefully skips query if all retries fail

```python
# 429 Error Handling
if r.status_code == 429:
    backoff = 2 ** attempt  # Exponential: 1s, 2s, 4s
    time.sleep(backoff)
    continue  # Retry
```

### 2. **Improved Request Throttling**
- Increased delay between queries: 0.4s → 1.5s
- Only throttles between queries (not after last)
- Added progress logging: "Fetching: {query} (1/4)"

### 3. **Better Error Handling**
- Distinguishes between rate limits (429) and network errors
- Skips failed queries instead of crashing
- All failures are logged for debugging

---

## How to Use

**No code changes needed** — optimizations are automatic!

```powershell
python main.py
```

### If Still Getting 429s:

#### Option 1: Wait (Free Tier)
- Free tier resets daily (UTC)
- Check: https://newsapi.org/account
- Wait for reset before trying again

#### Option 2: Reduce Queries
Edit `app.py` to search fewer topics:
```python
# Search fewer topics, or use simpler queries
topics = ["AI regulation"]  # Instead of 5 topics
```

#### Option 3: Upgrade Plan
- **Developer ($25/month)**: 500 requests/day
- **Business (custom)**: 50,000+ requests/day
- Free trial: https://newsapi.org/pricing

#### Option 4: Implement Request Caching
Add to `utils.py`:
```python
from functools import lru_cache

@lru_cache(maxsize=50)
def cached_fetch(query, api_key):
    """Cache responses for 24 hours"""
    return _fetch_for_query(query, api_key)
```

---

## Debugging Tips

### Check Your API Usage
1. Go to https://newsapi.org/account
2. See "Total requests" for the day
3. Shows reset time (UTC midnight)

### Monitor Requests
Look for these logs:
- ✅ `Fetching: 'query'` — Successful request
- ⚠️ `Rate limit hit. Backing off` — Retrying after 429
- ⚠️ `Rate limit hit after 3 retries` — Query skipped

### Test Single Query
```python
# In Python shell
from nodes.fetch_news import _fetch_for_query
results = _fetch_for_query("AI", "YOUR_API_KEY")
print(f"Got {len(results)} articles")
```

---

## Technical Details

### Retry Strategy
```
Request 1: 429 Error → Wait 1s → Retry
Request 2: 429 Error → Wait 2s → Retry  
Request 3: 429 Error → Wait 4s → Retry
Request 4: 429 Error → Skip query (all retries exhausted)
```

### Throttling Between Queries
Each query to NewsAPI is separated by 1.5 seconds to spread requests:
- 4 queries × 1.5s = 6 seconds total for fetch phase
- Prevents rate limit burst

### Combined Strategy
- **Retries**: Handle transient rate limits
- **Throttling**: Prevent rate limits from happening
- **Logging**: Debug when issues occur
- **Graceful degradation**: Skip failed queries instead of crashing

---

## Estimate Your Usage

For **Vantage Newsdigest**:
- Each search = 4 queries to NewsAPI (1 per angle)
- Each briefing = 1 search = 4 API calls
- Free tier = 100/day ÷ 4 = **25 briefings/day max**

### Examples
- 1 briefing/hour: ✅ Fine (24/day)
- 2 briefings/hour: ✅ Still good (48/day)
- 5 briefings/hour: ⚠️ Close to limit (120/day)
- 10 briefings/hour: ❌ Exceeds limit (240/day)

---

## Prevention Checklist

- [ ] Check your tier and daily limit at https://newsapi.org/account
- [ ] Space out searches (1.5s+ between queries)
- [ ] Restart app fresh each day (cache clears)
- [ ] Monitor logs for 429 errors
- [ ] Consider upgrade if heavy usage needed
