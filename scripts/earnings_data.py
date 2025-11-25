from typing import Any

import datatime as dt
import yfinance as yf

import logging

logger = logging.getLogger(__name__)


def get_earnings_calendar(
    symbols: list[str] | str,
    num: int = 1,
) -> list[dict[str, Any]]:
    """Explore earnings data for one or more symbols using yfinance.

    This helper is designed to back an agent-visible tool that can answer
    questions like:

    - "When is the next earnings date for AAPL?"
    - "Show me the last few earnings for MSFT and when they report next."

    Semantics:

    - ``symbols`` may be a single ticker symbol or a list of symbols.
    - ``num`` controls how many earnings *events* to surface per symbol.
        - If ``num <= 1``, only the next earnings date (if any) is returned.
        - If ``num > 1``, the response includes:
        - The next earnings date (if any), and
        - Up to ``num - 1`` most recent past earnings events.

    The return value is a list of dicts, one per symbol, of the form::

        {
            "symbol": "AAPL",
            "next_earnings_date": "2026-01-29" | None,
            "next_earnings_estimate": 2.66 | None,
            "past_earnings": [
            {
                "date": "2024-10-24",
                "eps_estimate": 2.10,
                "eps_actual": 2.20,
                "surprise_percent": 4.76,
            },
            ...,
            ],
        }

    Any symbol that cannot be looked up or has no data returns an entry
    with empty/None-valued fields instead of raising.
    """

    if num <= 0:
        num = 1

    today = dt.date.today()

    # Normalize symbols input to a list of upper-case strings.
    if isinstance(symbols, str):
        symbol_list = [symbols]
    else:
        symbol_list = list(symbols)

    normalized_symbols: list[str] = []
    for sym in symbol_list:
        sym = (sym or "").strip()
        if not sym:
            continue
        normalized_symbols.append(sym.upper())

    results: list[dict[str, Any]] = []

    for sym in normalized_symbols:
        entry: dict[str, Any] = {
            "symbol": sym,
            "next_earnings_date": None,
            "next_earnings_estimate": None,
            "past_earnings": [],
        }

        try:
            ticker = yf.Ticker(sym)
            try:
                df = ticker.get_earnings_dates(limit=max(num + 4, 8))
            except Exception:  # pragma: no cover - defensive
                df = getattr(ticker, "calendar", None)

            if df is None or getattr(df, "empty", False):
                results.append(entry)
                continue

            # Collect (date, row) pairs from the DataFrame index + rows.
            rows: list[tuple[dt.date, Any]] = []
            for idx, row in df.iterrows():
                try:
                    if hasattr(idx, "date"):
                        date_obj = idx.date()
                    else:
                        date_obj = dt.date.fromisoformat(str(idx)[:10])
                except Exception:  # pragma: no cover - defensive
                    continue

                rows.append((date_obj, row))

            if not rows:
                results.append(entry)
                continue

            # Sort by date ascending so we can find the next future event
            # and most recent past events easily.
            rows.sort(key=lambda pair: pair[0])

            future_rows = [(d, r) for d, r in rows if d >= today]
            past_rows = [(d, r) for d, r in rows if d < today]

            # Next earnings date (if any).
            if future_rows:
                next_date, next_row = future_rows[0]
                entry["next_earnings_date"] = next_date.isoformat()

                # Try to grab an EPS estimate for the next event.
                est = None
                for key in ("EPS Estimate", "epsestimate", "Estimate", "estimate"):
                    if key in next_row and next_row[key] is not None:
                        try:
                            est = float(next_row[key])
                            break
                        except (TypeError, ValueError):  # pragma: no cover - defensive
                            continue
                entry["next_earnings_estimate"] = est

            # Past earnings events (most recent first), up to num-1 entries.
            max_past = max(num - 1, 0)
            if max_past > 0 and past_rows:
                past_rows_sorted = sorted(past_rows, key=lambda pair: pair[0], reverse=True)
                for date_obj, row in past_rows_sorted[:max_past]:
                    eps_estimate = None
                    eps_actual = None
                    surprise_pct = None

                    for key in ("EPS Estimate", "epsestimate", "Estimate", "estimate"):
                        if key in row and row[key] is not None:
                            try:
                                eps_estimate = float(row[key])
                                break
                            except (TypeError, ValueError):  # pragma: no cover - defensive
                                continue

                    for key in ("Reported EPS", "reportedEPS", "epsactual", "actual"):
                        if key in row and row[key] is not None:
                            try:
                                eps_actual = float(row[key])
                                break
                            except (TypeError, ValueError):  # pragma: no cover - defensive
                                continue

                    for key in ("Surprise(%)", "surprise", "surprise_percent"):
                        if key in row and row[key] is not None:
                            try:
                                surprise_pct = float(row[key])
                                break
                            except (TypeError, ValueError):  # pragma: no cover - defensive
                                continue

                    entry["past_earnings"].append(
                        {
                            "date": date_obj.isoformat(),
                            "eps_estimate": eps_estimate,
                            "eps_actual": eps_actual,
                            "surprise_percent": surprise_pct,
                        }
                    )

        except Exception:  # pragma: no cover - defensive
            logger.exception("Failed to fetch earnings via yfinance for symbol %s", sym)

        results.append(entry)

    return results