# %% [markdown]
# # Pump or Dump: EV-optimal take-profit with calibrated level models
#
# What this notebook does differently from the starter notebooks:
#
# 1. **More history.** It trains on `train_archive.csv` and `train.csv` together, which means
#    every labelled day since the tape began, with recency weights. It is not limited to the
#    30-day window. Wallet and creator reputation also get the full history.
# 2. **More features.** Holder concentration at the snapshot, creator behaviour on the curve,
#    sniper share, sell pressure inside the first minute, pool depth, and a legal market-regime
#    signal. Regime uses only tokens that resolved at least one hour earlier.
# 3. **A per-token take-profit.** tp is not fixed at 5. One classifier per level estimates
#    P(max_x >= L). Each is calibrated on held-out, embargoed days. The notebook picks the level
#    with the highest expected value:
#    `EV(L) = P(L)·(L − 1.3) + (1 − P(L))·E[held | miss L]`.
#    It buys only when that EV clears a fixed margin.
# 4. **One decision per token.** Every token is decided from its own features and a threshold
#    fixed from training data only. Nothing depends on the other test tokens.
#
# Set `RUN_VALIDATION = True` to run an embargoed walk-forward over the last labelled days.
# The submission run keeps it off so the run stays well inside the 1-hour bot limit.

# %%
import os, glob, gc, re, time, warnings
import numpy as np, pandas as pd
import lightgbm as lgb
from sklearn.linear_model import LogisticRegression
warnings.filterwarnings('ignore')
T_START = time.time()

COST, WIN = 0.3, 3600            # trading cost; label window / resolution lag (s)
EMBARGO = 3600                   # extra gap between train labels and the day being scored
LEVELS = [3.0, 4.0, 5.0, 6.5, 8.0, 10.0, 13.0, 17.0]
MARGIN = float(os.environ.get('PD_MARGIN', 0.35))   # minimum EV per position to buy
HOLD_DAYS = 7                    # labelled days held out for calibration
HALF_LIFE_DAYS = 30.0            # recency weight half-life for training rows
SEEDS = [0, 1, 2]
RUN_VALIDATION = os.environ.get('PD_VALIDATE', '0') == '1'
VAL_DAYS = int(os.environ.get('PD_VAL_DAYS', 14))
N_JOBS = 4
USE_MISS_MODEL = os.environ.get('PD_MISS_MODEL', '1') == '1'
MISS_SHRINK = 0.5
SOL_MINT = 'So11111111111111111111111111111111111111112'
SUPPLY = 1e9                     # pump.fun total supply in whole tokens

DATA = next(p for p in ['/kaggle/input/competitions/memecoins-pump-or-dump',
                        '/kaggle/input/memecoins-pump-or-dump', 'data']
            if os.path.exists(p))
train = pd.read_csv(f'{DATA}/train.csv').rename(columns={'finalx': 'final_x'})
test = pd.read_csv(f'{DATA}/test.csv')
arch_path = f'{DATA}/train_archive.csv'
archive = (pd.read_csv(arch_path).rename(columns={'finalx': 'final_x'})
           if os.path.exists(arch_path) else train.iloc[:0])
LAB = (pd.concat([archive[['mint', 'mt', 'max_x', 'final_x']],
                  train[['mint', 'mt', 'max_x', 'final_x']]], ignore_index=True)
       .drop_duplicates('mint', keep='last'))
LAB = LAB[~LAB.mint.isin(test.mint)]
ALLTOK = (pd.concat([LAB[['mint', 'mt']], test[['mint', 'mt']]], ignore_index=True)
          .sort_values('mt', kind='stable').reset_index(drop=True))
ALLTOK['day'] = pd.to_datetime(ALLTOK.mt, unit='s').dt.strftime('%Y-%m-%d')
ALLTOK['is_test'] = ALLTOK.mint.isin(set(test.mint)).astype(np.int8)

if os.path.exists(f'{DATA}/trades'):
    DAYS = [(d.split('=')[-1], f'{d}/pumpfun_all_swaps.parquet', f'{d}/pumpswap_all_swaps.parquet')
            for d in sorted(glob.glob(f'{DATA}/trades/day=*'))]
else:
    DAYS = [(os.path.basename(f)[4:14], f, f.replace('pumpfun_all_swaps', 'pumpswap_all_swaps'))
            for f in sorted(glob.glob(f'{DATA}/day_*_pumpfun_all_swaps.parquet'))]
need_days = set(ALLTOK.day)
DAYS = [d for d in DAYS if d[0] in need_days]
print(f'{len(DAYS)} tape days | labelled {len(LAB)} (archive {len(archive)}) | test {len(test)}')


