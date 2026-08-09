#!/usr/bin/env python3
"""
Update performance rankings with Congress Tier List data and add new politicians.
Data source: https://congresstierlist.com/guides/best-stock-traders-in-congress/ (Aug 8, 2026)
Annualized return = S&P 500 baseline (~10%) + CTL alpha
"""

import json
from datetime import datetime, timezone

# ── Congress Tier List data (Aug 8, 2026) ──
# alpha = dollar-weighted avg outperformance vs S&P 500
# annualized_return = alpha + 10% (S&P baseline)
CTL_DATA = {
    'david-taylor':       {'ct_alpha': 8.39,  'win_rate': 77, 'trades': 89,   'tier': 'S'},
    'sheldon-whitehouse': {'ct_alpha': 638.42,'win_rate': 43, 'trades': 350,  'tier': 'A', 'note': '⚠️极端异常值，单一交易可能严重扭曲alpha'},
    'pete-sessions':      {'ct_alpha': 55.54, 'win_rate': 41, 'trades': 378,  'tier': 'A', 'note': '⚠️alpha异常高但胜率仅41%'},
    'dwight-evans':       {'ct_alpha': 33.43, 'win_rate': 44, 'trades': 177,  'tier': 'A'},
    'susie-lee':          {'ct_alpha': 27.50, 'win_rate': 45, 'trades': 1273, 'tier': 'A'},
    'gil-cisneros':       {'ct_alpha': 21.13, 'win_rate': 43, 'trades': 2503, 'tier': 'A'},
    'john-fetterman':     {'ct_alpha': 13.23, 'win_rate': 50, 'trades': 8,    'tier': 'A'},
    'lisa-mcclain':       {'ct_alpha': 13.12, 'win_rate': 28, 'trades': 1394, 'tier': 'A'},
    'kelly-morrison':     {'ct_alpha': 9.91,  'win_rate': 38, 'trades': 36,   'tier': 'A'},
    'cleo-fields':        {'ct_alpha': 8.93,  'win_rate': 57, 'trades': 193,  'tier': 'A'},
    'tim-moore':          {'ct_alpha': 8.58,  'win_rate': 54, 'trades': 199,  'tier': 'A'},
    'tom-suozzi':         {'ct_alpha': 3.73,  'win_rate': 45, 'trades': 613,  'tier': 'A'},
}

# ── Non-congress performance (public records) ──
NON_CONGRESS = {
    'druckenmiller': {'annualized_return': 28.6, 'win_rate': 78, 'track_record_years': 30,
                      'strength': '30年无亏损年份，宏观判断力顶级', 'weakness': '家族办公室不透明，13F仅显示多头',
                      'source': '1981-2010 Duquesne Capital，无一年亏损'},
    'tepper':        {'annualized_return': 25.4, 'win_rate': 72, 'track_record_years': 25,
                      'strength': '困境反转精准抄底，金融危机暴利', 'weakness': '风格高度集中，波动性大',
                      'source': '1993-2025 Appaloosa，困境资产专家'},
    'pelosi':        {'annualized_return': 25.0, 'win_rate': 60, 'track_record_years': 5,
                      'strength': '信息优势+期权放大器，NVDA/GOOGL精准交易', 'weakness': '样本小(5年)，$CRM重仓2025年拖累',
                      'source': 'STOCK Act披露，NVDA期权暴利（CTL未入A级）'},
    'li-lu':         {'annualized_return': 20.3, 'win_rate': 70, 'track_record_years': 25,
                      'strength': '深度价值研究，亚洲+美国跨境能力', 'weakness': '持仓高度集中，13F信息有限',
                      'source': '喜马拉雅资本公开记录，亚洲巴菲特'},
    'buffett':       {'annualized_return': 19.9, 'win_rate': 67, 'track_record_years': 60,
                      'strength': '超长期复利之王，60年年化19.9%无人能及', 'weakness': '近10年超额收益收窄，规模过大',
                      'source': '1965-2025 伯克希尔年报，40/60年跑赢标普500'},
    'klarman':       {'annualized_return': 16.5, 'win_rate': 65, 'track_record_years': 30,
                      'strength': '极端风控，持有大量现金等待机会', 'weakness': '保守风格在牛市跑输，现金拖累',
                      'source': 'Baupost 1982至今，《安全边际》作者'},
    'li-ka-shing':   {'annualized_return': 16.2, 'win_rate': 65, 'track_record_years': 40,
                      'strength': '低买高卖周期大师，全球基础设施布局', 'weakness': '港股持仓透明度低，依赖年报推测',
                      'source': '长和系公开财报，全球多元化布局'},
    'ackman':        {'annualized_return': 15.2, 'win_rate': 58, 'track_record_years': 20,
                      'strength': '集中投资+主动参与治理，大机会下重注', 'weakness': '波动极大，2022年亏损严重',
                      'source': 'Pershing Square 2004至今，激进投资者'},
    'pabrai':        {'annualized_return': 13.8, 'win_rate': 55, 'track_record_years': 20,
                      'strength': '纯粹价值投资，极度集中的持仓', 'weakness': '规模小，流动性差的标的波动大',
                      'source': '克隆巴菲特策略，2000-2025'},
    'dalio':         {'annualized_return': 11.5, 'win_rate': 60, 'track_record_years': 30,
                      'strength': '全天候策略抗周期，风险平价先驱', 'weakness': 'Pure Alpha近年表现平庸，规模过大',
                      'source': 'Pure Alpha策略，全天候组合'},
    'claude':        {'annualized_return': 10.0, 'win_rate': 55, 'track_record_years': 1,
                      'strength': '零情绪干扰，AI量化+基本面融合决策', 'weakness': '历史不足1年，未经完整牛熊周期',
                      'source': '2026.04启动，AI完全自主决策，Autopilot平台'},
    'wood':          {'annualized_return': 9.8,  'win_rate': 38, 'track_record_years': 10,
                      'strength': '特斯拉/比特币早期重仓，2020年封神', 'weakness': '2021-2022回撤80%+，波动率极高',
                      'source': 'ARK旗舰基金2014至今，颠覆式创新主题'},
}

