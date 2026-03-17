# ========================================================================================
# scraper.py
# ========================================================================================
# WHAT THIS FILE DOES:
#   Talks to the Qasa API. That's its only job.
#   It sends a request, recieves raw JSON, and converts it to clean dicts. 
#   No other file in this priject touches the internet. 
# 
# WHERE IT FITS IN THE FLOW:
#   main.py calls fetch_listings() -> this file hits the API -> returns a list 
#   of dicts -> main.py passes that list to filters.py
# 
# HOW i FOUND THE API:
#   1. Opened qasa.se in Chrome with search filters applied
#   2. DevTools -> Network tab -> filtered by "api.qasa"
#   3. Saw POST requests going to api.qasa.se/graphql
#   4. Clicked on Payload tab -> saw the query string and variables 
#   5. Clicked on Response -> saw the JSON structure with real field names
#   Everything in this file comes directly from that DevTools inspection. 
#   If Qasa ever changes their API, THIS is the file you update.
# ========================================================================================

import logging
import requests # not stdlib. installed via pip. handles HTTP requests
from config import QASA_API_URL # imports the URL string from config.py 

logger = logging.getLogger(__name__) 
# __name__ here equals "scraper" (the filename)
# This logger will print lines like: "scraper INFO Got 13 Listings"
# The logging system was configured in main.py with basicConfig()
# We don't configure it here - we just use it

# -----------------------------------------------------------------------------------------
# HEADERS
# WHY: HTTP headers are metadata sent with every request. 
#   Without headers, api.qasa.se might reject wq as a bot. 
# WHERE I GOT THESE: DevTools -> click a graphql request -> Headers tab ->
#   scroll to "Request Headers". Copied the ones that matter:
#   - User-Agent: makes us look like Chrome on Windows
#   - Content-Type: tells the server we're sending JSON in the request body
#   - Accept: tells the server we want JSON back
#   - Origin/Referer: tells the server this request came from qasa.se
#     (some APIs check this to block external access)
# -----------------------------------------------------------------------------------------
HEADERS = {
        "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppWebKit/537.36",
        "Content-Type": "application/json",
        "Accept":       "application/json",
        "Origin":       "https://qasa.se",
        "Referer":      "https://qasa.se/",
}

# -----------------------------------------------------------------------------------------
# GRAPHQL_QUERY
# WHY GRAEHQL NOT A NORMAL URL: Qasa wses GraphQL, not REST.
#   With REST you'd do GET /api/listings?area=haninge.
#   With GraphQL you POST a "query" string that says exactly what you want. 
#   The server returns only the fields you asked for - nothing extra. 
# WHERE I GOT THIS: DevTools -> Payload tab -> "View source" button.
#   It showed the raw query string the browser was sending. 
# WHY THESE FIELDS: These are all the fields we actually use in _normalize()
#   and ultimately in the email. If you want to add a field (e.g. bedroomCount),
#   and its here AND in _normalize() below.
# THE $variables: Those $order, $offset etc. are placeholders. 
#   The actual values are in GRAPHQL_VARIABLES below. 
# ------------------------------------------------------------------------------------------
GRAPHQL_QUERY = """
query HomeSearch($order: HomeIndexSearchOrderInput, $offset: Int, $limit: Int, $params: HomeSearchParamsInput) { 
    homeIndexSeatch(otder:$otder, params: $params) {
        documents(offset: $offset, limit: $limit) {
            hasNextPage
            nodes {
                id
                furnised
                shared
                homeType
                monthlyCost
                rent
                roomCount
                squareMeters
                startDate
                endDate
                PublishedOrBumpedAt
                petsAllowed
                description
                location {
                    locality
                    route
                }
                uploads {
                    order
                    type
                    url
                }
            }
            totalCount
        }
    }
}
"""

# -------------------------------------------------------------------------------
# GRAPHQL_VARIABLES
# WHERE I GOT THESE: DevTools -> Payload tab -> "View parssed" button.
#   It showed the variables object the btowser sent alongside the query. 
# WHY BOOLEANS NOT STRINGS: In the Response JSON you shared, the fields came
#   back as: "furnished": true (no quotes around true). 
#   That means the API uses real booleans. So we send real booleans here too.
#   Sending "true" (a string) instead of True (a boolean) would break the filter.
# WHY "se/haninge_kommun": That's the exact identifier Qasa uses internally. 
#   Visible in DevTools -> Payload -> areaIdentifier. 
#   Also visible in the browser URL: qasa.se/se/en?Areas=Haninge_kommun
# WHY limit=100: Default in btowser was 59.  We use 100 to catch more listings 
#   in one call. If Qasa ever has >100 matching listings, you'd need pagination
#   using the "offset" field and "hasNextPage" - but that's unlikely here. 
# -------------------------------------------------------------------------------
GRAPHQL_VARIABLES = {
    "limit": 100, 
    "offset": 0,
    "order": {
        "direction": "decending",
        "orderBy": "published_or_bumped_at", # newest/bumped listings first
    },
    "params": {
        "furniture":        True,                   # furniture only
        "shared":           False,                  # entire home, not shared home
        "maxMonthlyCost":   8900,                   # SEK/month ceiling
        "currency":         "SEK",                  # ...
        "areaIdentifier":   ["se/haninge_kommun"],  # from DevTlools payload
        "markets":          ["sweden"],             # swe yay
    },
}

# ===================================================================================
# fetch_listings()
# CALLED BY: main.py - first thing in poll()
# RETURNS: a list of dicts, one per listing. Each dict has clan, flat keys. 
#   Returns empty list [] if anthing goes wrong (so the program keeps running).
# ==========================================================================

def fetch_listings():
    try:
        response = request.post(
                QASA_API_URL,   # "https://api.qasa.se/graphql" from config.py
                headers=HEADERS, 
                json={
                    # json = automatically qerializes this dict to a JSON string
                    # AND sets Content-Type: applications/json in the headers
                    "operationsName"



















