# Energy Career Board: setup (about 10 minutes)

## 1. Put it on GitHub
1. Create a GitHub account if needed, then **New repository**. Name it `energy-job-board`. **Public** is required for free GitHub Pages. Never upload your CV or any personal documents to it.
2. Upload everything in this folder (drag and drop in the web page, or `git push`). Keep the `.github/workflows/weekly.yml` path exactly.

## 2. Allow the bot to save results
Settings → Actions → General → **Workflow permissions** → choose **Read and write permissions** → Save.

## 3. Switch on the weekly schedule and test it now
1. Actions tab → if asked, click **I understand my workflows, enable them**.
2. Open **Weekly refresh** → **Run workflow** → Run. Wait about 1–2 minutes.
3. Expect a green tick and a new commit "Weekly refresh". `data/status.json` and `reports/digest-DATE.md` now exist. Open the digest.
   - A red cross usually means every source failed (the script exits with an error on purpose so GitHub emails you). Open the run log.
   - Many "needs_recheck" lines on the first run are normal: some sites block bots or load by script. Those are listed for manual checking.
4. The schedule then runs every **Monday 05:00 UTC = 06:00 West Africa Time**. GitHub can delay scheduled runs by minutes to hours, and it pauses schedules on public repos with no activity for 60 days. Check the Actions tab monthly.

## 4. Host the board
Settings → Pages → Source: **Deploy from a branch** → Branch `main`, folder `/ (root)` → Save. After a minute your board is at `https://<your-username>.github.io/energy-job-board/`. The header then shows the last automated refresh and the Employers tab shows each source's weekly result.

## 5. Weekly routine (what the automation does and does not do)
- It checks the URLs in `sources.json`, politely (robots.txt, delays), and reports changed pages, closure wording, failures and redirects to other hosts.
- It does **not** verify vacancies, mark anything closed, apply for anything or message anyone. A changed page is a lead: open it, find the real vacancy on the employer site, then update the board.
- Add or fix a source by editing `sources.json`. URLs marked `memory` were not seen in any search; fix any that fail.

## Privacy
CV text, notes and outreach drafts are saved only in your own browser (localStorage). They never go to GitHub. Clear them with the Delete / Reset buttons. Do not use shared computers for them.
