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

## Step 3: Make portfolios permanent (free Supabase database)
Without this, visitors' portfolios are kept in files on the Streamlit server and are **lost whenever the app
restarts or sleeps**. With it, every portfolio is kept until you delete it.

1. Go to **supabase.com**, sign in with GitHub, click **New project**. Name it `stock-explorer`, choose a database
   password (write it down; the app does not need it), pick the region nearest India, and wait about 2 minutes.
2. In the left menu open **SQL Editor -> New query**, paste this, and click **Run**:
   ```sql
   create table if not exists public.accounts (
     key text primary key,
     name text not null,
     data jsonb not null,
     updated_at timestamptz not null default now()
   );
   alter table public.accounts enable row level security;
   grant all on public.accounts to service_role;
   ```
3. Open **Project Settings -> API Keys** (or **API**). Copy the **Project URL** and the **secret / service_role** key.
   Keep that key private: it must go only into Streamlit's Secrets box, never into GitHub or a chat.
4. On share.streamlit.io open your app -> **Settings -> Secrets**, paste this (with your own values), and **Save**:
   ```toml
   admin_pin = "choose-a-pin-only-the-organiser-knows"

   [supabase]
   url = "https://YOUR-PROJECT-ID.supabase.co"
   key = "YOUR-SECRET-SERVICE-ROLE-KEY"
   ```
   The app restarts by itself. `admin_pin` unlocks the **Organiser tools** (delete a portfolio, backup, restore).
5. **Test it:** create a user on the live site, then in Supabase open **Table Editor -> accounts**: you should see a row.
   In Streamlit choose **Reboot app**: the user should still be in "Returning user".
6. The free Supabase plan pauses a project after about a week with no use. Open the app (or the Supabase
   dashboard) in the days before the exhibition. A paused project can be restored with one click.

To try the database on your own Mac, put the same secrets in a file called `.streamlit/secrets.toml` (it is already
excluded from GitHub).

## The "Ask the bot" tab needs nothing extra
It answers from notes stored in the app itself (`core/knowledge.py`), so there is no key to set up, no outside service and
no cost. To teach it something new, add a note to that file and push.

## Personalising the About page (optional)
The About page works as it is. To add your daughter's first name, her own reason for building it, or an extra thank-you, add
this to Streamlit's Secrets (all three lines are optional):
```toml
[about]
creator = "Asha"
reason = "I wanted stock markets to feel less intimidating."
thanks_extra = "Thank you to my friends who tested it."
```
Please keep it to a first name: the site is public.

## What is different online
| Topic | Behaviour |
|---|---|
| Accounts | Each visitor chooses a name and starting capital. Portfolios are saved under the name and can be reopened any time (with the Supabase database from Step 3; without it they live in files on the server and are lost on restart). Names have no password, which suits an exhibition: anyone can open anyone's portfolio by name. |
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