def pnl(tp, max_x, final_x, cost=COST):
    tp = np.asarray(tp, float)
    hit = (max_x >= tp) & (tp > 0)
    held = np.maximum(final_x - 1 - cost, -1.0)
    return np.where(tp <= 0, 0.0, np.where(hit, tp - 1 - cost, held))

# %% [markdown]
# ## Launch metadata

# %%
cre = pd.read_csv(f'{DATA}/pumpfun_token_creation.csv', low_memory=False).drop_duplicates('mint')
CREATOR = dict(zip(cre.mint, cre.creator.astype(str))) if 'creator' in cre.columns else {}
name = cre.name.fillna('').astype(str) if 'name' in cre.columns else pd.Series([''] * len(cre))
sym = cre.symbol.fillna('').astype(str) if 'symbol' in cre.columns else pd.Series([''] * len(cre))
bs = (cre.bundle_structure.fillna('').astype(str) if 'bundle_structure' in cre.columns
      else pd.Series([''] * len(cre)))
M = pd.DataFrame({'mint': cre.mint.values})
M['name_len'] = name.str.len().values
M['symbol_len'] = sym.str.len().values
M['name_upper'] = name.apply(lambda s: sum(ch.isupper() for ch in s) / max(len(s), 1)).values
M['name_words'] = name.str.split().str.len().fillna(0).values
M['name_eq_symbol'] = (name.str.lower().str[:4] == sym.str.lower().str[:4]).astype(int).values
M['bs_ops'] = bs.str.split().str.len().fillna(0).values
M['bs_buys'] = bs.apply(lambda s: len(re.findall(r'\dB\d', s))).values
amt = bs.apply(lambda s: [int(x) for x in re.findall(r':(\d{6,})', s)])
M['bs_amt_sum'] = amt.apply(lambda v: float(np.sum(v)) if v else 0.0).values
M['bs_amt_max'] = amt.apply(lambda v: float(np.max(v)) if v else 0.0).values
for c_ in ['gas_used', 'amount_of_instructions', 'amount_of_lookup_reads', 'amount_of_lookup_writes',
           'creation_ix_index', 'pf_program_index', 'direct_pf_invocation', 'is_cashback_enabled',
           'bundle_size', 'bundled_buys', 'bundled_buys_count', 'dev_balance']:
    if c_ in cre.columns:
        M[c_] = pd.to_numeric(cre[c_], errors='coerce').values
if 'token_program' in cre.columns:
    M['token2022'] = (~cre.token_program.fillna('').astype(str).str.startswith('Tokenkeg')).astype(int).values
M['created_ts'] = pd.to_numeric(cre.created_ts, errors='coerce').values

mig_path = f'{DATA}/pfamm_migrations.csv'
if os.path.exists(mig_path):
    mig = pd.read_csv(mig_path, low_memory=False)
    mcol = 'mint' if 'mint' in mig.columns else None
    if mcol and 'sol_amount' in mig.columns:
        MIG = (mig.assign(mig_sol=pd.to_numeric(mig.sol_amount, errors='coerce') / 1e9)
               .groupby(mcol, as_index=False).mig_sol.last().rename(columns={mcol: 'mint'}))
        M = M.merge(MIG, on='mint', how='left')

# %% [markdown]
# ## Tape features: one day at a time, file order preserved

# %%
CURVE_COLS = ['failed', 'mint', 'ts_rel', 'direction', 'sol', 'tok', 'new_price', 'wallet',
              'parent_program', 'tip_index', 'fee', 'provided_gas_fee', 'slot', 'signature']
ROUTERS = {
    'FLASHX8DrLbgeR8FcfNV1F5krxYcYMUdBkrP1EPBtxB9': 'photon',
    '6Vo3245eszAb5wuqEMw8mGdbfRUdKbHhDHP5LcaGuTAB': 'r6v0',
    'GMgnVFR8Jb39LoXsEVzb3DvBy3ywCmdmJquHUy1Lrkqb': 'gmgn',
    'DF1ow4tspfHX9JwWJsAb9epbkA8hmpSEAtxXy1V27QBH': 'df1o',
    'JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4': 'jupiter',
    'term9YPb9mzAsABaqN71A4xdbxHmpBNZavpBiQKZzN3': 'trojan',
    'AKbotMAGJmYPwV8z55Lqiqgijt2KcjLeFGue5sw1noHM': 'akbot',
}
AMM_COLS = ['mint', 'ts_rel', 'direction', 'sol', 'tok', 'new_price', 'signing_wallet', 'fee_payer',
            'pool_quote_token_reserves_after', 'virtual_quote_reserves', 'parent_program',
            'slot', 'signature']


