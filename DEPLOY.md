# Putting Stock Explorer online (Streamlit Community Cloud)

Result: a web link (like `https://your-name-stock-explorer.streamlit.app`) that works on any
computer with a browser, including Windows PCs at school. Nothing to install for visitors.
Free for public apps.

## What you need
- A free **GitHub** account (github.com) - this holds the code.
- A free **Streamlit Community Cloud** account (share.streamlit.io) - sign in with that GitHub account.

## Step 1: Put the project on GitHub
Easiest: install **GitHub Desktop** (desktop.github.com), sign in, then
File -> Add Local Repository -> choose the `PG 2026 - CS` folder -> "create a repository" ->
Commit all files -> **Publish repository**.
(Untick "Keep this code private" - Community Cloud's free tier works best with public repos. The code
contains no passwords or personal data; `.venv` and your paper-trading save are excluded by `.gitignore`.)

Terminal alternative (after creating an empty repo on github.com):
```bash
cd "/Users/freyaashah/Desktop/PG 2026 - CS"
git init && git add . && git commit -m "Stock Explorer"
git branch -M main
git remote add origin https://github.com/<your-username>/stock-explorer.git
git push -u origin main
```
Note: the browser's "upload files" button on github.com allows only 100 files at a time and the offline
backup has 119, so use GitHub Desktop or Terminal.

## Step 2: Deploy
1. Go to **share.streamlit.io** -> **Create app** -> choose the repository.
2. Branch `main`, main file path **`app.py`**.
3. **Advanced settings -> Python version: 3.12** (or 3.13).
4. Click **Deploy**. The first build takes a few minutes.
5. Copy the link. Open it on another computer to test.

## What is different online
| Topic | Behaviour |
|---|---|
| Paper-trading account | Private to each visitor, starts with a starting capital the visitor chooses (default Rs 1,00,000), resets on refresh/close. (Local mode via `start.command` still saves to disk.) |
| Live prices | Yahoo Finance sometimes blocks or slows cloud servers. If so, the app switches to the saved backup files and shows a yellow banner. This is why the `data/offline` folder is uploaded too. |
| Sleep | Free apps "go to sleep" after a few days without visitors; opening the link wakes it in ~30 seconds. Open it a few minutes before the exhibition. |
| Updating the backup data | Run `scripts/download_offline_data.py` on your Mac, then commit and push the changed `data/offline` files; the app redeploys itself. |
| Updating the app | Any push to GitHub redeploys automatically. |
| Visitors | Anyone with the link can open it. Public apps can also be found via search engines; the disclaimer is on every page. |

## Quick checks after deploying
- Chart, indicators, simulation and backtest load for Reliance.
- Search "tata motors" works.
- BUY a share in the Paper trading tab; refresh the page and see the account reset.
- (If prices look old, the yellow banner will say so - that is the fallback working.)
