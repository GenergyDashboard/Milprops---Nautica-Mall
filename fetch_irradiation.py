"""
fetch_irradiation.py

Fetches today's hourly direct irradiation data from Open-Meteo API
for Nautica Shopping Centre and stores it in data/irradiation_data.json.

Accumulates daily records over time so the dashboard can show
irradiation history alongside generation data.

API: https://api.open-meteo.com/v1/forecast
Location: Nautica Shopping Centre, Saldanha Bay, Western Cape
"""

import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path


# ── Configuration ──────────────────────────────────────────────────────────
LATITUDE = -33.044243932480015
LONGITUDE = 18.05229423974645
TIMEZONE = "Africa/Johannesburg"

FORECAST_API = "https://api.open-meteo.com/v1/forecast"

DATA_DIR = Path("data")
IRRADIATION_FILE = DATA_DIR / "irradiation_data.json"


def fetch_today_irradiation():
    """Fetch today's hourly direct irradiation from Open-Meteo API."""
    url = (
        f"{FORECAST_API}"
        f"?latitude={LATITUDE}"
        f"&longitude={LONGITUDE}"
        f"&hourly=direct_radiation"
        f"&forecast_days=1"
        f"&timezone={TIMEZONE}"
    )

    print(f"🌤️  Fetching irradiation from Open-Meteo API...")
    print(f"📍 Location: {LATITUDE}, {LONGITUDE}")

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read())
    except Exception as e:
        print(f"❌ API request failed: {e}")
        return None

    # Parse response
    timestamps = data["hourly"]["time"]
    radiation_values = data["hourly"]["direct_radiation"]

    # Build hourly array (24 hours, W/m²)
    hourly = []
    for ts, val in zip(timestamps, radiation_values):
        hour = int(ts.split("T")[1].split(":")[0])
        hourly.append({
            "hour": hour,
            "direct_radiation_wm2": round(val, 1) if val is not None else 0.0
        })

    # Calculate daily summary
    values = [h["direct_radiation_wm2"] for h in hourly]
    daily_total_wh = round(sum(values), 1)          # Wh/m² (since each reading is 1hr)
    daily_total_kwh = round(daily_total_wh / 1000, 3)  # kWh/m²
    peak_wm2 = round(max(values), 1)
    sun_hours = sum(1 for v in values if v > 10)     # Hours with meaningful radiation

    date_str = timestamps[0].split("T")[0]

    print(f"📅 Date: {date_str}")
    print(f"☀️  Peak irradiation: {peak_wm2} W/m²")
    print(f"⚡ Daily total: {daily_total_wh} Wh/m² ({daily_total_kwh} kWh/m²)")
    print(f"🕐 Sun hours (>10 W/m²): {sun_hours}h")

    return {
        "date": date_str,
        "hourly": values,
        "peak_wm2": peak_wm2,
        "daily_total_wh_m2": daily_total_wh,
        "daily_total_kwh_m2": daily_total_kwh,
        "sun_hours": sun_hours
    }


def load_existing_data():
    """Load existing irradiation history."""
    if IRRADIATION_FILE.exists():
        with open(IRRADIATION_FILE, "r") as f:
            return json.load(f)
    return {
        "plant": "Nautica Shopping Centre",
        "location": {
            "latitude": LATITUDE,
            "longitude": LONGITUDE
        },
        "timezone": TIMEZONE,
        "daily_records": {}
    }


def main():
    print("🌤️  Nautica Shopping Centre - Irradiation Data")
    print("=" * 50)

    DATA_DIR.mkdir(exist_ok=True)

    # Fetch today's data
    today = fetch_today_irradiation()
    if today is None:
        print("❌ Failed to fetch irradiation data")
        sys.exit(1)

    # Load existing history
    data = load_existing_data()

    # Add/update today's record
    date_key = today["date"]
    data["daily_records"][date_key] = {
        "hourly_wm2": today["hourly"],
        "peak_wm2": today["peak_wm2"],
        "daily_total_wh_m2": today["daily_total_wh_m2"],
        "daily_total_kwh_m2": today["daily_total_kwh_m2"],
        "sun_hours": today["sun_hours"]
    }

    data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Calculate monthly summary for current month
    now = datetime.now()
    month_key = now.strftime("%Y-%m")
    month_days = {k: v for k, v in data["daily_records"].items() if k.startswith(month_key)}

    if month_days:
        month_total_kwh = round(sum(d["daily_total_kwh_m2"] for d in month_days.values()), 3)
        month_avg_peak = round(sum(d["peak_wm2"] for d in month_days.values()) / len(month_days), 1)
        month_avg_sun = round(sum(d["sun_hours"] for d in month_days.values()) / len(month_days), 1)

        if "monthly_summary" not in data:
            data["monthly_summary"] = {}

        data["monthly_summary"][month_key] = {
            "days_recorded": len(month_days),
            "total_kwh_m2": month_total_kwh,
            "avg_peak_wm2": month_avg_peak,
            "avg_sun_hours": month_avg_sun
        }

        print(f"\n📊 Month summary ({month_key}):")
        print(f"  📅 Days recorded: {len(month_days)}")
        print(f"  ⚡ Total: {month_total_kwh} kWh/m²")
        print(f"  ☀️  Avg peak: {month_avg_peak} W/m²")
        print(f"  🕐 Avg sun hours: {month_avg_sun}h")

    # Save
    with open(IRRADIATION_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\n✅ Saved to {IRRADIATION_FILE}")
    print(f"📊 Total days in history: {len(data['daily_records'])}")


if __name__ == "__main__":
    main()
