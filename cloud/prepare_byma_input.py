from pathlib import Path
import os
import pandas as pd

ROOT=Path(r'C:\Users\santi\OneDrive\Escritorio\ALPHA_ENGINE_V12_RETURN_FIRST\ALPHA_ENGINE_V13_RETURN_FIRST_MULTI_HORIZON')
src=ROOT/'outputs'/'live_shadow'/'v13_live_shadow_contract_latest.csv'
out=ROOT/'outputs'/'portfolio_sizing_shadow'/'v13_total_nav_shadow_sizing_latest.csv'
if not src.exists(): raise SystemExit(f'Missing live V13 contract: {src}')
x=pd.read_csv(src)
if x.empty: raise SystemExit('Live V13 contract is empty')
x['signal_date']=pd.to_datetime(x['signal_date'],errors='coerce')
asof=x['signal_date'].max()
x=x[x['signal_date'].eq(asof)].copy()
for c in ['model_target_weight','expected_active_total','effective_horizon_sessions','resize_band']:
    if c in x.columns: x[c]=pd.to_numeric(x[c],errors='coerce')
capital=float(os.getenv('ALPHA_BYMA_REFERENCE_CAPITAL_USD','1000'))
if not (capital>0): raise SystemExit('ALPHA_BYMA_REFERENCE_CAPITAL_USD must be positive')
w=x['model_target_weight'].fillna(0).clip(lower=0)
if w.sum()>1.0000001: raise SystemExit(f'Live target sum >1: {w.sum()}')
action=['BUY' if v>0 else 'HOLD' for v in w]
y=pd.DataFrame({
    'asof': asof.date().isoformat(),
    'seal_id': x.get('seal_id',''),
    'ticker': x['ticker'].astype(str).str.upper(),
    'action_total_nav_basis': action,
    'currently_held': False,
    'quantity_current': 0.0,
    'current_market_value_usd': 0.0,
    'current_weight_total_nav': 0.0,
    'phase3z_target_weight_total_nav': w,
    'target_value_usd': w*capital,
    'trade_value_usd_shadow': w*capital,
    'trade_side_shadow': ['BUY' if v>0 else 'NONE' for v in w],
    'resize_band': x.get('resize_band',1.0),
    'entry_ok': x.get('entry_ok',False),
    'expected_active_total': x.get('expected_active_total',0.0),
    'effective_horizon_sessions': x.get('effective_horizon_sessions',0.0),
    'reason': 'CLOUD_BYMA_REFERENCE_FROM_LIVE_V13',
})
out.parent.mkdir(parents=True,exist_ok=True)
y.to_csv(out,index=False)
print('BYMA_REFERENCE_INPUT: PASS')
print('asof:',asof.date(),'capital_usd:',capital,'rows:',len(y),'target_sum:',float(w.sum()))