# ── Build all entries ──
all_entries = []

# Non-congress
for pid, d in NON_CONGRESS.items():
    all_entries.append({
        'id': pid, 'name': '', 'name_zh': '', 'fund': '', 'category': '',
        'annualized_return': d['annualized_return'], 'win_rate': d['win_rate'],
        'track_record_years': d['track_record_years'],
        'key_strength': d['strength'], 'key_weakness': d['weakness'],
        'source_note': d['source'],
    })

# Congress (from CTL)
for pid, d in CTL_DATA.items():
    annualized = round(d['ct_alpha'] + 10.0, 2)
    note = d.get('note', '')
    all_entries.append({
        'id': pid, 'name': '', 'name_zh': '', 'fund': '', 'category': 'congress',
        'annualized_return': annualized, 'win_rate': d['win_rate'],
        'track_record_years': max(2, 2026 - 2023 + 1),
        'key_strength': f"CTL {d['tier']}级，{d['trades']}笔交易回溯" + (f"，{note}" if note else ""),
        'key_weakness': f"胜率{d['win_rate']}%" if d['win_rate'] < 50 else f"{d['trades']}笔交易验证",
        'source_note': f"Congress Tier List ({d['tier']}-Tier)，{d['trades']}笔交易，alpha +{d['ct_alpha']}%",
    })

# ── Fill names from investors.json ──
with open('data/investors.json', 'r', encoding='utf-8') as f:
    investors_data = json.load(f)

name_map = {}
for inv in investors_data['investors']:
    name_map[inv['id']] = (inv['name'], inv.get('name_zh', inv['name']), inv['fund'], inv['style'])

# Add names for new politicians not in investors.json yet
new_names = {
    'sheldon-whitehouse': ('Sheldon Whitehouse', '谢尔登·怀特豪斯', 'US Senate (RI)', 'congress'),
    'pete-sessions':      ('Pete Sessions', '皮特·塞申斯', 'US House (TX-17)', 'congress'),
    'dwight-evans':       ('Dwight Evans', '德怀特·埃文斯', 'US House (PA-03)', 'congress'),
    'tom-suozzi':         ('Thomas Suozzi', '托马斯·索齐', 'US House (NY-03)', 'congress'),
    'lisa-mcclain':       ('Lisa McClain', '丽莎·麦克莱恩', 'US House (MI-09)', 'congress'),
    'kelly-morrison':     ('Kelly Morrison', '凯莉·莫里森', 'US House (MN-03)', 'congress'),
}
name_map.update(new_names)

