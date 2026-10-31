"""Back the favorite at minute 1 when its price is in [LO, HI), fixed stake."""
import numpy as np
LO, HI, STAKE = 0.70, 0.80, 0.02
def fit(train): pass
def decide(df):
    p = df["p_up_1m"].values
    side = np.where((p >= LO) & (p < HI), 1, np.where((1 - p >= LO) & (1 - p < HI), -1, 0))
    return side, np.full(len(df), STAKE), np.ones(len(df), int)
