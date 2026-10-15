"""measures how accurate the sorter is, using the rows you have marked correct or wrong in supabase"""

import os
from collections import Counter

import requests


def main():
    url = os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1/inbox_log"
    key = os.environ["SUPABASE_SERVICE_KEY"]
    headers = {"apikey": key}
    if not key.startswith("sb_"):  # legacy service_role keys are jwts and also go in the authorization header
        headers["Authorization"] = f"Bearer {key}"

    rows = requests.get(url, headers=headers, params={"select": "category,priority,correct"}, timeout=15).json()
    print(f"{len(rows)} emails sorted in total")
    print("by category:", dict(Counter(r["category"] for r in rows)))
    print("by priority:", dict(Counter(r["priority"] for r in rows)))

    reviewed = [r for r in rows if r["correct"] is not None]
    if not reviewed:
        print("no emails reviewed yet: set the correct column to true or false in supabase")
        return
    right = sum(r["correct"] for r in reviewed)
    print(f"\naccuracy: {right}/{len(reviewed)} reviewed emails correct ({right / len(reviewed):.0%})")

    totals, rights = Counter(), Counter()
    for r in reviewed:
        totals[r["category"]] += 1
        rights[r["category"]] += r["correct"]
    for category in totals:
        print(f"  {category}: {rights[category]}/{totals[category]}")


if __name__ == "__main__":
    main()