def exec_features(df, prefix):
    """Execution fingerprints: routers/bots, Jito tips, priority fees, slot crowding."""
    g = df.groupby('mint', sort=False); X = pd.DataFrame(index=g.size().index)
    if 'parent_program' in df.columns:
        pp = df.parent_program.fillna('').astype(str)
        X[f'{prefix}_router_share'] = pp.ne('').groupby(df.mint).mean()
        X[f'{prefix}_router_unique'] = pp.where(pp.ne('')).groupby(df.mint).nunique()
        for addr, short in ROUTERS.items():
            X[f'{prefix}_r_{short}'] = pp.eq(addr).groupby(df.mint).mean()
    if 'tip_index' in df.columns:
        X[f'{prefix}_tip_share'] = (pd.to_numeric(df.tip_index, errors='coerce').fillna(-1) >= 0
                                    ).groupby(df.mint).mean()
    for col in ('fee', 'provided_gas_fee'):
        if col in df.columns:
            v = pd.to_numeric(df[col], errors='coerce') / 1e9
            X[f'{prefix}_{col}_mean'] = v.groupby(df.mint).mean()
            X[f'{prefix}_{col}_q90'] = v.groupby(df.mint).quantile(0.9)
    if 'slot' in df.columns:
        sc = df.groupby(['mint', 'slot']).size()
        X[f'{prefix}_slots'] = sc.groupby(level=0).size()
        X[f'{prefix}_max_slot_share'] = sc.groupby(level=0).max() / g.size()
    if 'signature' in df.columns:
        tc = df.groupby(['mint', 'signature']).size()
        X[f'{prefix}_multi_swap_tx'] = (tc[tc > 1].groupby(level=0).sum()
                                        .reindex(X.index).fillna(0) / g.size())
    return X


def safe_read(path, cols):
    import pyarrow.parquet as pq
    have = set(pq.read_schema(path).names)
    return pd.read_parquet(path, columns=[c for c in cols if c in have])


def div(a, b):
    b = b.replace(0, np.nan) if isinstance(b, pd.Series) else (np.nan if b == 0 else b)
    return a / b


