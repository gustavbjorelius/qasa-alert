# main.py 
# 
# WHAT THIS FILE DOES: 
#   Orchestrate everything. Calls the other files in the right sequence.
#   This file knows the otder of operations. It doesn't know HOW to fetch, 
#   filter, track state, or send emails - those files handle their own job. 
#
# THIS IS THE ONLY FILE YOU RUN: 
#   Locally:            python main.py --dry-run
#   Locally (real):     python main.py 
#   GitHub Actions:     python main.py (called by poll.yml on a schedule)
# CONTROL FLOW: - one complete poll cycle: 
#   1. fetch_listings()         scraper.py  -> hits Qasa API, return dict
#   2. apply_filters()          filters.py  -> keeps only matching listings
#   3. load_seen()              state.py    -> reads seen_ids.json from disk
#   4. find_new_listings()      state.py    -> compares: which are new?
#   5. send_alert()             notify.py   -> emails new listings (skipped if none)
#   6. mark_as_seen()           state.py    -> adds new IDs to the seen set
#   7. save_seen_ids()          state.py    -> writes updated set to disk
#   (GitHub Actions cashes seen_ids.json after script exits, restores next run)
# ==================================================================================
import argparse     # stdlib. reads flags from the commandline (e.g. --dry-run).
import logging      # stdlib. prints timestamped status lines to the terminal.

# FROM X IMPORT Y: go into file X, grab function Y, makr it available here.
#  Without these lines, Python doesn't know these files or functions exist. 
#  We import specific functions (not whole modules) to keep it explicit -
#  you can see exactly what this file uses from each module. 
from scraper    import fetch_listings
from filters    import apply_filters
from state      import load_seen_ids, save_seen_ids, find_new_listings, mark_as_seen
from notifier   import send_alert 

# CONFIGURE LOGGING FOR THE WHOLE PROGRAM:
#  basicConfig() sets up the logging system once. Every logger.info() call
#  in every file (scraper, filters, state, notifier) uses this format.

# WHY HERE: and not in each file: there should be one place that configures
#   logging. main.py runs first, so it configures, others just use it.
#   %(asctime)s     = timestamp e.g. "2026-03-16 12:00:01"
#   %(levelname)    = INFO, WARNING, ERROR etc. -8s pads it to 8 chars for alignment
#   %(message)s     = whatever you passed to logger.info("...")
logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
logger = logging.getLogger(__name__)
# __name__ here equals "main". Creates a logger names "main".
# logger.info("...") prints: "2026-03-01 12:00:01  INFO    ..."

# =================================================================================
# poll(dry_run=False)
# THE CORE FUNCTION. Contains the full control flow described above. 
#   dry_run=False means: if called with no argument, dry_run defaults to False.
#   Call poll(dry_run=True) to run without sending email or writing state.
# WHY dry_run: safe way to oest that the API works and listings are found, 
#   without spamming yourself or marking listings as seen prematurely. 
# ================================================================================
def poll(dry_run=False):

    # STEP 1: fetch
    all_listings = fetch_listings()
    # Returns a list of dicts. Each dict has keys defined in scraper._normalize():
    # "id", "monthly_cost", "furnished", "shared", "url".
    # Returns [] (empty list) if anything goes wrong - scraper ahdles its own errors.
    logger.info("Fetched %d listings from API", len(all_listings))
    # %d = integer placeholder. len() = count of items. Prints e.g. 
    # "Fetched 13 listings from API"

    # STEP 2: filter
    matching = apply_filters(all_listings)
    # Returnsa subset of all_listings = only those matching our criteria.
    # Even though the API already filtered server-side, this is a local safety net.
    logger.info("%d match criteria", len(matching))

    # STEP 3: load memory
    seen_ids = load_seen_ids()
    # Returns a set of ID strings we've already alerted on (from seen_ids.json).
    # Empty set on first fun (file doesn't exist yet).
    # In GitHub Actions: poll.yml restored seen_ids.json from cashe before this ran. 

    # STEP 4: find whats new
    new_listings = find_new_listings(matching, seen_ids)
    # Compares each listing's "id" against seen_ids.
    # Returns only listings whose ID is NOT in seen_ids.
    logger.info("%d are new", len(new_listings))

    # EARLY EXIT: if nothing is new, there's nothing left to do. 
    # `return` with no value exits the function immediately. 
    if not new_listings:
        logger.info("Nothing new. Done")
        return

    # STEP 5 + 6 + 7: alert and save (skipped entirely in dry_run mode)
    if dry_run:
        # Just print what we WOULD have emailed. No side effects.
        for listing in new_listings:
            logger.info("   [DRY RUN] %s | %s sek/month", listing["url"], listing["monthly_cost"])

    else:
        # STEP 5: send email
        send_alert(new_listings)
        # connects to smtp.google.com, sends one email with all new listings.

        # STEPS 6 + 7: update and save state
        save_seen_ids(mark_as_seen(new_listings, seen_ids))
        # mark_as_seen() returns seen_ids <\union> {new IDs} (set union - combines both sets)
        # save_seen_ids() writes that combines set to seen_ids.json
        # WHY SAVE AFTER SEND (not before): if the email fails, we don't mark
        # listings as seen. Next run will try to send again. Safer order.
        # In GitHub Actions: poll.yml cashes seen_ids.json after this script exits. 

        logger.info("Done.")

# ===========================================================================
# ENTRY POINT
#   if __name__ == "__main__": only runs when you execute this file directly.
#   `python main.py`    -> __name__ is "__main__" -> this block runs 
#   `import main`       -> __name__ is "main"     -> this block is skipped
# WHY THIS MATTERS: if another file ever imports something from main.py,
#   poll() won't accidentally rin as a side effect of the import.
# ============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # ArgumentParser reads sys.argv - the list of words you typed after "python main.py"

    parser.add_argument("--dry-run", action="store_true")
    # Registers --dry-run as a valid flag.
    # action="store_true" means:
    #   --dry-run present -> arg.dry_run = True
    #   --dry-run absent  -> args.dry_run = False
    # Note: argparse converts --dry-run to args.dry_run (hyphen -> underscore)

    args = parser.parse_args()
    # Actually reads the command line and populates args object.

    poll(dry_run=args.dry_run)
    # Calls poll() with True of False depending on wether --dry-run was passed.
