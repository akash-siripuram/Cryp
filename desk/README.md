# DEV WATCH — paper desk, $100 bankroll

Not financial advice. Paper only (`PAPER = True`); never holds a key, never signs.

$100 bankroll, $25 flat tickets, max 4 open. Paper fills pay 3% slippage each way.
Daily halt at -$50 realized. A buy is refused if free cash < $25.

## Setup
```bash
cd desk && pip install -r requirements.txt
read -rs -p "xai key: " K && printf 'XAI_API_KEY=%s\n' "$K" > .env && unset K && echo
read -rs -p "rpc url (enter = public): " R && echo
printf 'RPC_URL=%s\n' "${R:-https://api.mainnet-beta.solana.com}" >> .env && unset R
chmod 600 .env
```

## Run
```bash
python enter.py <mint>                    # check + paper buy one token
python scan.py                            # every 2h: Grok finds leads on X
python watch.py --minutes 9 --every 20    # every 10 min: guards positions
python pulse.py                           # every 60 min: X attention read
python report.py                          # evening: P&L, Grok bill, free cash
```
Or loop everything: `./run.sh`
