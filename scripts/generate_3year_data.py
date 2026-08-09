"""Generate 3 years of realistic synthetic market data for S&P500, NASDAQ 100, and VIX."""
import os, math, random

OUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'charts')
os.makedirs(OUT, exist_ok=True)

# Realistic known values for anchoring
# S&P500: Aug 2023 ~4467, Feb 2025 ~5955 (from our old CSV), Aug 2026 ~6100
# NASDAQ 100: Aug 2023 ~15000, Aug 2026 ~20500
# VIX: Aug 2023 ~16, typically 13-28 range with occasional spikes

random.seed(42)
np_random = random  # use random module

# Generate trading days (Mon-Fri, excluding common holidays roughly)
from datetime import datetime, timedelta

def generate_trading_days(start, end):
    """Generate trading days between start and end dates."""
    start_dt = datetime.strptime(start, '%Y%m%d')
    end_dt = datetime.strptime(end, '%Y%m%d')
    
    # US market holidays (rough, major ones)
    holidays = set()
    for year in [2023, 2024, 2025, 2026]:
        # New Year
        holidays.add(datetime(year, 1, 1))
        # MLK Day (3rd Monday of Jan)
        d = datetime(year, 1, 1)
        while d.weekday() != 0: d += timedelta(days=1)
        holidays.add(d + timedelta(days=14))
        # Presidents Day (3rd Monday of Feb)
        d = datetime(year, 2, 1)
        while d.weekday() != 0: d += timedelta(days=1)
        holidays.add(d + timedelta(days=14))
        # Memorial Day (last Monday of May)
        d = datetime(year, 5, 31)
        while d.weekday() != 0: d -= timedelta(days=1)
        holidays.add(d)
        # Independence Day
        holidays.add(datetime(year, 7, 4))
        # Labor Day (1st Monday of Sep)
        d = datetime(year, 9, 1)
        while d.weekday() != 0: d += timedelta(days=1)
        holidays.add(d)
        # Thanksgiving (4th Thursday of Nov)
        d = datetime(year, 11, 1)
        while d.weekday() != 3: d += timedelta(days=1)
        holidays.add(d + timedelta(days=21))
        # Christmas
        holidays.add(datetime(year, 12, 25))
    
    days = []
    curr = start_dt
    while curr <= end_dt:
        if curr.weekday() < 5 and curr not in holidays:
            # Also skip holiday-adjacent (Good Friday, etc.)
            is_holiday = False
            for h in holidays:
                if abs((curr - h).days) <= 0 and curr == h:
                    is_holiday = True
                    break
            if not is_holiday:
                days.append(curr.strftime('%Y-%m-%d'))
        curr += timedelta(days=1)
    return days

trading_days = generate_trading_days('20230809', '20260809')
n = len(trading_days)
print(f'Trading days: {n}')

# ── Generate realistic S&P500 3-year path ──
# Use a model with drift + GARCH-like volatility + occasional jumps
random.seed(42)

# Known anchors
sp_start = 4467.0  # Aug 9, 2023
sp_feb2025 = 5955.0  # Feb 25, 2025 (from old CSV)
sp_end_est = 6050.0  # Aug 2026 estimate

# We'll generate with drift that hits the anchors
# Split into periods:
# Period 1: Aug 2023 - Feb 2025 (bull run): ~33% total return = ~21% annualized
# Period 2: Feb 2025 - Aug 2026 (choppy/sideways): ~1.6% total = ~1% annualized

sp_closes = [sp_start]
annual_vol = 0.16  # 16% annual vol
daily_vol = annual_vol / math.sqrt(252)

for i in range(1, n):
    date = trading_days[i]
    
    # Drift varies by period
    if date <= '2025-02-25':
        # Bull phase: ~21% annual
        daily_drift = 0.00075  
    elif date <= '2025-06-01':
        # Correction phase
        daily_drift = -0.0003
    elif date <= '2025-10-01':
        # Recovery
        daily_drift = 0.0005
    elif date <= '2026-02-01':
        # Choppy
        daily_drift = 0.00015
    else:
        # Mild recovery
        daily_drift = 0.00035
    
    # Regime-switching volatility
    if date <= '2025-03-15':
        daily_vol = 0.009  # lower vol in bull
    elif date <= '2025-05-01':
        daily_vol = 0.016  # higher vol in correction
    else:
        daily_vol = 0.011
    
    # Generate return with fat tails (t-distribution approximation)
    u = random.random()
    if u < 0.01:
        shock = random.gauss(-0.02, 0.01)  # crash
    elif u > 0.99:
        shock = random.gauss(0.02, 0.008)  # rally
    else:
        shock = random.gauss(0, daily_vol)
    
    ret = daily_drift + shock
    sp_closes.append(sp_closes[-1] * (1 + ret))

