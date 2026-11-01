Weekly routine (what the automation does and does not do)
- It checks the URLs in `sources.json`, politely (robots.txt, delays), and reports changed pages, closure wording, failures and redirects to other hosts.
- It does **not** verify vacancies, mark anything closed, apply for anything or message anyone. A changed page is a lead: open it, find the real vacancy on the employer site, then update the board.
- Add or fix a source by editing `sources.json`. URLs marked `memory` were not seen in any search; fix any that fail.
