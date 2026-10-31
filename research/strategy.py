"""Fade the market's last-minute move: at k=2, bet against a big move since minute 1."""
import numpy as np
TH, STAKE = 0.15, 0.02
def fit(train): pass
def decide(df):
    d = df["p_up_2m"].values - df["p_up_1m"].values
    side = np.where(d > TH, 1, np.where(d < -TH, -1, 0))
    return side, np.full(len(df), STAKE), np.full(len(df), 2)
