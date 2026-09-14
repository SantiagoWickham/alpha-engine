from pathlib import Path
import py_compile

ROOT = Path(r"C:\Users\santi\OneDrive\Escritorio\ALPHA_ENGINE_V12_RETURN_FIRST\ALPHA_ENGINE_V13_RETURN_FIRST_MULTI_HORIZON")
TARGET = ROOT / "src" / "alpha_engine_v13" / "live_shadow.py"
MARKER = "# CLOUD_PORTABILITY_ANCHOR_OVERLAP_V1"

if not TARGET.exists():
    raise SystemExit(f"ERROR: live_shadow.py not found: {TARGET}")

text = TARGET.read_text(encoding="utf-8")

if MARKER in text:
    print("ANCHOR_HOTFIX: ALREADY_APPLIED")
    raise SystemExit(0)

needle = '    h = hist[hist.date.le(last_observed)][["date","ticker","feature_price"]].dropna().copy()\n'
if needle not in text:
    raise SystemExit(
        "ERROR: anchor-scale insertion point not found; refusing to modify runtime"
    )

injection = r"""    # CLOUD_PORTABILITY_ANCHOR_OVERLAP_V1
    # GitHub runners are stateless. A fresh Yahoo frame can begin strictly
    # AFTER last_observed, leaving _anchor_scale without an overlap row.
    # Recover ONLY the missing current-Yahoo adjusted-close anchors.
    # The original anchor coverage gate below is NOT changed or bypassed.
    _cloud_have = set(
        live.loc[live["date"].le(last_observed), "ticker"]
        .dropna()
        .astype(str)
    )
    _cloud_need = sorted(
        set(live["ticker"].dropna().astype(str)) - _cloud_have
    )

    if _cloud_need:
        import concurrent.futures as _cloud_cf
        import time as _cloud_time
        from urllib.parse import quote as _cloud_quote
        import requests as _cloud_requests

        _cloud_lo = pd.Timestamp(last_observed)
        _cloud_lo_utc = (
            _cloud_lo.tz_localize("UTC")
            if _cloud_lo.tzinfo is None
            else _cloud_lo.tz_convert("UTC")
        )
        _cloud_p1 = int(
            (_cloud_lo_utc - pd.Timedelta(days=14)).timestamp()
        )
        _cloud_p2 = int(
            (_cloud_lo_utc + pd.Timedelta(days=2)).timestamp()
        )

        if "provider_symbol" in live.columns:
            _cloud_symbols = (
                live.sort_values(["ticker", "date"])
                .dropna(subset=["ticker"])
                .groupby("ticker")["provider_symbol"]
                .last()
                .to_dict()
            )
        else:
            _cloud_symbols = {}

        def _cloud_anchor_one(_cloud_ticker):
            _cloud_symbol = str(
                _cloud_symbols.get(_cloud_ticker) or _cloud_ticker
            )
            _cloud_path = _cloud_quote(_cloud_symbol, safe="")
            _cloud_last = None

            for _cloud_host in (
                "query1.finance.yahoo.com",
                "query2.finance.yahoo.com",
            ):
                _cloud_url = (
                    f"https://{_cloud_host}/v8/finance/chart/"
                    f"{_cloud_path}"
                    f"?period1={_cloud_p1}&period2={_cloud_p2}"
                    "&interval=1d&events=div%2Csplits"
                    "&includeAdjustedClose=true"
                )

                for _cloud_attempt in range(3):
                    try:
                        _cloud_resp = _cloud_requests.get(
                            _cloud_url,
                            timeout=20,
                            headers={
                                "User-Agent":
                                    "Mozilla/5.0 AlphaEngineV13Cloud/1.0",
                                "Accept":
                                    "application/json,text/plain,*/*",
                            },
                        )

                        if _cloud_resp.status_code == 429:
                            _cloud_time.sleep(
                                1.0 + _cloud_attempt
                            )
                            continue

                        _cloud_resp.raise_for_status()
                        _cloud_payload = _cloud_resp.json()
                        _cloud_result = (
                            (_cloud_payload.get("chart") or {})
                            .get("result") or []
                        )
                        if not _cloud_result:
                            raise RuntimeError(
                                "Yahoo chart result empty"
                            )

                        _cloud_r = _cloud_result[0]
                        _cloud_ts = _cloud_r.get("timestamp") or []
                        _cloud_ind = (
                            _cloud_r.get("indicators") or {}
                        )
                        _cloud_quote_arr = (
                            (_cloud_ind.get("quote") or [{}])[0]
                        )
                        _cloud_close = (
                            _cloud_quote_arr.get("close") or []
                        )
                        _cloud_volume = (
                            _cloud_quote_arr.get("volume") or []
                        )
                        _cloud_adj = (
                            (_cloud_ind.get("adjclose") or [{}])[0]
                            .get("adjclose") or []
                        )
                        _cloud_n = len(_cloud_ts)
                        if not _cloud_n:
                            raise RuntimeError(
                                "Yahoo timestamps empty"
                            )

                        def _cloud_pad(_x):
                            _x = list(_x)
                            return (
                                _x + [None] * _cloud_n
                            )[:_cloud_n]

                        _cloud_dates = pd.Series(
                            pd.to_datetime(
                                _cloud_ts,
                                unit="s",
                                utc=True,
                                errors="coerce",
                            )
                        )
                        _cloud_dates = (
                            _cloud_dates.dt
                            .tz_convert("America/New_York")
                            .dt.tz_localize(None)
                            .dt.normalize()
                        )

                        _cloud_df = pd.DataFrame(
                            {
                                "date": _cloud_dates,
                                "ticker": _cloud_ticker,
                                "provider_symbol":
                                    _cloud_symbol,
                                "close": pd.to_numeric(
                                    pd.Series(
                                        _cloud_pad(
                                            _cloud_close
                                        )
                                    ),
                                    errors="coerce",
                                ),
                                "volume": pd.to_numeric(
                                    pd.Series(
                                        _cloud_pad(
                                            _cloud_volume
                                        )
                                    ),
                                    errors="coerce",
                                ),
                                "adj_close": pd.to_numeric(
                                    pd.Series(
                                        _cloud_pad(_cloud_adj)
                                    ),
                                    errors="coerce",
                                ),
                            }
                        )

                        _cloud_df["adj_close"] = (
                            _cloud_df["adj_close"].where(
                                _cloud_df[
                                    "adj_close"
                                ].gt(0),
                                _cloud_df["close"],
                            )
                        )

                        _cloud_df = _cloud_df[
                            _cloud_df["date"].le(
                                last_observed
                            )
                            & _cloud_df["close"].gt(0)
                            & _cloud_df[
                                "adj_close"
                            ].gt(0)
                        ].sort_values("date")

                        if _cloud_df.empty:
                            raise RuntimeError(
                                "No Yahoo overlap row "
                                "<= last_observed"
                            )

                        return (
                            _cloud_df.tail(1)
                            .iloc[0]
                            .to_dict()
                        )

                    except Exception as _cloud_exc:
                        _cloud_last = _cloud_exc
                        _cloud_time.sleep(
                            0.25
                            * (_cloud_attempt + 1)
                        )

            return {
                "_cloud_error_ticker":
                    _cloud_ticker,
                "_cloud_error":
                    str(_cloud_last),
            }

        _cloud_rows = []
        _cloud_errors = []

        with _cloud_cf.ThreadPoolExecutor(
            max_workers=8
        ) as _cloud_pool:
            for _cloud_result in _cloud_pool.map(
                _cloud_anchor_one,
                _cloud_need,
            ):
                if "_cloud_error" in _cloud_result:
                    _cloud_errors.append(
                        _cloud_result
                    )
                else:
                    _cloud_rows.append(
                        _cloud_result
                    )

        if _cloud_rows:
            live = pd.concat(
                [
                    live,
                    pd.DataFrame(_cloud_rows),
                ],
                ignore_index=True,
                sort=False,
            )
            live["date"] = pd.to_datetime(
                live["date"],
                errors="coerce",
            ).dt.normalize()
            live = (
                live.drop_duplicates(
                    ["date", "ticker"],
                    keep="last",
                )
                .sort_values(
                    ["ticker", "date"]
                )
                .reset_index(drop=True)
            )

        print(
            "CLOUD_ANCHOR_OVERLAP",
            {
                "needed":
                    len(_cloud_need),
                "recovered":
                    len(_cloud_rows),
                "failed":
                    len(_cloud_errors),
            },
        )

"""

patched = text.replace(
    needle,
    injection + needle,
    1,
)

TARGET.write_text(
    patched,
    encoding="utf-8",
)

# Fail before Phase 5B if our runtime-only adapter patch
# accidentally produced invalid Python.
py_compile.compile(
    str(TARGET),
    doraise=True,
)

print("ANCHOR_HOTFIX: PASS")
print("target:", TARGET)
