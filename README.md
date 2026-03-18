# qasa-alert

Polls qasa.se every 15 min via GitHub Actions.
Emails gustavbjorelius@gmail.com when new listings appear.
Criteria: Haninge Kommun, max 8900 sek/mo, furnished, entire home. 
Runs on cloud. Laptop off = fine. 

---

## Control Flow 

Every 15 min, GH Actions wakes up a fresh machine and runs:
`python main.py` 

main.py runs these steps in order:

1. scraper.py talks to api.qasa.se/graphql
   sends a a GraphQL POST request with your search criteria as variables
   receives JSON back, normalizes each listing into a flat dict
   returns a list of those dicts

2. filters.py checks each listing locally
   the API already filtered server-side, this is just a safety net
   keeps only listings where furnished=True, shared=False, cost<=8900
   returns a shorter list

3. state.py loads seen_ids.json
   this file contains IDs of listings we have already alerted on
   in GH Actions it was stored from cache before main.py ran
   returns a set of ID strings

4. state.py compares matching listings against seen IDs
   any listing whose ID is not in the set is "new"
   returns only new listings

5. if no new listings: exit. done.

6. notifier.py sends one email with all new listings 
   connects to smtp.gmail.com with your App Password
   sends plain text: title, cost, start date, URL for each listing

7. state.py adds new IDs to the seen set and writes seen_ids.json to disk
   GH Actions caches this file after the script exits
   next run restores it, so we remember what we already saw

---

## Files

main.py         orchestrator. calls all other files in the order above.
scraper.py      talks to the web. knows the GraphQL query and response shape.
filters.py      pure ligic. no I/O. just y/n on each listing.
state.py        reads and writes seen_ids.json no I/O to anything else.
notifier.py     sends email. knows nothing about listings except what main passes it
config.py       loads settings. all other files import from herer instead of touching os.getenv directly
.env            your secrets locally. never commited to git.
.github/workflows/poll.yml  tells GH Actions when to run the script.


    
