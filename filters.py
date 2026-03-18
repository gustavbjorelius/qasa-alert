# filters.py
# 
# WHAT: Decides y/n on each listing. Pure logic, no I/O. 
# WHY IT EXISTS: The API already filtered server-side via GRAPHQL-VARIABLES.
#   This is a local safeth net in case the API returns something unexpected.
# CONTROL FLOW: main.py calls apply_filters(all_listings) ->
#   returns only listings where all three conditions are True ->
#   main.py passes result to state.py

from config import FILTER_MAX_COST

def matches_criteria(listing):
    return (
            listing["furnished"] is True                       # FURNITURE PLZ
            and listing["shared"] is False                     # not shared room
            and 0 < listing["monthly_cost"] <= FILTER_MAX_COST # valid cost 
        )

def apply_filters(listings):
    return [listing for listing in listings if matches_criteria(listing)]
