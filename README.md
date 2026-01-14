# 🐦 Twitter/X Scraper & Archiver (GUI)

A user-friendly tool to archive Tweets from **X.com (formerly Twitter)**. Built with **Python**, **Selenium**, and **Streamlit**.

This tool connects to an existing Chrome browser session to bypass complex login/CAPTCHA checks and includes a dashboard for managing the scrape.

---

## 🚀 Features

* **GUI Dashboard:** No coding required. Control everything via a clean web interface.
* **Profile Scroll:** Scrape all recent tweets from a user's timeline.
* **Smart Autosave:** Saves progress automatically. If the script crashes, your data is safe in `autosave_{username}.json`.
* **Metadata Detection:** Automatically tags tweets as `is_reply` and `has_media`.
* **Date & Count Limits:** Stop scraping after **N** posts or when reaching a specific date.
* **JSON Export:** Data is saved in structured JSON format, ready for analysis.

---

## ⚠️ Disclaimer & Ethical Use

**This software is for educational and archival purposes only.**

* Scraping Twitter/X may violate their [Terms of Service](https://twitter.com/en/tos).
* **Do not** use this tool to spam, harass, or collect personal data unethically.
* **Use a Burner Account:** Strongly recommended to avoid risk to your primary account.

---

## 🛠️ Prerequisites

1. **Google Chrome** installed
2. **Python 3.8+** installed
3. **A Twitter/X account** (logged in)

---

## 📦 Installation

### 1. Dowbload the script

```bash
git clone https://github.com/MattD-123/Twitter-Profile-Scraper.git
cd Twitter-Profile-Scraper
```

### 2. Install Dependencies

```bash
pip install streamlit selenium pandas
```

---

## 🏃‍♂️ How to Run

This scraper works by connecting to a Chrome window that is **already open**.

---

### Step 1: Open Chrome in Debug Mode

⚠️ **Close ALL Chrome windows first** (check Task Manager / Activity Monitor).

#### Windows

```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="PATH_TO_USER_PROFILE_DATA"
```

#### macOS

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="/tmp/chrome_debug_profile"
```

A new Chrome window will open.

👉 Log in to **X.com** in this window and make sure you can see a timeline.

---

### Step 2: Launch the Scraper

Leave the debug Chrome window open.

From the project directory, run:

```bash
streamlit run app.py
```

A new browser tab will open with the **Scraper Dashboard**.

---

## 📖 Usage Guide

### Target Selection

* Enter the **Target Username** (e.g. `NASA`, `ElonMusk`).

### Scrape Mode

* **Profile Scroll** – chronological archive of a user's timeline

### Limits

* **Max N Posts** – stop after collecting N tweets
* **Cutoff Date** – stop when older tweets are reached

### Start

Click **🚀 Start Scraping**

---

## 📂 Output Data

* **JSON Archive:** `{username}_archive.json`
* **Autosave File:** `autosave_{username}.json` (used if the script crashes)

Both files are created in the project directory.

---

## 🐛 Known Issues

### Chrome Throttling When Minimized

Modern Chrome throttles JavaScript in minimized windows.

* ✅ You may place Chrome **behind other windows**
❌ Do **not** click the minimize (`_`) button

---
### Rate limiting
If the script has been running **x.com** may prevent the scaper from seeing any more replies.

* No known fix at the moment. Best to turn the scraper off and close the Chrome tab for a while.

### Infinite Scroll Stalls

X/Twitter sometimes refuses to load more tweets even at the bottom of the page.

* The script includes a small scroll "jiggle"
* Occasionally you may need to manually scroll the Chrome window slightly

---

### Port 9222 Conflicts

If you see errors like **"Chrome not found"**:

* A Chrome process is still running in the background
* Fully close Chrome and retry the debug command

---

### New Account Redirects

Brand-new accounts may be redirected to:

* "Welcome" screens
* Topic selection pages

You must manually clear these before starting the scraper.

---

## 📝 Roadmap / To‑Do

The following features were removed temporarily for stability and are planned:

* [ ] **Batch Processing** – scrape multiple users sequentially
* [ ] **Media Downloader** – download images & videos locally
* [ ] **Headless Mode** – run without an open browser window (advanced anti‑detection required)

---
