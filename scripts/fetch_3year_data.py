"""Fetch 3 years of S&P500 data and generate synthetic NASDAQ 100 / VIX data."""
import json, math, random, os, ssl
from datetime import datetime, timedelta
from urllib import request

ssl._create_default_https_context = ssl._create_unverified_context

OUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'charts')
os.makedirs(OUT, exist_ok=True)

END_DATE = '20260809'
START_DATE = '20230809'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Referer': 'https://quote.eastmoney.com/',
    'Accept': 'application/json',
}

def fetch_url(url):
    req = request.Request(url, headers=HEADERS)
    return request.urlopen(req, timeout=20)

# ── Step 1: Fetch S&P500 ──
sp500_data = None
secids_to_try = [
    # S&P500 various secid formats
    '100.SPX',       # US market S&P500
    '100.NDX',       # maybe NASDAQ
    '105.SPX',       # alternative
    '107.SPX',       # another
    '106.SPX',       # another
]

for secid in secids_to_try:
    url = (
        f'https://push2his.eastmoney.com/api/qt/stock/kline/get?'
        f'secid={secid}&fields1=f1,f2,f3,f4,f5,f6&'
        f'fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&'
        f'klt=101&fqt=1&beg={START_DATE}&end={END_DATE}'
    )
    print(f'Trying secid: {secid}')
    try:
        resp = fetch_url(url)
        data = json.loads(resp.read())
        print(f'  Response: rc={data.get("rc")}, has_data={bool(data.get("data") and data["data"].get("klines"))}')
        if data.get('data') and data['data'].get('klines'):
            sp500_data = data['data']['klines']
            print(f'  SUCCESS: got {len(sp500_data)} rows')
            break
        else:
            print(f'  No klines data')
    except Exception as e:
        print(f'  Error: {e}')

# ── Try Yahoo Finance as backup ──
if sp500_data is None:
    print('\nTrying Yahoo Finance...')
    try:
        # Use Yahoo Finance v8 chart API
        yahoo_url = (
            f'https://query1.finance.yahoo.com/v8/finance/chart/^GSPC?'
            f'period1={int(datetime(2023,8,9).timestamp())}&'
            f'period2={int(datetime(2026,8,9).timestamp())}&'
            f'interval=1d'
        )
        resp = fetch_url(yahoo_url)
        ydata = json.loads(resp.read())
        result = ydata['chart']['result'][0]
        timestamps = result['timestamp']
        quote = result['indicators']['quote'][0]
        opens = quote['open']
        closes = quote['close']
        highs = quote['high']
        lows = quote['low']
        volumes = quote['volume']
        
        sp500_data = []
        for i, ts in enumerate(timestamps):
            dt = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
            opn = opens[i] if i < len(opens) and opens[i] is not None else 0
            close = closes[i] if i < len(closes) and closes[i] is not None else 0
            high = highs[i] if i < len(highs) and highs[i] is not None else 0
            low = lows[i] if i < len(lows) and lows[i] is not None else 0
            vol = int(volumes[i]) if i < len(volumes) and volumes[i] is not None else 0
            if close > 0:
                sp500_data.append(f'{dt},{opn},{close},{high},{low},{vol}')
        
        print(f'  Yahoo Finance: got {len(sp500_data)} rows')
    except Exception as e:
        print(f'  Yahoo Finance error: {e}')

# ── If still no data, generate fully synthetic ──
if sp500_data is None:
    print('\nAll APIs failed. Generating fully synthetic data...')
    sp500_data = generate_synthetic_sp500()

# Parse S&P500
sp500_rows = []
for line in sp500_data:
    if isinstance(line, str):
        parts = line.split(',')
    else:
        parts = line
    date = parts[0]
    opn = float(parts[1])
    close = float(parts[2])
    high = float(parts[3])
    low = float(parts[4])
    vol = int(parts[5]) if len(parts) > 5 else 0
    sp500_rows.append([date, opn, close, high, low, vol])

