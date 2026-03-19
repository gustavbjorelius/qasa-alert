# ================================================================================
# state.py
# ================================================================================
# WHAT THIS FILE DOES:
#   Remember which listings we've already alerted on. 
#   Reads and wtires a file called seen_ids.json on disk. 
#   No internet. No email. Just disk I/O.
# 
# WHERE IT FITS IN THE FLOW:
#   main.py calls load_seen_ids() to get the set of known IDs.
#   main.py calls find_new_listings() to compare agaist that set.
#   main.py calls mark_as_seen() to add new IDs.
#   In GitHub Actions, poll.yml restores seen_ids.json from cashe BEFORE
#   main.py runs, and saves it to cache AFTER main.py exits.
# 
# WHY THIS FILE EXISTS:
#   Without memory, every run would think every listing is new.
#   You'd get an email with all 13 listings every 15 minutes. Forever.
#   seen_ids.json is that memory. It grows over time as you see more listings.
# 
# WHY A JSON FILE AND NOT A DATABASE:
#   This is a simple list if ID strings. SQLite/Postgres = massive overkill. 
# ================================================================================

import json     # stdlib. reads and writes JSON files
import logging  # ? 
import os       # stdlib. checks if files exist, builds file paths. 

logger = logging.getLogger(__name__)

# os.path.dirname(__file__) = the folder containing this script.
# os.path.join() builds a file path correctly for the OS.
# Result: seen_ids.json lives in the same filder as state.py
# WHY NOT just "seen_ids.json": if you run the script from a fifferent
# directory (e.g. python ~/qasa-alert/main.py from your home folder),
# a relative path woyld create the file in the wrong place.
STATE_FILE = os.path.join(os.path.dirname(__file__), "seen_ids.json")

# ==============================================================================
# load_seen_ids()
# CALLED BY: main.py - third step in poll()
# RETURNS: a Pythin set of ID strings (e.g. {"1211129", "1317253", "1315013",})
#
# WHY A SET NOT A LIST:
#   Sets have O(1) lookup - checking "is this ID in the set" takes the same
#   time wheather the set has 10 or 10,000 items. Lists are O(n) - slower
#   as they grow. For this use case the difference is tiny, but set is correct.
#   Also, sets automatically deduplicate - no ID can appear twice. 
# ==============================================================================
def load_seen_ids():
    if not os.path.exists(STATE_FILE):
        return set()    # first ever run - no file yet, nothing seen
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)     # reads the file, parses JSON -> Python list
            return set(data)        # convert list to set for fast lookup
    except (json.JSONDecodeError, TypeError) as e:
        # File exists but is corrupted or empty. Start fresh rather than craching
        logger.warning("Could not read file, start fresh: %s", e)
        return set()

# ================================================================================
# save_seen_ids(ids)
# CALLED BY: main.py - last step in poll(), only if not dry_run
# RECEIVES: updated set of all seen IDs
# WRITES: seen_ids.json to disk
#
# WHY json.dump(list(ids)): JSON doesn't support Python sets.
#   We convert set -> list before writing. When we read it back in
#   load_seen_ids(), we convert list -> set again.
# ===============================================================================
def save_seen_ids(ids):
    with open(STATE_FILE, "w") as f:
        json.dump(list(ids), f, indent=2)
        # indent=2 makes the file human-readable (each ID in its own line).
        # Without indent, it'd be one long line. Doesn't affect functionality. 

# ===============================================================================
# find_new_listings(listings, new_ids)
# CALLED BY: main.py - fourth step in poll()
# RECEIVES: filtered listing list (from filters.py), set of seen IDs (from dick)
# RETURNS: list if listings whise ID is NOT in seen_ids
#
# `not in` on a set is O(1) - fast.
# This is the core of the deduplication logic.
# ================================================================================
def find_new_listings(listings, seen_ids):
    return [listing for listing in listings if listing["id"] not in seen_ids]

# ================================================================================
# mark_as_seen(listings, seen_ids)
# CALLED BY: main.py - after send_alert(), only if not dry_run
# RECEIVES: list of new listings, current seen_ids set
# RETURNS: new set = old seen_ids the IDs of new listings
#
# SET UNION WITH |:
#   {listing["id"] for listing in listings} is a set comrehension - builds a set of IDs.
#   seen_ids | new_ids combinesjboth sets into one (union).
#   Does NOT modify either otiginal set - returns a new one. 
#   main.py then passes this to save_seen_ids().
#
# WHY RETURN A NEW SET not modify seen_ids directly:
#   Functions that return new values instead of midifying inputs are easier
#   to reason about and test. This ia a functional programming pattern. 
# ==================================================================================
def mark_as_seen_(listings, seen_ids):
    new_ids = {listing["id"] for listing in listings}
    return seen_ids | new_ids
