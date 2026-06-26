"""
fetch_usbr.py
-------------
Standalone fetch of Lake Powell daily elevation from the USBR RISE API
(catalog item 508). Same logic as the notebook, runnable on its own:

    python src/fetch_usbr.py

Writes data/usbr_lake_powell_elevation.csv. If the API param names have changed,
download the CSV manually from https://data.usbr.gov/catalog/2362/item/508 and
skip this script.
"""
import os
import sys

try:
    import requests
    import pandas as pd
except ImportError:
    sys.exit("Install deps first:  pip install requests pandas")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "usbr_lake_powell_elevation.csv")


def fetch_usbr_elevation(item_id=508, after="1984-01-01", before="2026-06-30"):
    url = "https://data.usbr.gov/rise/api/result"
    params = {"itemId": item_id, "after": after, "before": before,
              "order[dateTime]": "ASC", "itemsPerPage": 10000, "page": 1}
    headers = {"Accept": "application/vnd.api+json"}
    rows = []
    while True:
        r = requests.get(url, params=params, headers=headers, timeout=90)
        r.raise_for_status()
        data = r.json().get("data", [])
        if not data:
            break
        for d in data:
            a = d["attributes"]
            rows.append((a.get("dateTime"), a.get("result")))
        if len(data) < params["itemsPerPage"]:
            break
        params["page"] += 1
    out = pd.DataFrame(rows, columns=["dateTime", "elevation_ft"])
    out["date"] = pd.to_datetime(out["dateTime"]).dt.tz_localize(None)
    return out.dropna(subset=["elevation_ft"])[["date", "elevation_ft"]]


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    df = fetch_usbr_elevation()
    df.to_csv(OUT, index=False)
    print(f"Wrote {OUT}: {len(df)} rows, "
          f"{df.date.min().date()} to {df.date.max().date()}")
