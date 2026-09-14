from pathlib import Path
import json, math
import pandas as pd

ROOT=Path(r'C:\Users\santi\OneDrive\Escritorio\ALPHA_ENGINE_V12_RETURN_FIRST\ALPHA_ENGINE_V13_RETURN_FIRST_MULTI_HORIZON')
REPO=Path(__file__).resolve().parents[1]
OUT=REPO/'public'/'data'/'latest.json'
EXPECTED_SEAL='46bbbf853561e26625ee3ecbccb6037051556f2f3ca26dcb4e311c165c08d8e9'

def j(path, required=True):
    p=ROOT/path
    if not p.exists():
        if required: raise SystemExit(f'Missing {p}')
        return None
    return json.loads(p.read_text(encoding='utf-8'))

def records(path):
    p=ROOT/path
    if not p.exists(): return []
    x=pd.read_csv(p)
    x=x.replace({float('nan'):None})
    return json.loads(x.to_json(orient='records',date_format='iso'))

live=j(Path('outputs/live_shadow/v13_live_shadow_summary.json'))
if live.get('status')!='PASS': raise SystemExit(f"V13 live status={live.get('status')}")
if live.get('seal_id')!=EXPECTED_SEAL: raise SystemExit('V13 seal mismatch')
if live.get('real_orders_sent') is not False: raise SystemExit('REAL ORDER SAFETY BREACH')
if live.get('tuning_performed') is not False: raise SystemExit('TUNING SAFETY BREACH')

contract=records(Path('outputs/live_shadow/v13_live_shadow_contract_latest.csv'))
byma=j(Path('outputs/phase5h_executable_v4/v13_phase5h_v4_summary.json'), required=False)
byma_port=records(Path('outputs/phase5h_executable_v4/v13_phase5h_v4_current_integer_portfolio.csv'))
byma_master=records(Path('outputs/phase5h_executable_v4/v13_phase5h_v4_current_official_byma_master.csv'))
freeze=j(Path('outputs/v13_phase3aa_freeze_manifest.json'))
hold=j(Path('outputs/v13_phase4_holdout_summary.json'))

state={
  'schema':'ALPHA_ENGINE_CLOUD_STATE_V1',
  'status':'PASS',
  'model_authority':'V13_IDEAL',
  'local_implementation':'BYMA_TRANSFER',
  'freeze_id':freeze.get('freeze_id'),
  'seal_id':live.get('seal_id'),
  'holdout_verdict':hold.get('economic_verdict'),
  'asof':live.get('latest_completed_session'),
  'market':{
      'last_observed':live.get('last_observed'),
      'latest_completed_session':live.get('latest_completed_session'),
      'new_sessions':live.get('new_sessions'),
      'coverage':live.get('market_coverage_latest'),
      'sec':live.get('sec'),
  },
  'v13':{'summary':live,'targets':contract},
  'byma_transfer':{'summary':byma,'integer_portfolio':byma_port,'master':byma_master},
  'safety':{'real_orders_sent':False,'tuning_performed':False,'sheet_dependency':False},
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(state,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
print('CLOUD_STATE_EXPORT: PASS')
print('asof:',state['asof'])
print('v13_rows:',len(contract),'byma_rows:',len(byma_port),'byma_master_rows:',len(byma_master))
