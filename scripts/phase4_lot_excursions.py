"""Post-trade quote excursions for completed FIFO lots; never a trading input."""
from collections import defaultdict
import numpy as np
import pandas as pd

from phase3_reporting import FEE_RATE, FillLedger


def quote_window(times, prices, start, end, entry_quote, exit_quote, buy_price):
    if end < start or not np.isfinite(buy_price) or buy_price <= 0:
        raise ValueError('Invalid completed-lot interval or buy price')
    # Several ticks can share a timestamp. Only the recorded fill quotes are
    # unambiguous at the endpoints; all strictly interior ticks are observable.
    left, right = np.searchsorted(times, start, side='right'), np.searchsorted(times, end, side='left')
    interior = prices[left:right]
    observed = np.concatenate(([entry_quote, exit_quote], interior))
    if not np.all(np.isfinite(observed)) or np.any(observed <= 0):
        raise ValueError('Invalid observed quote')
    low, high = float(observed.min()), float(observed.max())
    return {'minimum_quote': low, 'maximum_quote': high,
            'mae_quote_pct': min(0.0, (low / buy_price - 1) * 100),
            'mfe_quote_pct': max(0.0, (high / buy_price - 1) * 100),
            'strictly_interior_ticks': len(interior)}


def load_quotes(package, days):
    times, prices = defaultdict(list), defaultdict(list)
    for day in days:
        frame = pd.read_csv(package / f'marketInfo/ticks/{day}.csv',
                            usecols=['ShareCode', 'TradeDateTime', 'LastPrice'])
        frame['TradeDateTime'] = pd.to_datetime(frame['TradeDateTime'])
        for symbol, group in frame.groupby('ShareCode', sort=True):
            times[symbol].append(group['TradeDateTime'].to_numpy())
            prices[symbol].append(group['LastPrice'].to_numpy(dtype=float))
    quotes = {}
    for symbol in times:
        t, p = np.concatenate(times[symbol]), np.concatenate(prices[symbol])
        if np.any(t[1:] < t[:-1]) or not np.all(np.isfinite(p)) or np.any(p <= 0):
            raise ValueError(f'Invalid or unordered quote history: {symbol}')
        quotes[symbol] = (t, p)
    return quotes


def completed_excursions(fills, quotes, capital=10000000):
    ledger, entries, result = FillLedger(capital), {}, []
    for fill in fills:
        key = (fill['Symbol'], str(fill['Order Number']))
        timestamp = (pd.Timestamp(fill['Timestamp']) + pd.Timedelta(hours=7)).to_datetime64()
        if fill['Side'] == 'Buy':
            entries.setdefault(key, (timestamp, float(fill['Market Price'])))
        before = len(ledger.completed)
        ledger.apply(fill)
        for lot in ledger.completed[before:]:
            symbol, order = lot['symbol'], lot['order']
            start, entry_quote = entries[(symbol, order)]
            gross_buy_price = lot['unit_cost'] / (1 + FEE_RATE)
            measures = quote_window(*quotes[symbol], start, timestamp, entry_quote,
                                    float(fill['Market Price']), gross_buy_price)
            result.append({'symbol': symbol, 'order': order, 'first_buy_bangkok': str(start),
                           'completion_bangkok': str(timestamp), 'gross_average_buy_price': gross_buy_price,
                           **measures})
    return {'completed_lots': result,
            'method': 'Quote MAE/MFE relative to average buy fill price, first buy through final FIFO completion',
            'boundaries': 'Recorded entry/exit quotes plus strictly interior timestamps; other same-time endpoint ticks excluded',
            'limitations': ['Diagnostic uses future price paths after entry; never supplied to the strategy',
                            'Quotes include auctions and are not executable liquidation opportunities',
                            'No weighting for the declining quantity of partially sold lots',
                            'Gross quote excursions exclude commissions and exit slippage; not portfolio intraday drawdown']}
