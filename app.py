import os
import re
import random
import requests
import gradio as gr

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

GENRE_MAP = {
    "aksiyon": 28, "macera": 12, "animasyon": 16, "komedi": 35, "suç": 80,
    "belgesel": 99, "dram": 18, "aile": 10751, "fantastik": 14, "tarih": 36,
    "korku": 27, "müzik": 10402, "gizem": 9648, "romantik": 10749,
    "bilim kurgu": 878, "gerilim": 53, "savaş": 10752, "western": 37
}

# -------------------- yardımcılar --------------------
def _parse_query(q: str):
    ql = q.lower()
    genres = [gid for word, gid in GENRE_MAP.items() if word in ql]
    m = re.search(r'(\d+(?:\.\d)?)', ql)
    min_rating = float(m.group(1)) if m else None
    return genres, min_rating

def _safe_get(session: requests.Session, url: str, params: dict):
    try:
        r = session.get(url, params=params, timeout=20)
        if r.status_code != 200:
            return None, f"TMDB hata: {r.status_code} - {r.text[:160]}"
        return r.json(), None
    except Exception as e:
        return None, f"İstek hatası: {e}"

def _extract_seen_titles(history):
    """
    Botun daha önce gönderdiği yanıtlardan başlıkları çıkartır.
    Kart formatımız: '🎬 **Title (Year)** — ...'
    """
    seen = set()
    if not history:
        return seen
    title_re = re.compile(r"🎬 \*\*(.+?) \(\d{4}|\?\?\?\?\)\*\*")
    for user_msg, bot_msg in history:
        if not bot_msg:
            continue
        for line in bot_msg.splitlines():
            m = title_re.search(line)
            if m:
                seen.add(m.group(1).strip())
    return seen

def _detect_more_and_base_query(message, history):
    """
    'başka / daha / farklı' gibi taleplerde, önceki kullanıcı sorusunu geri döndürür.
    """
    msg = (message or "").strip().lower()
    wants_more = any(k in msg for k in ["başka", "daha", "farklı", "yenisi", "bir tane daha"])
    base_query = message
    if wants_more:
        # history'deki son KULLANICI mesajını bul (boş/komut olmayan)
        for u, _ in reversed(history or []):
            if u and not any(k in u.lower() for k in ["başka", "daha", "farklı", "yenisi"]):
                base_query = u
                break
    return wants_more, base_query or message

def _build_cards(results):
    cards = []
    for m in results[:5]:
        title = m.get("title") or m.get("original_title") or "Bilinmeyen Başlık"
        overview = m.get("overview") or "Özet bulunamadı."
        rating = m.get("vote_average", 0)
        year = (m.get("release_date") or "????")[:4]
        poster = m.get("poster_path")
        if poster:
            poster_url = f"https://image.tmdb.org/t/p/w500{poster}"
            cards.append(
                f"🎬 **{title} ({year})** — ⭐ {rating}/10\n"
                f"📝 {overview}\n\n"
                f"![poster]({poster_url})"
            )
        else:
            cards.append(f"🎬 **{title} ({year})** — ⭐ {rating}/10\n📝 {overview}")
    return "\n\n".join(cards) if cards else "❌ Uygun film bulunamadı, lütfen başka bir arama yap!"

# -------------------- öneri motoru --------------------
def _search_discover(session, params, pages_to_try=(1, 2, 3, 4, 5)):
    """
    Discover endpoint'ini, farklı sayfaları deneyip karıştırarak döndür.
    """
    for page in random.sample(list(pages_to_try), k=len(pages_to_try)):
        p = dict(params)
        p["page"] = page
        data, err = _safe_get(session, "https://api.themoviedb.org/3/discover/movie", p)
        if err:
            return [], err
        results = (data or {}).get("results") or []
        if results:
            random.shuffle(results)
            return results, None
    return [], None

def _search_query(session, params, pages_to_try=(1, 2, 3, 4, 5)):
    """
    Search endpoint'ini, farklı sayfaları deneyip karıştırarak döndür.
    """
    for page in random.sample(list(pages_to_try), k=len(pages_to_try)):
        p = dict(params)
        p["page"] = page
        data, err = _safe_get(session, "https://api.themoviedb.org/3/search/movie", p)
        if err:
            return [], err
        results = (data or {}).get("results") or []
        if results:
            random.shuffle(results)
            return results, None
    return [], None

def get_movie_recommendations(query: str, seen_titles=None):
    if not TMDB_API_KEY:
        return ("⚠️ API anahtarı yok. Settings → Repository secrets → TMDB_API_KEY ekle, "
                "sonra Restart Space.")

    seen_titles = seen_titles or set()
    genres, min_rating = _parse_query(query)
    session = requests.Session()
    base = {"api_key": TMDB_API_KEY, "include_adult": "false", "vote_count.gte": 50}

    # 1) Discover (ipucu varsa)
    if genres or min_rating is not None:
        params = dict(base, language="tr-TR", sort_by="vote_average.desc")
        if genres:
            params["with_genres"] = ",".join(map(str, genres))
        if min_rating is not None:
            params["vote_average.gte"] = min_rating

        results, err = _search_discover(session, params)
        if not results:
            # TR boşsa EN'e düş
            params["language"] = "en-US"
            results, err = _search_discover(session, params)
        if err:
            return f"⚠️ {err}"

    else:
        # 2) Metin arama
        params = dict(base, language="tr-TR", query=query)
        results, err = _search_query(session, params)
        if not results:
            params["language"] = "en-US"
            results, err = _search_query(session, params)
        if err:
            return f"⚠️ {err}"

    # Daha önce önerilen başlıkları ele
    filtered = [m for m in results if (m.get("title") or m.get("original_title")) not in seen_titles]

    # Filtre yüzünden boşaldıysa başka sayfa dene
    if not filtered:
        # rastgele başka bir sayfa daha dene
        if "language" in params:
            # discover veya search hangisiyse ona göre tekrar çağır
            if "with_genres" in params or "vote_average.gte" in params:
                filtered, err2 = _search_discover(session, params)
            else:
                filtered, err2 = _search_query(session, params)
            filtered = [m for m in filtered if (m.get("title") or m.get("original_title")) not in seen_titles]

    if not filtered:
        return "🤷‍♀️ Aynı şeyleri önermemek için eledim ama yeni sonuç bulamadım. Biraz daha açık tarif edebilir misin?"

    return _build_cards(filtered)

# -------------------- Gradio arayüz --------------------
def chat_with_bot(message, history):
    # “başka / daha / farklı” yakala → önceki soruyu kullan
    wants_more, base_query = _detect_more_and_base_query(message, history)
    # geçmişte önerilmiş başlıkları topla
    seen = _extract_seen_titles(history)
    answer = get_movie_recommendations(base_query, seen_titles=seen)

    if wants_more:
        prefix = "🔁 Tamam, farklıları getiriyorum:\n\n"
    else:
        prefix = ""
    return prefix + answer

demo = gr.ChatInterface(
    fn=chat_with_bot,
    title="🎬 Film Öneri Chatbotu",
    description=(
        "İpucu ver: *korku 7 üstü*, *romantik komedi*, *dram 8+*.\n"
        "‘başka / daha / farklı’ dersen daha önce önerdiklerimizi eleyip yeni sayfalardan getirir."
    ),
    examples=[
        ["korku filmi 7 üstü"],
        ["romantik komedi öner"],
        ["dram 8 ve üzeri"],
        ["başka"]
    ],
)

if __name__ == "__main__":
    demo.launch()

