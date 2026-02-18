"""
process_nautica_data.py

Reads today's scraped data (data/nautica_raw.xlsx) and adds it to the
starting values (data/starting_values.json) to produce an updated
output (data/nautica_processed.json).

Flow:
  1. Parse today's daily report from FusionSolar
  2. Load starting values (monthly + lifetime baselines)
  3. Add today's values to the current month
  4. Recalculate lifetime for current year (sum of all months in that year)
  5. Save updated nautica_processed.json
  6. Update starting_values.json so next run builds on today's totals
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd


# ── Fields that are summed when adding daily data ──────────────────────────
ADDITIVE_FIELDS = [
    "PV Yield (kWh)",
    "Inverter Yield (kWh)",
    "Export (kWh)",
    "Import (kWh)",
    "Consumption (kWh)",
    "Self-consumption (kWh)",
    "CO₂ Avoided (t)",
    "Standard Coal Saved (t)",
    "Revenue (R.)",
    "Charge (kWh)",
    "Discharge (kWh)",
    "Theoretical Yield (kWh)",
    "Loss Due to Export Limitation (kWh)",
    "Loss Due to Export Limitation(R.)",
]

# ── Fields where we take the max ───────────────────────────────────────────
MAX_FIELDS = [
    "Peak Power (kW)",
]

# ── Fields that are recalculated from other fields ─────────────────────────
# Self-consumption Rate = (Self-consumption / PV Yield) * 100


def parse_daily_report(filepath):
    """Parse the daily xlsx download from FusionSolar.
    
    The file has the same structure as the monthly report:
    Row 0: Title row
    Row 1: Column headers
    Row 2+: Data rows (typically 1 row for a daily report)
    """
    df = pd.read_excel(filepath, header=None, sheet_name=0)
    headers = df.iloc[1].tolist()
    
    # Sum all data rows (in case there are multiple days)
    combined = {}
    row_count = 0
    
    for idx in range(2, len(df)):
        row = df.iloc[idx]
        period = str(row.iloc[0]) if not pd.isna(row.iloc[0]) else ""
        
        for i, h in enumerate(headers):
            if pd.isna(h) or h in ['Statistical Period', 'Total String Capacity (kWp)']:
                continue
            key = str(h).strip()
            val = float(row.iloc[i]) if not pd.isna(row.iloc[i]) else 0.0
            
            if key in ADDITIVE_FIELDS:
                combined[key] = combined.get(key, 0.0) + val
            elif key in MAX_FIELDS:
                combined[key] = max(combined.get(key, 0.0), val)
            else:
                # For non-additive fields, keep last value
                combined[key] = val
        
        row_count += 1
        print(f"  📊 Parsed row: {period}")
    
    if row_count == 0:
        print("  ⚠️  No data rows found in daily report")
        return None
    
    print(f"  ✅ Parsed {row_count} row(s) from daily report")
    return combined


def add_daily_to_month(monthly_data, daily_data):
    """Add daily values to monthly totals."""
    updated = dict(monthly_data)
    
    for field in ADDITIVE_FIELDS:
        daily_val = daily_data.get(field, 0.0)
        monthly_val = updated.get(field, 0.0)
        updated[field] = round(monthly_val + daily_val, 3)
    
    for field in MAX_FIELDS:
        daily_val = daily_data.get(field, 0.0)
        monthly_val = updated.get(field, 0.0)
        updated[field] = round(max(monthly_val, daily_val), 3)
    
    # Recalculate self-consumption rate
    pv_yield = updated.get("PV Yield (kWh)", 0.0)
    self_consumption = updated.get("Self-consumption (kWh)", 0.0)
    if pv_yield > 0:
        updated["Self-consumption Rate (%)"] = round((self_consumption / pv_yield) * 100, 3)
    
    return updated


def recalculate_lifetime_year(monthly_data, year_str):
    """Recalculate a lifetime year entry by summing all months in that year."""
    year_total = {}
    
    # Find all months for this year
    matching_months = {k: v for k, v in monthly_data.items() if k.startswith(year_str)}
    
    if not matching_months:
        return None
    
    for month_key, month_vals in matching_months.items():
        for field in ADDITIVE_FIELDS:
            year_total[field] = year_total.get(field, 0.0) + month_vals.get(field, 0.0)
        for field in MAX_FIELDS:
            year_total[field] = max(year_total.get(field, 0.0), month_vals.get(field, 0.0))
    
    # Round all values
    for key in year_total:
        year_total[key] = round(year_total[key], 3)
    
    # Recalculate self-consumption rate for the year
    pv_yield = year_total.get("PV Yield (kWh)", 0.0)
    self_consumption = year_total.get("Self-consumption (kWh)", 0.0)
    if pv_yield > 0:
        year_total["Self-consumption Rate (%)"] = round((self_consumption / pv_yield) * 100, 3)
    
    return year_total


def calculate_all_time_totals(lifetime_data):
    """Calculate grand totals across all years."""
    totals = {}
    
    for year_key, year_vals in lifetime_data.items():
        for field in ADDITIVE_FIELDS:
            totals[field] = totals.get(field, 0.0) + year_vals.get(field, 0.0)
        for field in MAX_FIELDS:
            totals[field] = max(totals.get(field, 0.0), year_vals.get(field, 0.0))
    
    # Round
    for key in totals:
        totals[key] = round(totals[key], 3)
    
    # Recalculate rate
    pv_yield = totals.get("PV Yield (kWh)", 0.0)
    self_consumption = totals.get("Self-consumption (kWh)", 0.0)
    if pv_yield > 0:
        totals["Self-consumption Rate (%)"] = round((self_consumption / pv_yield) * 100, 3)
    
    return totals


def main():
    data_dir = Path("data")
    raw_file = data_dir / "nautica_raw.xlsx"
    starting_file = data_dir / "starting_values.json"
    output_file = data_dir / "nautica_processed.json"
    
    print("🔄 Processing Nautica data...")
    
    # ── Load today's daily data ────────────────────────────────────────────
    if not raw_file.exists():
        print(f"❌ Daily report not found: {raw_file}")
        sys.exit(1)
    
    print(f"📥 Reading daily report: {raw_file}")
    daily_data = parse_daily_report(raw_file)
    if daily_data is None:
        print("❌ No data to process")
        sys.exit(1)
    
    # Show key daily values
    print(f"  ⚡ PV Yield today:      {daily_data.get('PV Yield (kWh)', 0):,.2f} kWh")
    print(f"  📤 Export today:         {daily_data.get('Export (kWh)', 0):,.2f} kWh")
    print(f"  📥 Import today:         {daily_data.get('Import (kWh)', 0):,.2f} kWh")
    print(f"  🏠 Consumption today:    {daily_data.get('Consumption (kWh)', 0):,.2f} kWh")
    print(f"  💰 Revenue today:        R {daily_data.get('Revenue (R.)', 0):,.2f}")
    
    # ── Load starting values ───────────────────────────────────────────────
    if not starting_file.exists():
        print(f"❌ Starting values not found: {starting_file}")
        sys.exit(1)
    
    print(f"📥 Reading starting values: {starting_file}")
    with open(starting_file, "r") as f:
        starting = json.load(f)
    
    monthly = starting["monthly"]
    lifetime = starting["lifetime"]
    
    # ── Determine current month key ────────────────────────────────────────
    now = datetime.now()
    current_month_key = now.strftime("%Y-%m")
    current_year_key = now.strftime("%Y")
    
    print(f"📅 Current month: {current_month_key}")
    print(f"📅 Current year:  {current_year_key}")
    
    # ── Add today to current month ─────────────────────────────────────────
    if current_month_key not in monthly:
        print(f"  ℹ️  New month {current_month_key} - starting fresh")
        monthly[current_month_key] = {}
    
    print(f"📊 Updating monthly data for {current_month_key}...")
    monthly[current_month_key] = add_daily_to_month(
        monthly[current_month_key], daily_data
    )
    
    month_pv = monthly[current_month_key].get("PV Yield (kWh)", 0)
    print(f"  ⚡ Month-to-date PV Yield: {month_pv:,.2f} kWh")
    
    # ── Recalculate lifetime for current year ──────────────────────────────
    print(f"📊 Recalculating lifetime for {current_year_key}...")
    year_totals = recalculate_lifetime_year(monthly, current_year_key)
    if year_totals:
        # Preserve any lifetime-only fields (like Equivalent Trees Planted)
        if current_year_key in lifetime:
            for key in lifetime[current_year_key]:
                if key not in year_totals:
                    year_totals[key] = lifetime[current_year_key][key]
        lifetime[current_year_key] = year_totals
    
    year_pv = lifetime.get(current_year_key, {}).get("PV Yield (kWh)", 0)
    print(f"  ⚡ Year-to-date PV Yield: {year_pv:,.2f} kWh")
    
    # ── Calculate all-time totals ──────────────────────────────────────────
    all_time = calculate_all_time_totals(lifetime)
    total_pv = all_time.get("PV Yield (kWh)", 0)
    print(f"  ⚡ All-time PV Yield:     {total_pv:,.2f} kWh")
    
    # ── Load yesterday's data ─────────────────────────────────────────────
    # Check new key first, fall back to old key for backward compatibility
    yesterday_data = starting.get("yesterday", None)
    yesterday_date = starting.get("yesterday_date", "")
    
    # Backward compat: if old key exists but new key doesn't, migrate
    if yesterday_data is None and "previous_today" in starting:
        prev_date = starting.get("previous_today_date", "")
        today_date = now.strftime("%Y-%m-%d")
        if prev_date and prev_date != today_date:
            # The old previous_today is actually yesterday's data
            yesterday_data = starting["previous_today"]
            yesterday_date = prev_date
            print(f"  📅 Migrated yesterday from previous_today ({prev_date})")
    
    # ── Build output ───────────────────────────────────────────────────────
    output = {
        "plant": "Nautica Shopping Centre",
        "last_updated": now.strftime("%Y-%m-%d %H:%M"),
        "yesterday": {
            "date": yesterday_date,
            "data": {k: round(v, 2) for k, v in yesterday_data.items()}
        } if yesterday_data else None,
        "today": {
            "date": now.strftime("%Y-%m-%d"),
            "data": {k: round(v, 2) for k, v in daily_data.items()}
        },
        "current_month": {
            "period": current_month_key,
            "data": {k: round(v, 2) for k, v in monthly[current_month_key].items()}
        },
        "monthly": {
            k: {fk: round(fv, 2) for fk, fv in v.items()}
            for k, v in sorted(monthly.items())
        },
        "lifetime": {
            k: {fk: round(fv, 2) for fk, fv in v.items()}
            for k, v in sorted(lifetime.items())
        },
        "all_time_totals": {k: round(v, 2) for k, v in all_time.items()}
    }
    
    # ── Save output ────────────────────────────────────────────────────────
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"✅ Output saved to: {output_file}")
    
    # ── Hourly generation tracking ──────────────────────────────────────────
    hourly_file = data_dir / "hourly_generation.json"
    try:
        if hourly_file.exists():
            with open(hourly_file, "r") as f:
                hourly_gen = json.load(f)
        else:
            hourly_gen = {"days": {}, "last_snapshot": None}
        
        today_date = now.strftime("%Y-%m-%d")
        current_hour = now.hour
        current_pv = daily_data.get("PV Yield (kWh)", 0.0)
        
        # Ensure today's entry exists with 24 zeros
        if today_date not in hourly_gen["days"]:
            hourly_gen["days"][today_date] = [0.0] * 24
        
        # Calculate increment from last snapshot
        last = hourly_gen.get("last_snapshot")
        if last and last.get("date") == today_date:
            increment = max(0.0, current_pv - last.get("pv_kwh", 0.0))
        else:
            # First run of the day — all generation so far is attributed to this hour
            increment = current_pv
        
        hourly_gen["days"][today_date][current_hour] = round(increment, 2)
        hourly_gen["last_snapshot"] = {
            "date": today_date,
            "hour": current_hour,
            "pv_kwh": round(current_pv, 2)
        }
        
        # Calculate monthly hourly averages (for expected values)
        current_month_prefix = now.strftime("%Y-%m")
        month_days = {d: hrs for d, hrs in hourly_gen["days"].items()
                      if d.startswith(current_month_prefix) and d != today_date}
        
        hourly_averages = [0.0] * 24
        if month_days:
            for hour in range(24):
                values = [hrs[hour] for hrs in month_days.values() if hour < len(hrs) and hrs[hour] > 0]
                hourly_averages[hour] = round(sum(values) / len(values), 2) if values else 0.0
        
        hourly_gen["monthly_averages"] = {current_month_prefix: hourly_averages}
        hourly_gen["current_hour"] = current_hour
        
        # Prune old data (keep last 90 days)
        cutoff = (now - __import__('datetime').timedelta(days=90)).strftime("%Y-%m-%d")
        hourly_gen["days"] = {d: v for d, v in hourly_gen["days"].items() if d >= cutoff}
        
        with open(hourly_file, "w") as f:
            json.dump(hourly_gen, f, indent=2)
        print(f"✅ Hourly generation updated: hour {current_hour}, increment {increment:.2f} kWh")
        
    except Exception as e:
        print(f"⚠️  Hourly tracking error (non-fatal): {e}")
    
    # ── Add hourly data to output ───────────────────────────────────────────
    try:
        output["hourly"] = {
            "today": hourly_gen["days"].get(today_date, [0.0] * 24),
            "current_hour": current_hour,
            "monthly_averages": hourly_gen.get("monthly_averages", {}).get(current_month_prefix, [0.0] * 24)
        }
        # Re-save output with hourly data
        with open(output_file, "w") as f:
            json.dump(output, f, indent=2)
    except Exception as e:
        print(f"⚠️  Hourly output error (non-fatal): {e}")
    
    # ── Update starting values for next run ────────────────────────────────
    starting["monthly"] = monthly
    starting["lifetime"] = lifetime
    starting["last_updated"] = now.strftime("%Y-%m-%d")
    
    # Only rotate today→yesterday when the date actually changes
    prev_today_date = starting.get("previous_today_date", "")
    today_date = now.strftime("%Y-%m-%d")
    
    if prev_today_date and prev_today_date != today_date:
        # Date changed — yesterday becomes the final snapshot from previous day
        starting["yesterday"] = starting.get("previous_today", {})
        starting["yesterday_date"] = prev_today_date
        print(f"  📅 Rotated yesterday: {prev_today_date}")
    
    # Always update today's running snapshot
    starting["previous_today"] = daily_data
    starting["previous_today_date"] = today_date
    
    with open(starting_file, "w") as f:
        json.dump(starting, f, indent=2)
    print(f"✅ Starting values updated: {starting_file}")
    
    print("✅ Processing complete!")


if __name__ == "__main__":
    main()