def tape_features(c, a):
    for df in (c, a):
        df['is_buy'] = df.direction.astype(str).str.upper().str.startswith('B').astype(np.int8)
    c['creator'] = c.mint.map(CREATOR)
    a['creator'] = a.mint.map(CREATOR)
    g = a.groupby('mint', sort=False)
    F = pd.DataFrame(index=pd.Index(a.mint.unique(), name='mint'))
    buys, sells = a[a.is_buy == 1], a[a.is_buy == 0]
    # --- first minute on the AMM: participation and flow
    F['amm_n'] = g.size()
    F['amm_sol'] = g.sol.sum()
    F['amm_uw'] = g.wallet.nunique()
    F['amm_buy_n'] = buys.groupby('mint').size()
    F['amm_sell_n'] = sells.groupby('mint').size()
    F['amm_buy_sol'] = buys.groupby('mint').sol.sum()
    F['amm_sell_sol'] = sells.groupby('mint').sol.sum()
    F[['amm_buy_n', 'amm_sell_n', 'amm_buy_sol', 'amm_sell_sol']] = \
        F[['amm_buy_n', 'amm_sell_n', 'amm_buy_sol', 'amm_sell_sol']].fillna(0)
    F['amm_net_sol'] = F.amm_buy_sol - F.amm_sell_sol
    F['amm_buyshare'] = div(F.amm_buy_sol, F.amm_sol)
    F['trades_per_wallet'] = div(F.amm_n, F.amm_uw)
    ws = buys.groupby(['mint', 'wallet']).sol.sum()
    F['amm_top1'] = div(ws.groupby('mint').max(), ws.groupby('mint').sum())
    F['amm_buyers'] = buys.groupby('mint').wallet.nunique()
    F['amm_sellers'] = sells.groupby('mint').wallet.nunique()
    F['buy_max'] = buys.groupby('mint').sol.max()
    F['buy_med'] = buys.groupby('mint').sol.median()
    F['whale_buys'] = buys[buys.sol >= 5].groupby('mint').size().reindex(F.index).fillna(0)
    F['sell_max'] = sells.groupby('mint').sol.max()
    F['fp_diff_share'] = (a.assign(d=(a.get('fee_payer', a.wallet) != a.wallet).astype(float))
                          .groupby('mint').d.mean())
    for lo, hi, tag in [(0, 15, 'e'), (15, 45, 'm'), (45, 61, 'l')]:
        w = a[(a.ts_rel >= lo) & (a.ts_rel < hi)]
        b_ = w[w.is_buy == 1].groupby('mint').sol.sum()
        s_ = w[w.is_buy == 0].groupby('mint').sol.sum()
        F[f'net_{tag}'] = b_.reindex(F.index).fillna(0) - s_.reindex(F.index).fillna(0)
        F[f'n_{tag}'] = w.groupby('mint').size().reindex(F.index).fillna(0)
    F['late_over_early'] = div(F.n_l, F.n_e)
    last10 = a[a.ts_rel >= 50]
    F['net_last10'] = (last10.assign(s=np.where(last10.is_buy == 1, last10.sol, -last10.sol))
                       .groupby('mint').s.sum().reindex(F.index).fillna(0))
    early_w = a[a.ts_rel < 15].groupby('mint').wallet.apply(set)
    late_w = a[a.ts_rel >= 45].groupby('mint').wallet.apply(set)
    F['fresh_wallets'] = pd.Series({m: len(s - early_w.get(m, set())) for m, s in late_w.items()})
    eb = a[(a.ts_rel <= 15) & (a.is_buy == 1)].groupby('mint').wallet.apply(set)
    sw = sells.groupby('mint').wallet.apply(set)
    F['flip_rate'] = pd.Series({m: len(s & sw.get(m, set())) / max(len(s), 1) for m, s in eb.items()})
    # --- price path in the first minute (reserve price; file order = chain order)
    ap = a[a.new_price > 0]
    gp = ap.groupby('mint', sort=False).new_price
    p_first, p_last, p_max, p_min = gp.first(), gp.last(), gp.max(), gp.min()
    F['ret60'] = div(p_last, p_first)
    F['runup'] = div(p_max, p_first)
    F['at_high'] = div(p_last, p_max)
    F['above_low'] = div(p_last, p_min)
    lp = np.log(ap.new_price)
    F['vol'] = lp.groupby(ap.mint).std()
    dl = lp.groupby(ap.mint).diff()
    F['vol_step'] = dl.groupby(ap.mint).std()
    F['ret_last15'] = div(p_last, ap[ap.ts_rel <= 45].groupby('mint').new_price.last())
    F['log_entry'] = np.log(p_last)
    if 'pool_quote_token_reserves_after' in a.columns:
        q = (a.pool_quote_token_reserves_after.astype(float) +
             a.get('virtual_quote_reserves', 0).astype(float)) / 1e9
        F['depth_sol'] = q.groupby(a.mint).last()
        F['depth_chg'] = div(F.depth_sol, q.groupby(a.mint).first())
    # --- holders at the snapshot (curve + AMM net token flow per wallet)
    ok = c[c.failed == 0]
    flows = pd.concat([
        ok[['mint', 'wallet', 'tok', 'is_buy']],
        a[['mint', 'wallet', 'tok', 'is_buy']]], ignore_index=True)
    flows['net'] = np.where(flows.is_buy == 1, flows.tok, -flows.tok)
    hold = flows.groupby(['mint', 'wallet']).net.sum()
    hold = hold[hold > 0]
    hs = hold.groupby(level=0)
    srt = hold.sort_values(ascending=False).groupby(level=0)
    F['holders'] = hs.size()
    F['top1_share'] = hs.max() / SUPPLY
    F['top10_share'] = srt.head(10).groupby(level=0).sum() / SUPPLY
    F['top50_share'] = srt.head(50).groupby(level=0).sum() / SUPPLY
    # creator
    cf = flows[flows.wallet == flows.mint.map(CREATOR)]
    F['dev_hold_share'] = (cf.groupby('mint').net.sum() / SUPPLY).reindex(F.index).fillna(0)
    F['dev_sells'] = cf[cf.is_buy == 0].groupby('mint').size().reindex(F.index).fillna(0)
    F['dev_buy_tok'] = cf[cf.is_buy == 1].groupby('mint').tok.sum().reindex(F.index).fillna(0) / SUPPLY
    # --- the curve
    gc_ = ok.groupby('mint', sort=False)
    F['curve_n'] = gc_.size()
    F['curve_sol'] = gc_.sol.sum()
    F['curve_uw'] = gc_.wallet.nunique()
    F['curve_dur'] = -gc_.ts_rel.min()
    F['curve_sell_share'] = ok.assign(s=1 - ok.is_buy).groupby('mint').s.mean()
    F['curve_tiny_share'] = ok.assign(t=(ok.sol < 0.01).astype(float)).groupby('mint').t.mean()
    cw = ok[ok.is_buy == 1].groupby(['mint', 'wallet']).sol.sum()
    F['curve_top10_sol'] = div(cw.sort_values(ascending=False).groupby(level=0).head(10)
                               .groupby(level=0).sum(), cw.groupby(level=0).sum())
    fin = ok[ok.ts_rel < 0]
    for w_ in (60, 300):
        z = fin[fin.ts_rel >= -w_]
        F[f'curve_sol_last{w_}'] = z.groupby('mint').sol.sum().reindex(F.index).fillna(0)
        F[f'curve_uw_last{w_}'] = z.groupby('mint').wallet.nunique().reindex(F.index).fillna(0)
    F['curve_speed_ratio'] = div(F.curve_sol_last300, F.curve_sol)
    first_ts = gc_.ts_rel.transform('min')
    snip = ok[ok.ts_rel <= first_ts + 5]
    F['snipe_sol'] = snip[snip.is_buy == 1].groupby('mint').sol.sum().reindex(F.index).fillna(0)
    F['snipe_uw'] = snip.groupby('mint').wallet.nunique().reindex(F.index).fillna(0)
    F['curve_failed'] = c[c.failed != 0].groupby('mint').size().reindex(F.index).fillna(0)
    F['failed_share'] = div(F.curve_failed, F.curve_failed + F.curve_n.fillna(0))
    lf = c[(c.failed != 0) & (c.ts_rel >= -60)]
    F['failed_last60'] = lf.groupby('mint').size().reindex(F.index).fillna(0)
    curve_last = ok[ok.new_price > 0].groupby('mint').new_price.last()
    F['migration_pop'] = div(p_first, curve_last)
    # AMM wallets that held curve tokens and are selling
    cbw = ok[ok.is_buy == 1][['mint', 'wallet']].drop_duplicates()
    sold = sells.merge(cbw, on=['mint', 'wallet'])
    F['curve_holders_dump_sol'] = sold.groupby('mint').sol.sum().reindex(F.index).fillna(0)
    F['curve_holders_dump_share'] = div(F.curve_holders_dump_sol, F.amm_sell_sol)
    F = F.join(exec_features(ok, 'cx'), how='left').join(exec_features(c, 'ca'), how='left',
                                                           rsuffix='_all')
    F = F.join(exec_features(a, 'ax'), how='left')
    keep = [k for k in F.columns if not k.startswith('ca_') or k in
            ('ca_tip_share', 'ca_provided_gas_fee_mean', 'ca_provided_gas_fee_q90')]
    return F[keep]


