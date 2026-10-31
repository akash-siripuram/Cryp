"""The ONLY file the research loop edits. Baseline: never bet."""
import numpy as np

def fit(train):
    pass

def decide(df):
    n = len(df)
    return np.zeros(n, int), np.zeros(n)