sp500_rows.sort(key=lambda r: r[0])
print(f'\nS&P500 rows: {len(sp500_rows)}')
print(f'Date range: {sp500_rows[0][0]} to {sp500_rows[-1][0]}')
print(f'Close range: {sp500_rows[0][2]:.0f} to {sp500_rows[-1][2]:.0f}')

# ── Filter to exactly 3 years ──
# Keep only rows within START_DATE to END_DATE
sp500_rows = [r for r in sp500_rows if START_DATE <= r[0].replace('-','') <= END_DATE]
print(f'Filtered to: {len(sp500_rows)} rows')

# ── Step 2: Generate synthetic NASDAQ 100 ──
print(f'\nGenerating synthetic NASDAQ 100...')
random.seed(42)

# Starting values for Aug 2023
sp_start = sp500_rows[0][2]
nas_start = 15000.0 if sp_start > 4000 else 15000.0 * (sp_start / 4450)

nasdaq_rows = []
nas_close_prev = nas_start
for i, sp_row in enumerate(sp500_rows):
    if i == 0:
        nas_close = nas_start
    else:
        sp_ret = (sp_row[2] / sp500_rows[i-1][2]) - 1
        beta = 1.3
        noise = random.gauss(0, 0.005)
        nas_ret = beta * sp_ret + noise
        nas_close = nas_close_prev * (1 + nas_ret)
    nas_close_prev = nas_close
    
    vol_ratio = abs((nas_close / nas_start - 1))
    daily_vol = 0.003 + vol_ratio * 0.002
    high = nas_close * (1 + abs(random.gauss(0, daily_vol)))
    low = nas_close * (1 - abs(random.gauss(0, daily_vol)))
    opn = low + random.random() * (high - low)
    vol = int(sp_row[5] * random.uniform(0.35, 0.65))
    nasdaq_rows.append([sp_row[0], round(opn, 2), round(nas_close, 2), round(high, 2), round(low, 2), vol])

print(f'  NASDAQ: {nasdaq_rows[0][2]:.0f} -> {nasdaq_rows[-1][2]:.0f}')

# ── Step 3: Generate synthetic VIX ──
print(f'\nGenerating synthetic VIX...')
random.seed(123)
vix_rows = []
vix_val = 16.0

for i, sp_row in enumerate(sp500_rows):
    if i > 0:
        sp_ret = (sp_row[2] / sp500_rows[i-1][2]) - 1
    else:
        sp_ret = 0
    
    # VIX mean-reverts around 19
    vix_target = 19.0 + (abs(sp_ret) * 280)
    if abs(sp_ret) > 0.02:
        vix_target += random.uniform(3, 8)
    
    vix_val = vix_val + 0.06 * (vix_target - vix_val) + random.gauss(0, 0.4)
    vix_val = max(10, min(50, vix_val))
    
    if random.random() < 0.02:
        vix_val += random.uniform(3, 8)
    
    close = round(vix_val, 2)
    daily_range = close * (0.01 + random.random() * 0.04)
    high = round(close + daily_range * random.random(), 2)
    low = round(close - daily_range * random.random(), 2)
    opn = round(low + random.random() * (high - low), 2)
    vix_rows.append([sp_row[0], opn, close, max(high,opn), min(low,opn), 0])

print(f'  VIX: {vix_rows[0][2]:.1f} -> {vix_rows[-1][2]:.1f}')

# ── Step 4: Write CSV ──
header = 'Date,Open,Close,High,Low,Volume\n'
for fname, rows in [('sp500.csv', sp500_rows), ('nasdaq100.csv', nasdaq_rows), ('vix.csv', vix_rows)]:
    path = os.path.join(OUT, fname)
    with open(path, 'w') as f:
        f.write(header)
        for r in rows:
            f.write(f'{r[0]},{r[1]},{r[2]},{r[3]},{r[4]},{r[5]}\n')
    print(f'Wrote {path}: {len(rows)} rows')

print('\nDone!')
