
# qasa-alert

Polls qasa.se every 15 minutes via GitHub Actions.
Emails gustavbjorelius@gmail.com when new listings appear.
Criteria: Haninge kommun, max 8 900 kr/mån, entire home, furnished.
Runs in the cloud. Laptop off is fine.

---

## Control flow

Every 15 minutes, GitHub Actions wakes up a fresh machine and runs:
`python main.py`

main.py runs these steps in order:

1. scraper.py talks to api.qasa.se/graphql
   sends a GraphQL POST request with your search criteria as variables
   receives JSON back, normalizes each listing into a flat dict
   returns a list of those dicts

2. filters.py checks each listing locally
   the API already filtered server-side, this is just a safety net
   keeps only listings where furnished=True, shared=False, cost<=8900
   returns a shorter list

3. state.py loads seen_ids.json
   this file contains IDs of listings we have already alerted on
   in GitHub Actions it was restored from cache before main.py ran
   returns a set of ID strings

4. state.py compares matching listings against seen IDs
   any listing whose ID is not in the set is "new"
   returns only new listings

5. if no new listings: exit. done.

6. notifier.py sends one email with all new listings
   connects to smtp.gmail.com with your App Password
   sends plain text: title, cost, start date, URL for each listing

7. state.py adds new IDs to the seen set and writes seen_ids.json to disk
   GitHub Actions caches this file after the script exits
   next run restores it, so we remember what we already saw

---

## Files

main.py          orchestrator. calls all other files in the order above.
scraper.py       talks to the internet. knows the GraphQL query and response shape.
filters.py       pure logic. no I/O. just yes/no on each listing.
state.py         reads and writes seen_ids.json. no I/O to anything else.
notifier.py      sends email. knows nothing about listings except what main passes it.
config.py        loads settings. all other files import from here instead of touching os.getenv directly.
.env             your secrets locally. never committed to git.
.github/workflows/poll.yml   tells GitHub Actions when and how to run the script.

---

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# fill in SMTP_PASS with your Gmail App Password
# create one at: myaccount.google.com  Security  App passwords

python main.py --dry-run   # prints listings, no email, no state written
python main.py             # real run: email + state written
```

## Deploy (set and forget)

```bash
git init
git add .
git commit -m "initial commit"
gh repo create qasa-alert --private --source=. --push

gh secret set SMTP_USER   --body "gustavbjorelius@gmail.com"
gh secret set SMTP_PASS  	# prompt user to input classic GH token
gh secret set ALERT_EMAIL --body "gustavbjorelius@gmail.com"
```

Then go to github.com/yourusername/qasa-alert  Actions tab.
You will see it running. You can also click "Run workflow" to trigger manually.

No more steps. It runs every 15 minutes from now on.

---

## State persistence note

GitHub Actions caches seen_ids.json between runs.
GitHub deletes that cache if unused for 7 days.
If that happens: next run emails you all current listings once, then works normally again.
This is acceptable for a listing alert.

