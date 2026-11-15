#!/usr/bin/env python3
"""btc-cent-forecast-01 — wallet w4 entry.

Linear-trend extrapolation blend: OLS regression of log(price) against time
over the last 720 minutes, extrapolated 240 minutes ahead; the forecast is
the 50/50 blend of that extrapolated price and the checkpoint's last close,
with the total move clamped to +/-2% of the last close. Falls back to the
last close when fewer than 100 prices are available.

Python 3.13, standard library only, no network. Deterministic: same input
bytes always produce the same output bytes.

Usage (outside the grader): MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out
python3 main.py
"""

import json
import math
import os
from pathlib import Path

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR") or "/input"
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"

MIN_PRICE = 0.00001
MAX_PRICE = 9_999_999.99999

WINDOW = 720          # minutes of history used for the log-price regression
HORIZON = 240         # minutes ahead to extrapolate
BLEND = 0.5           # weight on the extrapolated price (rest on last close)
MAX_SHIFT = 0.02      # clamp total move to +/-2% of the last close
MIN_PRICES = 100      # fallback to last close below this many prices


def price5(x: float) -> float:
    """Keep x on the grid's 5 decimals and inside (0, 10_000_000)."""
    if not math.isfinite(x):
        raise ValueError("non-finite price")
    return round(min(MAX_PRICE, max(MIN_PRICE, x)) * 1e5) / 1e5


def forecast(prices) -> float:
    """One forecast for a list of one-minute closes, last = checkpoint."""
    if not prices:
        raise ValueError("market has no prices")
    last = float(prices[-1])
    if not math.isfinite(last) or last <= 0:
        raise ValueError("last price is not a finite positive number")

    if len(prices) < MIN_PRICES:
        return price5(last)

    window = prices[-WINDOW:]
    n = len(window)
    # Log-prices only exist for positive prices; drop any non-positive
    # (or non-finite) bar instead of letting math.log kill the whole case.
    # Keep the time index of each surviving bar so the slope stays honest.
    points = []
    for t, p in enumerate(window):
        v = float(p)
        if math.isfinite(v) and v > 0:
            points.append((t, math.log(v)))
    if len(points) < MIN_PRICES:
        return price5(last)
    n = len(points)
    t_mean = sum(t for t, _ in points) / n
    y_mean = sum(y for _, y in points) / n
    sxx = sum((t - t_mean) ** 2 for t, _ in points)
    if sxx == 0:
        return price5(last)
    sxy = sum((t - t_mean) * (y - y_mean) for t, y in points)
    slope = sxy / sxx
    intercept = y_mean - slope * t_mean
    # Extrapolate to the checkpoint (t = n - 1 of the window) + HORIZON.
    log_extrap = intercept + slope * ((len(window) - 1) + HORIZON)
    extrapolated = math.exp(log_extrap)

    blended = BLEND * extrapolated + (1.0 - BLEND) * last
    # Clamp the total move to +/-2% of the last close.
    lo = last * (1.0 - MAX_SHIFT)
    hi = last * (1.0 + MAX_SHIFT)
    return price5(min(hi, max(lo, blended)))


def main() -> None:
    in_dir = Path(INPUT_DIR)
    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    inputs = sorted(
        p for p in in_dir.iterdir() if p.is_file() and p.name.endswith(".in")
    )
    for path in inputs:
        case_id = path.name[: -len(".in")]
        with path.open("r", encoding="utf-8") as fh:
            case = json.load(fh)
        markets = case.get("markets")
        if not isinstance(markets, list) or len(markets) != 1:
            raise ValueError(f"{path.name} does not hold exactly one market")
        price = forecast(markets[0]["prices"])
        payload = {"forecasts": [{"case": case_id, "price": price}]}
        out_path = out_dir / f"{case_id}.out"
        with out_path.open("w", encoding="utf-8") as fh:
            fh.write(json.dumps(payload) + "\n")


if __name__ == "__main__":
    main()