# Scale to hit anchor at Feb 2025
feb2025_idx = None
for i, d in enumerate(trading_days):
    if d == '2025-02-25':
        feb2025_idx = i
        break

if feb2025_idx:
    scale = sp_feb2025 / sp_closes[feb2025_idx]
    sp_closes = [c * scale for c in sp_closes]

# Build S&P500 rows
sp500_rows = []
for i, date in enumerate(trading_days):
    close = round(sp_closes[i], 2)
    daily_range = close * 0.008 * (0.7 + 0.6 * random.random())
    high = round(close + daily_range * random.random(), 2)
    low = round(close - daily_range * random.random(), 2)
    opn = round(low + random.random() * (high - low), 2)
    vol = int(random.uniform(2.5e9, 5.5e9))
    sp500_rows.append([date, opn, close, max(high, opn), min(low, opn), vol])

print(f'S&P500: {sp500_rows[0][2]:.0f} -> {sp500_rows[-1][2]:.0f}')

# ── Generate NASDAQ 100 ──
random.seed(123)
nas_start = 15100.0
nas_closes = [nas_start]

for i in range(1, n):
    sp_ret = (sp_closes[i] / sp_closes[i-1]) - 1
    # NASDAQ amplifies S&P500 moves by ~1.3x with ~0.85 correlation + extra noise
    beta = 1.28
    noise_vol = 0.005
    noise = random.gauss(0, noise_vol)
    nas_ret = beta * sp_ret + noise
    nas_closes.append(nas_closes[-1] * (1 + nas_ret))

nasdaq_rows = []
for i, date in enumerate(trading_days):
    close = round(nas_closes[i], 2)
    daily_range = close * 0.01 * (0.7 + 0.6 * random.random())
    high = round(close + daily_range * random.random(), 2)
    low = round(close - daily_range * random.random(), 2)
    opn = round(low + random.random() * (high - low), 2)
    vol = int(random.uniform(1.8e9, 4.5e9))
    nasdaq_rows.append([date, opn, close, max(high, opn), min(low, opn), vol])

print(f'NASDAQ 100: {nasdaq_rows[0][2]:.0f} -> {nasdaq_rows[-1][2]:.0f}')

# ── Generate VIX ──
random.seed(456)
vix_rows = []
vix_val = 16.5

for i, date in enumerate(trading_days):
    if i > 0:
        sp_ret = (sp_closes[i] / sp_closes[i-1]) - 1
    else:
        sp_ret = 0
    
    # VIX target based on recent volatility and market moves
    # VIX rises when market falls fast
    recent_returns = []
    for j in range(max(0, i-20), i+1):
        if j > 0:
            recent_returns.append((sp_closes[j] / sp_closes[j-1]) - 1)
    
    recent_vol = 0
    if recent_returns:
        mean_ret = sum(recent_returns) / len(recent_returns)
        recent_vol = math.sqrt(sum((r - mean_ret)**2 for r in recent_returns) / len(recent_returns))
    
    # VIX baseline ~17, rises with vol and negative returns
    vix_target = 17.0 + recent_vol * 400 + max(0, -sp_ret) * 300
    
    # Mean reversion speed
    mr_speed = 0.05
    vix_val = vix_val + mr_speed * (vix_target - vix_val) + random.gauss(0, 0.35)
    vix_val = max(10.0, min(45.0, vix_val))
    
    # Occasional spikes (volatility clustering)
    if random.random() < 0.015:
        vix_val += random.uniform(3, 10)
    
    close = round(vix_val, 2)
    daily_range = close * 0.04 * random.random()
    high = round(close + daily_range * random.random(), 2)
    low = round(close - daily_range * random.random(), 2)
    opn = round(low + random.random() * (high - low), 2)
    vix_rows.append([date, opn, close, max(high, opn), min(low, opn), 0])

print(f'VIX: mean={sum(r[2] for r in vix_rows)/len(vix_rows):.1f}, range={min(r[2] for r in vix_rows):.1f}-{max(r[2] for r in vix_rows):.1f}')

# ── Write CSV ──
header = 'Date,Open,Close,High,Low,Volume\n'
for fname, rows in [('sp500.csv', sp500_rows), ('nasdaq100.csv', nasdaq_rows), ('vix.csv', vix_rows)]:
    path = os.path.join(OUT, fname)
    with open(path, 'w') as f:
        f.write(header)
        for r in rows:
            f.write(f'{r[0]},{r[1]},{r[2]},{r[3]},{r[4]},{r[5]}\n')
    print(f'Wrote {path}: {len(rows)} rows')

print('\nDone! 3 years of data generated.')
