"""Batch update investors.json: remove Burry, add new investors with source field."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INV_PATH = os.path.join(ROOT, "data", "investors.json")

with open(INV_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# 1. Remove Michael Burry
data["investors"] = [inv for inv in data["investors"] if inv["id"] != "burry"]
print("✓ Burry removed")

# 2. Add source field to existing investors
for inv in data["investors"]:
    inv["source"] = "13F"

# 3. Add new investors (non-13F)
new_investors = [
    {
        "id": "musk",
        "name": "Elon Musk",
        "name_zh": "埃隆·马斯克",
        "fund": "Tesla / SpaceX / xAI",
        "source": "form4",
        "cik": "0001494730",
        "issuer_cik": "0001318605",
        "issuer_ticker": "TSLA",
        "style": "contrarian",
        "color": "#E31937",
        "initials": "EM",
        "tagline": "特斯拉CEO，世界首富。通过Form 4追踪内部人交易。",
        "filing_date": "",
        "period_of_report": "",
        "total_value_usd": 0,
        "holdings_count": 0,
        "holdings": [],
    },
    {
        "id": "trump",
        "name": "Donald Trump",
        "name_zh": "唐纳德·特朗普",
        "fund": "Trump Media & Technology Group",
        "source": "form4",
        "cik": "0001841804",
        "issuer_cik": "0001841804",
        "issuer_ticker": "DJT",
        "style": "contrarian",
        "color": "#DA291C",
        "initials": "DT",
        "tagline": "第45/47任美国总统，DJT大股东。通过Form 4追踪内部人交易。",
        "filing_date": "",
        "period_of_report": "",
        "total_value_usd": 0,
        "holdings_count": 0,
        "holdings": [],
    },
    {
        "id": "pelosi",
        "name": "Nancy Pelosi",
        "name_zh": "南希·佩洛西",
        "fund": "US House of Representatives",
        "source": "congress",
        "cik": "",
        "style": "contrarian",
        "color": "#0D6EFD",
        "initials": "NP",
        "tagline": "国会山股神。通过STOCK Act交易披露追踪，非13F。",
        "filing_date": "",
        "period_of_report": "",
        "total_value_usd": 0,
        "holdings_count": 0,
        "holdings": [],
    },
    {
        "id": "li-ka-shing",
        "name": "Li Ka-shing",
        "name_zh": "李嘉诚",
        "fund": "长江集团 (CK Hutchison / CK Asset)",
        "source": "hkex",
        "cik": "",
        "style": "value",
        "color": "#003D7C",
        "initials": "LK",
        "tagline": "香港首富，长江集团创始人。通过港交所权益披露追踪。",
        "filing_date": "",
        "period_of_report": "",
        "total_value_usd": 0,
        "holdings_count": 0,
        "holdings": [],
    },
]

data["investors"].extend(new_investors)
print(f"✓ Added {len(new_investors)} new investors: musk, trump, pelosi, li-ka-shing")

# 4. Update style labels - add form4/congress/hkex styles
if "styles" in data:
    data["styles"]["form4"] = {
        "label": "名人交易追踪",
        "description": "通过SEC Form 4追踪企业内部人买卖交易",
        "color": "#f59e0b",
    }
    data["styles"]["congress"] = {
        "label": "国会交易追踪",
        "description": "通过STOCK Act披露追踪国会议员交易",
        "color": "#0D6EFD",
    }
    data["styles"]["hkex"] = {
        "label": "港股权益追踪",
        "description": "通过港交所权益披露追踪大股东持股变动",
        "color": "#003D7C",
    }

# 5. Remove QoQ data (will be regenerated)
data.pop("qoq", None)

with open(INV_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Show summary
print(f"\nTotal investors: {len(data['investors'])}")
for inv in data["investors"]:
    print(f"  {inv['id']:18s} | {inv.get('source','13F'):8s} | {inv['name_zh']}")

print("\n✓ investors.json updated!")
