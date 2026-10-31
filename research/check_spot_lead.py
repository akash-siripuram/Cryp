import pandas as pd, numpy as np, json, sys
from scipy.stats import norm
d=pd.read_csv('btc_5m_updown_30d_odds.csv'); d=d[d.result.isin(['Up','Down'])].reset_index(drop=True)
cache={}
for l in open('odds_cache.jsonl'):
    j=json.loads(l); cache[j['slug']]=j['history']
sp=pd.read_csv('data/btc_spot_1m.csv').set_index('ts'); cl=sp['close']
vol=np.log(cl).diff().rolling(60).std()
up=(d.result=='Up').values
for k in range(1,5):
    P,T=[],[]
    for s,slug in zip(d.start_ts,d.slug):
        pts=[p for p in cache.get(slug,[]) if p['t']<=s+60*k]
        P.append(pts[-1]['p'] if pts else np.nan); T.append(pts[-1]['t'] if pts else np.nan)
    P,T=np.array(P),np.array(T)
    print(f'k={k} market sample age (s): median {np.nanmedian(s+60*k-T) if False else np.nanmedian(d.start_ts.values+60*k-T):.0f}')
    for lagmin in [0,1,2]:
        m=(np.floor(T/60)*60 - 60*(1+lagmin))       # candle that closed before the sample
        S=cl.reindex(m).values; sig=vol.reindex(m).values
        rem=(d.start_ts.values+300-(m+60))/60
        pm=norm.cdf(np.log(S/d.price_to_beat.values)/(sig*np.sqrt(np.maximum(rem,0.5))))
        ok=~np.isnan(pm)&~np.isnan(P)
        ll=lambda p:-np.mean(up[ok]*np.log(np.clip(p[ok],1e-4,1-1e-4))+(1-up[ok])*np.log(np.clip(1-p[ok],1e-4,1-1e-4)))
        print(f'   spot {lagmin+1}+ min older than sample: logloss market {ll(P):.4f} spot {ll(pm):.4f}')
print('--- blend: logistic on [logit(market), spot z, recent spot momentum], fit first 60%, score last 40%')
from sklearn.linear_model import LogisticRegression
lg=lambda p:np.log(np.clip(p,1e-3,1-1e-3)/(1-np.clip(p,1e-3,1-1e-3)))
for k in range(1,5):
    P,T=[],[]
    for s,slug in zip(d.start_ts,d.slug):
        pts=[p for p in cache.get(slug,[]) if p['t']<=s+60*k]
        P.append(pts[-1]['p'] if pts else np.nan); T.append(pts[-1]['t'] if pts else np.nan)
    P,T=np.array(P),np.array(T); m=np.floor(T/60)*60-60
    S=cl.reindex(m).values; sig=vol.reindex(m).values
    rem=(d.start_ts.values+300-(m+60))/60
    z=np.log(S/d.price_to_beat.values)/(sig*np.sqrt(np.maximum(rem,.5)))
    mom=np.log(S/cl.reindex(m-120).values)/sig
    X=np.c_[lg(P),z,mom]; ok=~np.isnan(X).any(1); X,y=X[ok],up[ok]
    a=int(len(y)*.6)
    ll=lambda p,yy:-np.mean(yy*np.log(p)+(1-yy)*np.log(1-p))
    m1=LogisticRegression().fit(X[:a,:1],y[:a]); m3=LogisticRegression().fit(X[:a],y[:a])
    print(f'k={k} market-only {ll(m1.predict_proba(X[a:,:1])[:,1],y[a:]):.4f}  +spot {ll(m3.predict_proba(X[a:])[:,1],y[a:]):.4f} coefs {np.round(m3.coef_[0],3)}')
