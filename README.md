# btc-cent-forecast-01 — wallet w4

Forecast Bitcoin's price 240 minutes after each checkpoint.

## Approach (variant w4: linear-trend extrapolation blend)

1. Take the last **720 minutes** (12 hours) of one-minute closes.
2. Run an OLS linear regression of **log(price) against time** on that window.
3. Extrapolate the fitted line **+240 minutes** past the checkpoint and
   exponentiate back to a price.
4. Forecast = **0.5 × extrapolated price + 0.5 × last close** — the trend
   moves the guess, the checkpoint close anchors it.
5. Clamp the total move to **±2% of the last close**, so a steep fitted
   slope can never drag the guess far from the checkpoint price.

## Safety

- Fewer than 100 prices in the case (or fewer than 100 usable positive
  prices in the window) → forecast = last close (persistence fallback).
- Non-positive / non-finite bars are dropped from the regression instead of
  crashing it; a degenerate (flat) window also falls back to the last close.
- Output price is kept on the grid's 5 decimals and inside (0, 10,000,000).

## Running

Python 3.13, standard library only, no network, deterministic.

```sh
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Reads every `<id>.in` in the input directory and writes `<id>.out`
(`{"forecasts":[{"case":"<id>","price":<number>}]}`) for each.