for entry in all_entries:
    pid = entry['id']
    if pid in name_map:
        entry['name'] = name_map[pid][0]
        entry['name_zh'] = name_map[pid][1]
        entry['fund'] = name_map[pid][2]
        entry['category'] = name_map[pid][3]

# ── Sort and rank ──
by_return = sorted(all_entries, key=lambda x: x['annualized_return'], reverse=True)
by_win = sorted(all_entries, key=lambda x: x['win_rate'], reverse=True)
by_composite = sorted(all_entries, key=lambda x: x['annualized_return'] * 0.5 + x['win_rate'] * 0.5, reverse=True)

def add_ranks(lst):
    for i, entry in enumerate(lst):
        entry['rank'] = i + 1
        entry['composite_score'] = round(entry['annualized_return'] * 0.5 + entry['win_rate'] * 0.5, 1)
    return lst

# ── Capitol Trades selections ──
# Top 5 congress by annualized return
congress_by_return = [e for e in by_return if e['category'] == 'congress']
top5_return = [e['id'] for e in congress_by_return[:5]]

# Top 5 congress by win rate
congress_by_win = [e for e in by_win if e['category'] == 'congress']
top5_win = [e['id'] for e in congress_by_win[:5]]

# Currently tracked congress IDs
tracked_congress = {'pelosi', 'david-taylor', 'cleo-fields', 'tim-moore',
                     'john-fetterman', 'susie-lee', 'gil-cisneros'}

# New additions = union of top5_return and top5_win, minus tracked
selected = list(dict.fromkeys(top5_return + top5_win))  # deduped, order preserved
new_to_add = [s for s in selected if s not in tracked_congress]

# ── Build performance.json ──
performance = {
    'last_updated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    'note': '年化回报率=CTL alpha+S&P500基线(10%)；胜率=交易跑赢标普500占比。数据来源：Congress Tier List (15,630笔交易回溯, 更新时间 2026-08-08)',
    'source_urls': [
        'https://congresstierlist.com/guides/best-stock-traders-in-congress/',
        'https://www.capitoltrades.com/politicians',
        'https://kapitol.ai/best-performing-congress-stock-traders',
    ],
    'rankings': {
        'by_annualized_return': add_ranks(by_return[:25]),
        'by_win_rate': add_ranks(by_win[:25]),
        'by_composite': add_ranks(by_composite[:25]),
    },
    'capitol_trades_selections': {
        'top5_by_return': top5_return,
        'top5_by_win_rate': top5_win,
        'selected_for_tracking': new_to_add,
        'methodology': '年化率=avg_alpha + S&P500基线(~10%)；胜率=交易跑赢S&P500的百分比；来源：Congress Tier List (15,630笔交易回溯, 2026-08-08更新)',
        'data_warning': '⚠️ Sheldon Whitehouse的alpha +638%为极端异常值，可能由单一交易驱动。Pete Sessions alpha +55%也异常高但胜率仅41%。建议关注高胜率+合理alpha的组合。',
    }
}

with open('data/performance.json', 'w', encoding='utf-8') as f:
    json.dump(performance, f, ensure_ascii=False, indent=2)

print('=== Performance Rankings ===')
print()

print('--- 年化回报率排名 (Top 10) ---')
for e in by_return[:10]:
    flag = ' [已追踪]' if e['id'] in tracked_congress or e.get('category') != 'congress' else ' [NEW]'
    print(f"  #{e.get('rank','?')}. {e.get('name_zh','')} ({e['name']}) - {e['annualized_return']}%, {e['win_rate']}%胜率, {e['track_record_years']}年{flag}")

print()
print('--- 胜率排名 (Top 10) ---')
for e in by_win[:10]:
    flag = ' [已追踪]' if e['id'] in tracked_congress or e.get('category') != 'congress' else ' [NEW]'
    print(f"  #{e.get('rank','?')}. {e.get('name_zh','')} ({e['name']}) - {e['win_rate']}%胜率, {e['annualized_return']}%年化, {e['track_record_years']}年{flag}")

print()
print('=== Capitol Trades 选取结果 ===')
print(f'年化率前5: {top5_return}')
print(f'胜率前5:   {top5_win}')
print(f'已追踪国会: {sorted(tracked_congress)}')
print(f'新增追踪:   {new_to_add}')
print()
print(f'总条目: {len(all_entries)}')
print(f'performance.json 已更新')
