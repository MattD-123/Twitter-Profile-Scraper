import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import random
from datetime import datetime
import pandas as pd
import os
import glob
import html  # <--- Added to fix broken layouts caused by special characters

# ==========================================
# 0. CONFIG & CSS
# ==========================================
st.set_page_config(page_title="Twitter Archiver", page_icon="🐦", layout="wide")

st.markdown("""
<style>
    /* X.com Dark Theme Card */
    .tweet-card {
        background-color: #000000;
        border: 1px solid #2f3336;
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 12px;
        color: #e7e9ea;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    .retweet-context {
        font-size: 13px;
        color: #71767b;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 5px;
        font-weight: bold;
    }

    .tweet-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        font-size: 15px;
        color: #71767b;
        margin-bottom: 4px;
    }

    .tweet-author-block {
        display: flex;
        gap: 4px;
        flex-wrap: wrap;
    }

    .tweet-author {
        font-weight: bold;
        color: #e7e9ea;
        text-decoration: none;
    }
    .tweet-handle {
        color: #71767b;
    }

    .tweet-text {
        margin-top: 4px;
        margin-bottom: 8px;
        font-size: 15px;
        line-height: 20px;
        white-space: pre-wrap; /* Preserves newlines */
        color: #e7e9ea;
    }

    .badges-row {
        margin-top: 8px;
        margin-bottom: 8px;
        display: flex;
        gap: 8px;
    }
    .badge {
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: bold;
    }
    .badge-media { border: 1px solid #1d9bf0; color: #1d9bf0; }
    .badge-reply { border: 1px solid #71767b; color: #71767b; }

    /* ID Footer */
    .tweet-footer {
        border-top: 1px solid #2f3336;
        padding-top: 8px;
        margin-top: 8px;
        font-size: 12px;
        color: #536471;
        font-family: monospace;
        text-align: right;
    }

    a.view-link {
        color: #1d9bf0;
        text-decoration: none;
        font-size: 14px;
    }
    a.view-link:hover { text-decoration: underline; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 1. HELPER FUNCTIONS
# ==========================================

def connect_to_chrome():
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        return None


def parse_twitter_date(date_str):
    if not date_str or date_str == "Unknown": return None
    try:
        return datetime.strptime(date_str.split("T")[0], "%Y-%m-%d").date()
    except:
        return None


def load_json_files():
    files = glob.glob("*_archive.json")
    files.sort(key=os.path.getmtime, reverse=True)
    return files


# ==========================================
# 2. SCRAPING ENGINE
# ==========================================
def run_scraper(driver, target_username, mode, search_query, limit_type, max_count, stop_date, progress_bar,
                status_text):
    target_username = target_username.replace("@", "").strip()
    autosave_file = f"autosave_{target_username}.json"

    if mode == "Keyword Search":
        encoded_query = f"from:{target_username} {search_query}"
        url = f"https://x.com/search?q={encoded_query}&src=typed_query&f=live"
        status_text.text(f"Navigating to search: {encoded_query}...")
    else:
        url = f"https://x.com/{target_username}"
        status_text.text(f"Navigating to profile: {target_username}...")

    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "article")))
    except:
        st.error(f"Page load timeout for {target_username}.")
        return []

    tweets = {}
    start_time = time.time()
    keep_scrolling = True

    while keep_scrolling:
        if time.time() - start_time > 45:
            st.warning("Timeout: No new tweets found for 45s.")
            break

        articles = driver.find_elements(By.XPATH, "//article[@data-testid='tweet']")
        new_in_batch = 0

        for a in articles:
            try:
                link = a.find_element(By.XPATH, './/a[contains(@href, "/status/")]').get_attribute("href")
                parts = link.split("/")
                tweet_id = parts[-1]
                tweet_author = parts[-3]

                if tweet_id in tweets: continue

                try:
                    text = a.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text
                except:
                    text = ""

                try:
                    time_tag = a.find_element(By.TAG_NAME, "time").get_attribute("datetime")
                    tweet_date = parse_twitter_date(time_tag)
                except:
                    time_tag = "Unknown"
                    tweet_date = None

                # Flags
                is_reply = False
                try:
                    if len(a.find_elements(By.XPATH, ".//div[contains(text(), 'Replying to')]")) > 0: is_reply = True
                except:
                    pass

                has_media = False
                try:
                    if len(a.find_elements(By.XPATH,
                                           './/div[@data-testid="tweetPhoto"] | .//div[@data-testid="videoPlayer"]')) > 0: has_media = True
                except:
                    pass

                # Retweet Logic
                is_retweet = False
                if tweet_author.lower() != target_username.lower():
                    is_retweet = True

                # Stop Check
                if limit_type == "Date Cutoff" and tweet_date and stop_date:
                    if tweet_date < stop_date:
                        if mode == "Profile Scroll":
                            status_text.text(f"Reached date limit ({stop_date}). Stopping.")
                            keep_scrolling = False
                            break

                tweets[tweet_id] = {
                    "id": tweet_id,
                    "author": tweet_author,
                    "scraped_from": target_username,
                    "date": str(tweet_date),
                    "text": text,
                    "is_reply": is_reply,
                    "has_media": has_media,
                    "is_retweet": is_retweet,
                    "url": link
                }
                new_in_batch += 1
                start_time = time.time()

                if limit_type == "Max N Posts" and len(tweets) >= max_count:
                    status_text.text(f"Reached limit of {max_count} tweets.")
                    keep_scrolling = False
                    break
            except:
                continue

        if not keep_scrolling: break

        if new_in_batch > 0:
            current_count = len(tweets)
            prog_val = min(current_count / (max_count if limit_type == "Max N Posts" else 50), 1.0)
            progress_bar.progress(prog_val)
            status_text.text(f"Collected {current_count} tweets...")
            try:
                with open(autosave_file, "w", encoding="utf-8") as f:
                    json.dump(list(tweets.values()), f, indent=2, default=str)
            except:
                pass
            time.sleep(random.uniform(2, 4))
        else:
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(2)
            consecutive_no_data += 1
            if len(articles) == 0: break  # Safety break if page is blank

        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(2)

    return list(tweets.values())


# ==========================================
# 3. MAIN APP UI
# ==========================================

tab_scrape, tab_view = st.tabs(["🚀 Scraper Dashboard", "📄 JSON Feed Viewer"])

# --- TAB 1: SCRAPER ---
with tab_scrape:
    st.title("🕵️‍♀️ Twitter Scraper")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Settings")
        target_user_input = st.text_input("Target Username", "BryceSouve")
        mode = st.radio("Mode", ["Profile Scroll", "Keyword Search"])

        search_query = ""
        if mode == "Keyword Search":
            search_query = st.text_input("Keyword", "AI")
            st.caption(f"Searching: from:{target_user_input} {search_query}")

        limit_option = st.selectbox("Stop Condition", ["Max N Posts", "Date Cutoff"])
        max_tweets = 50
        stop_date = None

        if limit_option == "Max N Posts":
            max_tweets = st.number_input("Max Tweets", 10, 2000, 50)
        else:
            stop_date = st.date_input("Cutoff Date", datetime(2025, 1, 1))

        if st.button("Start Scraping", type="primary"):
            if not target_user_input:
                st.error("Enter a username!")
            else:
                driver = connect_to_chrome()
                if not driver:
                    st.error("Chrome not found on Port 9222.")
                else:
                    st.success("Connected!")
                    prog_bar = st.progress(0)
                    stat_text = st.empty()
                    data = run_scraper(driver, target_user_input, mode, search_query, limit_option, max_tweets,
                                       stop_date, prog_bar, stat_text)
                    if data:
                        filename = f"{target_user_input}_archive.json"
                        with open(filename, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, default=str)
                        st.success(f"Saved {len(data)} tweets to {filename}")

# --- TAB 2: JSON FEED VIEWER ---
with tab_view:
    st.header("📱 Feed Viewer")

    json_files = load_json_files()
    if not json_files:
        st.warning("No archive files found.")
    else:
        selected_file = st.selectbox("Select Archive File", json_files)

        try:
            with open(selected_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            df = pd.DataFrame(raw_data)

            # --- ROBUST REPAIR LOGIC ---
            if "date" not in df.columns and "timestamp" in df.columns:
                df["date"] = pd.to_datetime(df["timestamp"], errors='coerce').dt.date
            elif "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"], errors='coerce').dt.date

            if "text" not in df.columns: df["text"] = ""
            if "author" not in df.columns:
                if "username" in df.columns:
                    df["author"] = df["username"]
                elif "url" in df.columns:
                    df["author"] = df["url"].apply(
                        lambda x: x.split('/')[3] if isinstance(x, str) and len(x.split('/')) > 3 else "Unknown")
                else:
                    df["author"] = "Unknown"

            inferred_target = selected_file.split("_archive")[0]
            if "scraped_from" not in df.columns:
                df["scraped_from"] = inferred_target
            # ---------------------------

            f_col1, f_col2, f_col3, f_col4 = st.columns([2, 1, 1, 1])
            with f_col1:
                keyword = st.text_input("🔍 Filter by Keyword", placeholder="Search text...")
            with f_col2:
                if "date" in df.columns and not df["date"].isnull().all():
                    min_date, max_date = df["date"].min(), df["date"].max()
                else:
                    min_date, max_date = datetime.now().date(), datetime.now().date()
                date_range = st.date_input("📅 Date Window", [min_date, max_date])
            with f_col3:
                per_page = st.selectbox("Results/Page", [10, 50, 100], index=0)

            filtered_df = df.copy()
            if keyword:
                filtered_df = filtered_df[filtered_df["text"].str.contains(keyword, case=False, na=False)]
            if len(date_range) == 2 and "date" in filtered_df.columns:
                start_d, end_d = date_range
                filtered_df = filtered_df[(filtered_df["date"] >= start_d) & (filtered_df["date"] <= end_d)]

            total_results = len(filtered_df)
            total_pages = max(1, (total_results // per_page) + (1 if total_results % per_page > 0 else 0))
            with f_col4:
                page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1)

            st.caption(f"Showing {total_results} tweets found.")
            st.divider()

            start_idx = (page_num - 1) * per_page
            page_data = filtered_df.iloc[start_idx:start_idx + per_page]

            for _, row in page_data.iterrows():
                # Safe Extraction
                author = html.escape(str(row.get('author', 'Unknown')))
                date_str = str(row.get('date', 'Unknown'))
                text_content = html.escape(str(row.get('text', '')))
                url_link = row.get('url', '#')
                scraped_from = html.escape(str(row.get('scraped_from', inferred_target)))
                tweet_id = row.get('id', 'Unknown')

                is_retweet = row.get('is_retweet', False)
                if 'is_retweet' not in row and author.lower() != scraped_from.lower():
                    is_retweet = True

                # Conditional HTML Blocks
                retweet_div = f'<div class="retweet-context">🔄 {scraped_from} Retweeted</div>' if is_retweet else ""

                badges_html = ""
                if row.get('is_reply'): badges_html += '<span class="badge badge-reply">Reply</span>'
                if row.get('has_media'): badges_html += '<span class="badge badge-media">Media</span>'

                badges_div = f'<div class="badges-row">{badges_html}</div>' if badges_html else ""

                # Pure HTML string (No indentation to prevent Markdown interpretation issues)
                card_html = f"""<div class="tweet-card">{retweet_div}<div class="tweet-header"><div class="tweet-author-block"><span class="tweet-author">{author}</span><span class="tweet-handle">@{author}</span><span>· {date_str}</span></div><a href="{url_link}" target="_blank" class="view-link">View</a></div><div class="tweet-text">{text_content}</div>{badges_div}<div class="tweet-footer">ID: {tweet_id}</div></div>"""

                st.markdown(card_html, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error reading file: {e}")