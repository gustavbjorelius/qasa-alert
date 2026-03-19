# scraper.py
# 
# WHAT: Fetches listings fro the Qasa GraphQL API. 
# HOW I FOUND THE API: DevTools > network tab > filtered "api.qasa" >
#   found POST requests to api.qasa.se/graphql > payload tab showed the query
#
# CONTROL FLOW: main.py calls fetch_listings() -> returns list of minimal dicts
#   -> passes to filters.py

import logging
import requests
from config import QASA_API_URL

logger = logging.getLogger(__name__)

HEADERS = {
        "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Accept":       "application/json",
        "Origin":       "https://qasa.se",
        "Referer":      "https://qasa.se",
}

# We only request the 4 fields we actually need.
# GraphQL lets you ask for exactly what you want - the server sends nothing extra.
# id            -> to build the URL and track seen listings in state.py
# furnished     -> to double-check the filter locally in filters.py
# shared        -> to double-check the filter locally in filters.py
# monthly_cost   -> to ...
# We do NOT request: location, uploads, squareMeters, etc
GRAPHQL_QUERY = """
query HomeSearch($order: HomeIndexSearchOrderInput, $offset: Int, $limit: Int, $params: HomeSearchParamsInput) {
    homeIndexSearch(order: $order, params: $params) {
        documents(offset: $offset, limit: $limit) {
            nodes {
                id
                furnished
                shared
                monthly_cost
            }
        }
    }
}
"""

# These variables tell the Qasa server what to filter BEFORE sending data back. 
# The server does the heavy work. We only receive listings that already match. 
# Our local checks in filters.py are just a safety net on top. 
# FROM: DevToos -> Payload tab -> variables section (exact keys and values). 
# furnished/shared are booleans (true/false in JSON -> True/False in Python).
# areaIdentifier "se/haninge_kommun" - visible in DevTools Payload.
GRAPHQL_VARIABLES = {
        "limit": 100,
        "offset": 0,
        "order": {
            "direction": "decsending",
            "orderBy":   "published_or_bumped_at",
        },
        "params": {
            "furniture":           True,
            "shared":               False,
            "maxMonthlyCost":       8900,
            "currency":             "SEK",
            "areaIdentifier":       ["se/haninge_kommun"],
            "markets":              ["sweden"],
        },
}


def fetch_listings():
    # POST to the GraphQL endpoint. Returns a list of minimal dicts.
    # Returns [] on any error so the program keeps running. 
    try:
        response = requests.post(
                QASA_API_URL,
                headers=HEADERS,
                json={
                    "operationName":    "HomeSearch",
                    "query":            GRAPHQL_QUERY,
                    "variables":         GRAPHQL_VARIABLES,
                },
                timeout=15,
            )
        response.raise_for_status()
        data = response.json()

        # Path comes from the JSON response structure: data -> homeIndexSearch -> documents -> nodes
        nodes = (
                data
                .get("data",{})
                .get("homeIndexSearch",{})
                .get("documents",{})
                .get("nodes",[])
            )

        return [_normalize(node) for node in nodes]

    except requests.HTTPError as e:
        logger.error("HTTP error: %s", e)
    except requests.ConnectionError:
        logger.error("No connecion to %s", QASA_API_URL)
    except (KeyError, ValueError) as e:
        logger.error("Unexpected response shape: %s", e)

    return []

def _normalize(raw):
    # Converts one raw API node into a flat dict with only what we need. 
    # str(id) because IDs from APIs are sometimes ints - always store as string
    # for consistent comparison in state.py.
    listing_id = str(raw.get("id", ""))
    return {
            "id":           listing_id,
            "furnished":    bool(raw.get("furnished")),
            "shared":       bool(raw.get("shared")),
            "monthlyCost":  int(raw.get("monthlyCost") or 0),
            "url":          f"https://qasa.se/se/home/{listing_id}",
            # URL pattern found by visiting any listing on qasa and reading the browser URL.
        }