t0 = time.time(); frames = []; EDGE_A = []; EDGE_C = []
NEED_MINTS = set(ALLTOK.mint)
for i, (day, cp, ap_) in enumerate(DAYS, 1):
    c = safe_read(cp, CURVE_COLS)
    a = safe_read(ap_, AMM_COLS).rename(columns={'signing_wallet': 'wallet'})
    c = c[c.mint.isin(NEED_MINTS)]
    a = a[a.mint.isin(NEED_MINTS)]
    if 'tok' not in c.columns: c['tok'] = 0.0
    if 'tok' not in a.columns: a['tok'] = 0.0
    frames.append(tape_features(c, a).reset_index())
    # reputation edges: first-minute AMM buyers, and the first 30 executed curve buyers (snipers)
    b = a[a.is_buy == 1]
    EDGE_A.append(b.groupby(['mint', 'wallet'], as_index=False).sol.sum())
    okb = c[(c.failed == 0) & (c.is_buy == 1)]
    okb = okb.groupby('mint', sort=False).head(30)
    EDGE_C.append(okb.groupby(['mint', 'wallet'], as_index=False).sol.sum())
    del c, a, b, okb; gc.collect()
    if i % 10 == 0 or i == len(DAYS):
        print(f'  tape {i}/{len(DAYS)} ({time.time()-t0:.0f}s)', flush=True)
TAPE = pd.concat(frames, ignore_index=True).drop_duplicates('mint', keep='last')
TAPE = TAPE.replace([np.inf, -np.inf], np.nan)
del frames; gc.collect()

# %% [markdown]
# ## History features under the resolution rule
#
# On the test day, labels exist only for tokens that migrated before (test-day start − 2 h).
# Every token, train or test, therefore uses the same information horizon:
# `cut_i = UTC-day-start(mt_i) − 2 h`. An outcome is used only if `mt_j < cut_i`. That is
# stricter than the one-hour resolution rule, and train and test features keep the same
# distribution. Migration counts (public immediately) use every earlier token.

# %%
T = ALLTOK.merge(LAB[['mint', 'max_x', 'final_x']].rename(columns={'max_x': 'mx', 'final_x': 'fx'}),
                 on='mint', how='left')
T = T.sort_values('mt', kind='stable').reset_index(drop=True)
mts, mx, fx, mints = T.mt.values.astype(np.int64), T.mx.values, T.fx.values, T.mint.values
n = len(T)
labelled = ~np.isnan(mx)
h3 = np.where(labelled, mx >= 3, 0).astype(np.int32)
h5 = np.where(labelled, mx >= 5, 0).astype(np.int32)
dead = np.where(labelled, fx < 0.2, 0).astype(np.int32)
logmx = np.where(labelled, np.log(np.clip(mx, 1e-3, None)), 0.0)

