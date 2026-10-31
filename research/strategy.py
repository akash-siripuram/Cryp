"""Recalibrate the market price at a fixed minute k, bet when the edge beats costs.

fit: logistic regression of outcome on logit(p_up_km) on train.
decide: model prob q vs price; bet the side with expected value > MARGIN,
stake = KELLY_MULT * Kelly fraction.
"""
import numpy as np
from sklearn.linear_model import LogisticRegression

K = 1
MARGIN = 0.0
KELLY_MULT = 0.25
SLIP, FEE = 0.01, 0.01
COL = ["p_up_open", "p_up_1m", "p_up_2m", "p_up_3m", "p_up_4m"][K]
model = None

def logit(p):
    p = np.clip(p, 1e-3, 1 - 1e-3)
    return np.log(p / (1 - p))

def fit(train):
    global model
    model = LogisticRegression().fit(logit(train[COL].values)[:, None], train["result"] == "Up")

def decide(df):
    p = df[COL].values
    q = model.predict_proba(logit(p)[:, None])[:, 1]
    cost_up, cost_dn = p + SLIP, 1 - p + SLIP
    ev_up = q / cost_up - 1 - FEE
    ev_dn = (1 - q) / cost_dn - 1 - FEE
    side = np.where((ev_up > MARGIN) & (ev_up >= ev_dn), 1, np.where(ev_dn > MARGIN, -1, 0))
    qw = np.where(side > 0, q, 1 - q); c = np.where(side > 0, cost_up, cost_dn)
    b = 1 / c - 1
    kelly = np.clip((qw * b - (1 - qw)) / b, 0, None)
    return side, np.where(side != 0, KELLY_MULT * kelly, 0.0), np.full(len(df), K)
