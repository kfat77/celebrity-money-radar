#!/usr/bin/env python3
"""Add new Capitol Trades politicians to investors.json"""

import json
from datetime import datetime, timezone

# New politician data
NEW = [
    {
        'id': 'sheldon-whitehouse',
        'name': 'Sheldon Whitehouse',
        'name_zh': '谢尔登·怀特豪斯',
        'fund': 'US Senate (RI)',
        'source': 'STOCK Act',
        'cik': '',
        'style': 'congress',
        'color': '#0D6EFD',
        'initials': 'SW',
        'tagline': 'A级国会交易者#1，alpha +638%极端异常值，350笔交易，43%胜率。COHR/MU买入，NVDA卖出。',
        'filing_date': '2026-08-03',
        'period_of_report': '2026-07-31',
        'total_value_usd': 2540000.0,
        'holdings_count': 8,
        'holdings': [
            {'ticker': 'COHR', 'name': 'COHERENT CORP', 'value_usd': 450000, 'weight': 17.7, 'shares': 1},
            {'ticker': 'MU', 'name': 'MICRON TECHNOLOGY', 'value_usd': 400000, 'weight': 15.7, 'shares': 1},
            {'ticker': 'AAPL', 'name': 'APPLE INC', 'value_usd': 380000, 'weight': 15.0, 'shares': 1},
            {'ticker': 'NVDA', 'name': 'NVIDIA CORP', 'value_usd': 350000, 'weight': 13.8, 'shares': 1},
            {'ticker': 'LOW', 'name': 'LOWES COMPANIES INC', 'value_usd': 300000, 'weight': 11.8, 'shares': 1},
            {'ticker': 'ORCL', 'name': 'ORACLE CORP', 'value_usd': 280000, 'weight': 11.0, 'shares': 1},
            {'ticker': 'JPM', 'name': 'JPMORGAN CHASE', 'value_usd': 200000, 'weight': 7.9, 'shares': 1},
            {'ticker': 'HD', 'name': 'HOME DEPOT INC', 'value_usd': 180000, 'weight': 7.1, 'shares': 1},
        ]
    },
    {
        'id': 'pete-sessions',
        'name': 'Pete Sessions',
        'name_zh': '皮特·塞申斯',
        'fund': 'US House (TX-17)',
        'source': 'STOCK Act',
        'cik': '',
        'style': 'congress',
        'color': '#0D6EFD',
        'initials': 'PS',
        'tagline': 'A级#2，alpha +55.5%，378笔交易，41%胜率。NVDA/MSFT重仓。',
        'filing_date': '2026-07-27',
        'period_of_report': '2026-07-24',
        'total_value_usd': 3250000.0,
        'holdings_count': 7,
        'holdings': [
            {'ticker': 'NVDA', 'name': 'NVIDIA CORP', 'value_usd': 800000, 'weight': 24.6, 'shares': 1},
            {'ticker': 'MSFT', 'name': 'MICROSOFT CORP', 'value_usd': 600000, 'weight': 18.5, 'shares': 1},
            {'ticker': 'ARCC', 'name': 'ARES CAPITAL CORP', 'value_usd': 450000, 'weight': 13.8, 'shares': 1},
            {'ticker': 'VZ', 'name': 'VERIZON COMMUNICATIONS', 'value_usd': 400000, 'weight': 12.3, 'shares': 1},
            {'ticker': 'DHR', 'name': 'DANAHER CORP', 'value_usd': 350000, 'weight': 10.8, 'shares': 1},
            {'ticker': 'JNJ', 'name': 'JOHNSON & JOHNSON', 'value_usd': 350000, 'weight': 10.8, 'shares': 1},
            {'ticker': 'MO', 'name': 'ALTRIA GROUP INC', 'value_usd': 300000, 'weight': 9.2, 'shares': 1},
        ]
    },
    {
        'id': 'dwight-evans',
        'name': 'Dwight Evans',
        'name_zh': '德怀特·埃文斯',
        'fund': 'US House (PA-03)',
        'source': 'STOCK Act',
        'cik': '',
        'style': 'congress',
        'color': '#0D6EFD',
        'initials': 'DE',
        'tagline': 'A级#3，alpha +33.4%，177笔交易，44%胜率。NVDA买入+大量科技股卖出。',
        'filing_date': '2026-06-25',
        'period_of_report': '2026-06-10',
        'total_value_usd': 330000.0,
        'holdings_count': 8,
        'holdings': [
            {'ticker': 'NVDA', 'name': 'NVIDIA CORP', 'value_usd': 60000, 'weight': 18.2, 'shares': 1},
            {'ticker': 'MSFT', 'name': 'MICROSOFT CORP', 'value_usd': 50000, 'weight': 15.2, 'shares': 1},
            {'ticker': 'GD', 'name': 'GENERAL DYNAMICS', 'value_usd': 45000, 'weight': 13.6, 'shares': 1},
            {'ticker': 'INTC', 'name': 'INTEL CORP', 'value_usd': 40000, 'weight': 12.1, 'shares': 1},
            {'ticker': 'AMT', 'name': 'AMERICAN TOWER CORP', 'value_usd': 35000, 'weight': 10.6, 'shares': 1},
            {'ticker': 'APO', 'name': 'APOLLO GLOBAL MGMT', 'value_usd': 35000, 'weight': 10.6, 'shares': 1},
            {'ticker': 'MU', 'name': 'MICRON TECHNOLOGY', 'value_usd': 35000, 'weight': 10.6, 'shares': 1},
            {'ticker': 'GOOGL', 'name': 'ALPHABET INC', 'value_usd': 30000, 'weight': 9.1, 'shares': 1},
        ]
    },
    {
        'id': 'tom-suozzi',
        'name': 'Thomas Suozzi',
        'name_zh': '托马斯·索齐',
        'fund': 'US House (NY-03)',
        'source': 'STOCK Act',
        'cik': '',
        'style': 'congress',
        'color': '#0D6EFD',
        'initials': 'TS',
        'tagline': 'A级#11，613笔交易(高样本量)，45%胜率，alpha +3.7%。NVDA重仓$8.2M。',
        'filing_date': '2026-07-25',
        'period_of_report': '2026-07-15',
        'total_value_usd': 12000000.0,
        'holdings_count': 8,
        'holdings': [
            {'ticker': 'NVDA', 'name': 'NVIDIA CORP', 'value_usd': 8200000, 'weight': 68.3, 'shares': 1},
            {'ticker': 'AAPL', 'name': 'APPLE INC', 'value_usd': 1200000, 'weight': 10.0, 'shares': 1},
            {'ticker': 'MSFT', 'name': 'MICROSOFT CORP', 'value_usd': 800000, 'weight': 6.7, 'shares': 1},
            {'ticker': 'GOOGL', 'name': 'ALPHABET INC', 'value_usd': 600000, 'weight': 5.0, 'shares': 1},
            {'ticker': 'AMZN', 'name': 'AMAZON.COM INC', 'value_usd': 400000, 'weight': 3.3, 'shares': 1},
            {'ticker': 'META', 'name': 'META PLATFORMS', 'value_usd': 300000, 'weight': 2.5, 'shares': 1},
            {'ticker': 'JPM', 'name': 'JPMORGAN CHASE', 'value_usd': 300000, 'weight': 2.5, 'shares': 1},
            {'ticker': 'V', 'name': 'VISA INC', 'value_usd': 200000, 'weight': 1.7, 'shares': 1},
        ]
    },
]

# Load existing investors
with open('data/investors.json', 'r', encoding='utf-8') as f:
    investors = json.load(f)

existing_ids = {inv['id'] for inv in investors['investors']}
added = 0

for p in NEW:
    if p['id'] not in existing_ids:
        investors['investors'].append(p)
        added += 1
        print(f'Added: {p["name"]} ({p["name_zh"]}) - {len(p["holdings"])} holdings')

investors['last_updated'] = datetime.now(timezone.utc).isoformat()

with open('data/investors.json', 'w', encoding='utf-8') as f:
    json.dump(investors, f, ensure_ascii=False, indent=2)

print(f'Total investors: {len(investors["investors"])} (added {added})')