# market regime: resolved hit rates over trailing windows, and migration intensity
cum = lambda v: np.concatenate([[0], np.cumsum(v)])
c_lab, c_h3, c_h5, c_lm = cum(labelled.astype(int)), cum(h3), cum(h5), cum(logmx)
REG = {}
cut = (mts // 86400) * 86400 - 7200                            # label horizon, same for train/test
resolved_end = np.searchsorted(mts, cut, side='left')            # tokens with mt_j < cut_i
for hrs in (6, 24, 72):
    start = np.searchsorted(mts, cut - hrs * 3600, side='left')
    nl = c_lab[resolved_end] - c_lab[start]
    REG[f'reg_n_{hrs}h'] = nl
    REG[f'reg_h3_{hrs}h'] = (c_h3[resolved_end] - c_h3[start] + 0.14 * 20) / (nl + 20)
    REG[f'reg_h5_{hrs}h'] = (c_h5[resolved_end] - c_h5[start] + 0.06 * 20) / (nl + 20)
    REG[f'reg_lmx_{hrs}h'] = (c_lm[resolved_end] - c_lm[start]) / np.maximum(nl, 1)
cur = np.searchsorted(mts, mts, side='left')                    # strictly earlier migrations
for hrs in (1, 6):
    REG[f'mig_rate_{hrs}h'] = cur - np.searchsorted(mts, mts - hrs * 3600, side='left')
REG = pd.DataFrame(REG); REG['mint'] = mints
hod = pd.to_datetime(T.mt, unit='s')
REG['hour'] = hod.dt.hour.values
REG['dow'] = hod.dt.dayofweek.values


def reputation(edges, prefix, prior_n=4.0):
    E = pd.concat(edges, ignore_index=True)
    E = E[E.mint.isin(set(mints))]
    E['wid'] = E.wallet.astype('category').cat.codes.astype(np.int64)
    nW = int(E.wid.max()) + 1 if len(E) else 1
    by = {m: (g.wid.values, g.sol.values.astype(float))
          for m, g in E.sort_values('mint', kind='stable').groupby('mint', sort=False)}
    app = np.zeros(nW, np.float64); hit3 = np.zeros(nW); hit5 = np.zeros(nW); dd = np.zeros(nW)
    base3, base5, based = 0.14, 0.06, 0.6
    cols = ['known', 'h3_max', 'h3_wmean', 'h5_max', 'h5_wmean', 'h5_top3', 'dead_wmean',
            'elite_n', 'elite_sol_share', 'rugger_sol_share', 'exp_wmean']
    out = np.full((n, len(cols)), np.nan); j = 0
    for i in range(n):
        while j < n and mts[j] < cut[i]:
            if labelled[j]:
                w = by.get(mints[j])
                if w is not None:
                    np.add.at(app, w[0], 1); np.add.at(hit3, w[0], h3[j])
                    np.add.at(hit5, w[0], h5[j]); np.add.at(dd, w[0], dead[j])
            j += 1
        w = by.get(mints[i])
        if w is None: continue
        wid, sol = w
        ap = app[wid]
        r3 = (hit3[wid] + prior_n * base3) / (ap + prior_n)
        r5 = (hit5[wid] + prior_n * base5) / (ap + prior_n)
        rd = (dd[wid] + prior_n * based) / (ap + prior_n)
        sw = np.log1p(sol) * np.minimum(ap, 10)
        tot = sw.sum()
        known = ap >= 2
        elite = (ap >= 4) & (hit5[wid] / np.maximum(ap, 1) >= 0.25)
        rugger = (ap >= 4) & (dd[wid] / np.maximum(ap, 1) >= 0.9)
        out[i] = [known.sum(), r3.max(), (r3 * sw).sum() / tot if tot > 0 else base3,
                  r5.max(), (r5 * sw).sum() / tot if tot > 0 else base5,
                  np.sort(r5)[-3:].mean(), (rd * sw).sum() / tot if tot > 0 else based,
                  elite.sum(), sol[elite].sum() / max(sol.sum(), 1e-9),
                  sol[rugger].sum() / max(sol.sum(), 1e-9), np.log1p(ap).mean()]
    R = pd.DataFrame(out, columns=[f'{prefix}_{c}' for c in cols]); R['mint'] = mints
    return R


t0 = time.time()
REP_A = reputation(EDGE_A, 'wa')
REP_C = reputation(EDGE_C, 'wc')
del EDGE_A, EDGE_C; gc.collect()

# creator history: earlier migrations of the same creator, and their resolved outcomes
crt = pd.Series(mints).map(CREATOR).fillna('?').values
cr_n = np.zeros(n); cr_res = np.zeros(n); cr_h3 = np.full(n, np.nan); cr_lmx = np.full(n, np.nan)
hist = {}
for i in range(n):
    lst = hist.setdefault(crt[i], [])
    if crt[i] != '?' and lst:
        prev = np.array(lst)
        cr_n[i] = len(prev)
        res = prev[(mts[prev] < cut[i]) & labelled[prev]]
        cr_res[i] = len(res)
        if len(res):
            cr_h3[i] = h3[res].mean(); cr_lmx[i] = logmx[res].mean()
    lst.append(i)
CR = pd.DataFrame({'mint': mints, 'cr_prev_migr': cr_n, 'cr_prev_res': cr_res,
                   'cr_h3': cr_h3, 'cr_lmx': cr_lmx})
print(f'history features done ({time.time()-t0:.0f}s)')

# %% [markdown]
# ## Feature table

# %%
D = (T.merge(TAPE, on='mint', how='left').merge(M, on='mint', how='left')
      .merge(REG, on='mint', how='left').merge(REP_A, on='mint', how='left')
      .merge(REP_C, on='mint', how='left').merge(CR, on='mint', how='left'))
D['age_s'] = D.mt - D.created_ts
D['log_age'] = np.log1p(D.age_s.clip(lower=0))
D = D.sort_values('mt', kind='stable').reset_index(drop=True)
DROP = {'mint', 'mt', 'day', 'is_test', 'mx', 'fx', 'created_ts', 'age_s', 'dow'}
FEATS = [c for c in D.columns if c not in DROP and pd.api.types.is_numeric_dtype(D[c])]
D[FEATS] = D[FEATS].astype(np.float32).replace([np.inf, -np.inf], np.nan)
LD = D[D.is_test == 0].reset_index(drop=True)
TD = D[D.is_test == 1].reset_index(drop=True)
print(f'{len(FEATS)} features | labelled {len(LD)} | test {len(TD)} | {time.time()-T_START:.0f}s')
# runtime guard: the bot kills runs at 60 min (score 0). Cut ensemble size if features were slow.
_el = time.time() - T_START
if _el > 25 * 60: SEEDS = [0]
elif _el > 15 * 60: SEEDS = [0, 1]
print('seeds:', SEEDS)

# %% [markdown]
# ## Level models, calibration, and the EV policy

# %%
LGB = dict(n_estimators=450, learning_rate=0.03, num_leaves=15, min_child_samples=60,
           subsample=0.8, subsample_freq=1, colsample_bytree=0.6, reg_lambda=5.0,
           min_split_gain=0.0, verbose=-1, n_jobs=N_JOBS)


def weights(df, ref_mt):
    age_days = (ref_mt - df.mt.values) / 86400.0
    return 0.5 ** (age_days / HALF_LIFE_DAYS)


def fit_predict(trn, targets, ref_mt, seeds=SEEDS):
    X = trn[FEATS].values; w = weights(trn, ref_mt)
    mx_ = trn.mx.values
    def predict(val):
        Xv = val[FEATS].values
        P = np.zeros((len(val), len(LEVELS)))
        for k, L in enumerate(LEVELS):
            y = (mx_ >= L).astype(int)
            if y.sum() < 15:
                P[:, k] = y.mean(); continue
            P[:, k] = np.mean([lgb.LGBMClassifier(random_state=s, **LGB).fit(X, y, sample_weight=w)
                               .predict_proba(Xv)[:, 1] for s in seeds], axis=0)
        return P
    return predict


def logit(p):
    p = np.clip(p, 1e-5, 1 - 1e-5); return np.log(p / (1 - p))


class Policy:
    """Fit on labelled rows `trn` (all resolved before the day being decided)."""

    def __init__(self, trn, seeds=SEEDS):
        days = sorted(trn.day.unique())
        hold_start_day = days[-HOLD_DAYS] if len(days) > HOLD_DAYS + 7 else days[len(days) // 2]
        cal = trn[trn.day >= hold_start_day]
        old = trn[trn.mt <= cal.mt.min() - WIN - EMBARGO]
        Pc = fit_predict(old, LEVELS, cal.mt.min(), seeds)(cal)
        self.platt = []
        mxc, fxc = cal.mx.values, cal.fx.values
        for k, L in enumerate(LEVELS):
            y = (mxc >= L).astype(int)
            if y.sum() >= 5 and y.sum() < len(y) - 5:
                lr = LogisticRegression(C=1.0).fit(logit(Pc[:, [k]]), y)
                self.platt.append((float(lr.coef_[0, 0]), float(lr.intercept_[0])))
            else:
                self.platt.append((1.0, 0.0))
        # expected held payoff when level is missed, among tokens the model likes
        Pcal = self.calibrate(Pc)
        held = np.maximum(fxc - 1 - COST, -1.0)
        glob_miss = held.mean()
        self.miss = []
        for k, L in enumerate(LEVELS):
            top = Pcal[:, k] >= np.quantile(Pcal[:, k], 0.9)
            m = top & (mxc < L)
            nm = m.sum()
            est = (held[m].sum() + 20 * glob_miss) / (nm + 20)
            self.miss.append(min(est, -0.5))       # never assume a missed level is cheap
        self.model = fit_predict(trn, LEVELS, trn.mt.max(), seeds)
        # token-specific payoff when the level is missed: regression on the held payoff of tokens
        # that did not reach 3x, used as a shrunk offset around the per-level constants
        self.miss_reg = None
        if USE_MISS_MODEL:
            m3 = trn.mx.values < LEVELS[0]
            y = np.clip(np.maximum(trn.fx.values[m3] - 1 - COST, -1.0), -1.0, LEVELS[0] - 1 - COST)
            Xm = trn[FEATS].values[m3]
            self.miss_reg = lgb.LGBMRegressor(random_state=0, **{**LGB, 'n_estimators': 300}).fit(
                Xm, y, sample_weight=weights(trn[m3], trn.mt.max()))
            self.miss_center = float(np.average(y, weights=weights(trn[m3], trn.mt.max())))

    def calibrate(self, P):
        out = np.column_stack([1 / (1 + np.exp(-(a * logit(P[:, k]) + b)))
                               for k, (a, b) in enumerate(self.platt)])
        return np.minimum.accumulate(out, axis=1)            # P(reach L) is non-increasing in L

    def miss_matrix(self, val):
        Mv = np.tile(np.array(self.miss), (len(val), 1))
        if self.miss_reg is not None:
            off = self.miss_reg.predict(val[FEATS].values) - self.miss_center
            Mv = Mv + MISS_SHRINK * off[:, None]
        return np.minimum(Mv, -0.3)

    def ev(self, P, val=None):
        Lv = np.array(LEVELS)
        Mv = np.array(self.miss)[None, :] if val is None else self.miss_matrix(val)
        return P * (Lv - 1 - COST) + (1 - P) * Mv

    def decide(self, val, margin=MARGIN):
        P = self.calibrate(self.model(val))
        EV = self.ev(P, val)
        k = EV.argmax(1)
        best = EV[np.arange(len(val)), k]
        tp = np.where(best > margin, np.array(LEVELS)[k], 0.0)
        return tp, best, P

# %% [markdown]
# ## Optional: embargoed walk-forward (set PD_VALIDATE=1)

# %%
if RUN_VALIDATION:
    days = sorted(LD.day.unique())
    rows = []
    for day in days[-VAL_DAYS:]:
        val = LD[LD.day == day]
        trn = LD[LD.mt <= val.mt.min() - WIN - EMBARGO]
        if trn.day.nunique() < 14 or len(val) < 30: continue
        pol = Policy(trn, seeds=SEEDS[:1])
        P = pol.calibrate(pol.model(val)); EV = pol.ev(P, val)
        k = EV.argmax(1); best = EV[np.arange(len(val)), k]
        k5 = LEVELS.index(5.0)
        for mg in (0.0, 0.2, 0.35, 0.5, 0.8, 1.2):
            tp = np.where(best > mg, np.array(LEVELS)[k], 0.0)
            tp5 = np.where(EV[:, k5] > mg, 5.0, 0.0)
            rows.append(dict(day=day, margin=mg, n=int((tp > 0).sum()),
                             pnl=float(pnl(tp, val.mx.values, val.fx.values).sum()),
                             n5=int((tp5 > 0).sum()),
                             pnl_tp5=float(pnl(tp5, val.mx.values, val.fx.values).sum())))
        print(day, {r['margin']: round(r['pnl'], 1) for r in rows if r['day'] == day},
              f'({time.time()-T_START:.0f}s)', flush=True)
    V = pd.DataFrame(rows)
    S = V.groupby('margin').agg(days=('day', 'nunique'), buys_day=('n', 'mean'), pnl=('pnl', 'sum'),
                                green=('pnl', lambda s: int((s > 0).sum())),
                                buys5_day=('n5', 'mean'), pnl_tp5=('pnl_tp5', 'sum'))
    print(S.round(2))

# %% [markdown]
# ## Submission

# %%
pol = Policy(LD)
tp, best, P = pol.decide(TD)
sub = pd.DataFrame({'mint': TD.mint.values, 'tp': tp})
sub = test[['mint']].merge(sub, on='mint', how='left').fillna({'tp': 0.0})
sub['tp'] = np.where(sub.tp > 0, sub.tp.clip(3, 100), 0.0)
sub.to_csv('submission.csv', index=False)
print('miss payoffs:', np.round(pol.miss, 3))
print(f'submission.csv: {len(sub)} rows, buying {int((sub.tp > 0).sum())}',
      sub.tp[sub.tp > 0].value_counts().sort_index().to_dict(), f'| total {time.time()-T_START:.0f}s')
