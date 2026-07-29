# Demo Video Script — Fraud Detection Pipeline

A narration script for a screen-recorded demo (Loom, OBS, QuickTime, etc.).
Every command and every number below was actually run and captured during
this project — read the lines in **"Say"** while the terminal runs the
command in **"Do"**. Total runtime: roughly 3-4 minutes.

**Setup before recording:** open a terminal in the `fraud_pipeline/` folder,
and have this script open on a second screen/window to read from.

---

## Scene 1 — Intro (10-15 sec, face-to-camera or voiceover over the README)

**Say:**
> "Hi, I'm [Your Name]. This is a fraud detection pipeline I built for
> banking use cases — it simulates transaction data, flags suspicious
> activity using SQL rules in dbt, and uses an AI agent in n8n to
> enrich and route alerts to a fraud analyst. Let me walk through it."

**Do:** Show the project folder structure or the README.md in an editor.

---

## Scene 2 — Generate transaction data (20-30 sec)

**Say:**
> "First, I simulate realistic bank transactions — 5,000 of them, across
> 200 customers — with a small percentage of deliberately suspicious
> patterns built in: unusually large amounts, transactions from foreign
> locations, and rapid repeat transactions, which mimic a stolen card
> being used quickly."

**Do:** Run this command:
```bash
cd scripts
python generate_transactions.py --n_customers 200 --n_transactions 5000 --fraud_rate 0.02
```

**Real output you'll see:**
```
Generated 5057 transactions for 200 customers.
  - Ground-truth simulated fraud rate: 3.10%
Saved transactions to: ../data/transactions.csv
Saved customer profiles to: ../data/customers.csv
```

**Say:**
> "That gives us just over five thousand transactions, with about 3%
> flagged as fraud in the ground truth — which we only use later to
> check how well our detection actually works."

---

## Scene 3 — Load into the database (15-20 sec)

**Say:**
> "Next, I load this raw data into the warehouse — I'm using DuckDB here
> so this demo runs with zero setup, but the exact same SQL works against
> PostgreSQL or Snowflake in production."

**Do:** Run:
```bash
python load_to_db.py
```

**Real output:**
```
Loaded 5057 rows into raw.transactions
Loaded 200 rows into raw.customers

Database ready at: ../dbt_project/fraud_pipeline.duckdb
```

---

## Scene 4 — Transform with dbt (30-40 sec)

**Say:**
> "Now the interesting part — dbt transforms this raw data through a
> staging layer, then computes each customer's own historical spending
> baseline, checks for rapid repeat transactions, and finally applies
> three fraud-flagging rules: unusually high amount, unusual location,
> and rapid repeats."

**Do:** Run:
```bash
cd ../dbt_project
dbt run
```

**Real output:**
```
Found 5 models, 14 data tests, 486 macros

1 of 5 OK created sql view model main.stg_customers ............ [OK in 0.15s]
2 of 5 OK created sql view model main.stg_transactions ........... [OK in 0.14s]
3 of 5 OK created sql view model main.int_customer_transaction_stats [OK in 0.06s]
4 of 5 OK created sql view model main.int_transaction_velocity ... [OK in 0.06s]
5 of 5 OK created sql table model main.flagged_transactions ...... [OK in 0.13s]

Completed successfully
Done. PASS=5 WARN=0 ERROR=0 SKIP=0 NO-OP=0 REUSED=0 TOTAL=5
```

**Say:**
> "All five models built successfully. Now let's make sure the data
> quality is solid — this matters a lot in banking, where auditors need
> to trust the pipeline."

**Do:** Run:
```bash
dbt test
```

**Real output:**
```
Finished running 14 data tests in 0 hours 0 minutes and 0.39 seconds

Completed successfully
Done. PASS=14 WARN=0 ERROR=0 SKIP=0 NO-OP=0 REUSED=0 TOTAL=14
```

**Say:**
> "All fourteen tests pass — uniqueness and not-null checks across every
> table in the pipeline."

---

## Scene 5 — Show the actual results (30-40 sec)

**Say:**
> "So how good is the detection? Let's check it against the ground truth
> I generated earlier."

**Do:** Run this Python snippet (or open it as a small script):
```python
import duckdb
con = duckdb.connect('fraud_pipeline.duckdb')

total = con.execute('SELECT COUNT(*) FROM main.flagged_transactions').fetchone()[0]
flagged = con.execute('SELECT COUNT(*) FROM main.flagged_transactions WHERE is_flagged').fetchone()[0]
true_fraud = con.execute('SELECT COUNT(*) FROM main.flagged_transactions WHERE is_simulated_fraud=1').fetchone()[0]
caught = con.execute('SELECT COUNT(*) FROM main.flagged_transactions WHERE is_flagged AND is_simulated_fraud=1').fetchone()[0]

print(f'Total transactions: {total}')
print(f'Total flagged: {flagged} ({flagged/total:.1%})')
print(f'Recall: {caught}/{true_fraud} = {caught/true_fraud:.1%}')
print(f'Precision: {caught}/{flagged} = {caught/flagged:.1%}')
```

**Real output:**
```
Total transactions: 5057
Total flagged: 138 (2.7%)
Recall: 110/157 = 70.1%
Precision: 110/138 = 79.7%
```

**Say:**
> "So with pure SQL rules — no machine learning yet — we're catching 70%
> of the actual fraud, and when we do flag something, we're right about
> 80% of the time. That's a solid, fully explainable starting point,
> which matters a lot for compliance teams who need to understand exactly
> why something was flagged."

**Optional — show a real flagged example:**
```
transaction_id: 66977a60-78ca-4ce7-8caf-0c83d53f4f71
customer_id: CUST00064
amount: 4729.84
location: Lagos
home_city: Grand Baie
flag_count: 2  (high amount + unusual location)
```

**Say:**
> "Here's a real example — this customer's home city is Grand Baie, but
> the transaction happened in Lagos, and the amount is well above their
> normal spending. Two rules triggered, so this gets prioritized."

---

## Scene 6 — The AI agent layer (30-40 sec)

**Say:**
> "But a flagged row in a table isn't useful to a fraud analyst on its
> own. So I built an AI agent in n8n that picks up these flagged
> transactions, sends them to Claude to generate a plain-language risk
> summary, and routes them to Slack — high-risk ones to an urgent
> channel, lower-risk ones to a standard review queue."

**Do:** Show the n8n workflow canvas (import `n8n/fraud_triage_agent.json`
and open it in the n8n editor beforehand so it's ready to display).

**Say:**
> "Every step here is designed with a human in the loop — the AI never
> blocks a card or closes an account on its own. It enriches the alert
> and hands it to a person to make the final call, which is exactly the
> kind of judgment banks expect from an AI system handling financial
> decisions."

---

## Scene 7 — Wrap-up (10-15 sec)

**Say:**
> "So that's the full pipeline — from simulated data, through SQL-based
> fraud detection with dbt, to an AI agent that makes the output
> actionable for a human analyst. All the code is on my GitHub, linked
> below. Thanks for watching."

**Do:** Show the GitHub repo URL or README on screen.

---

## Recording Tips

- Record in 1080p, screen + narration (no need to show your face unless you want to)
- Keep total video length under 4 minutes — recruiters skim
- Use a tool like **Loom** (easiest, auto-generates a shareable link) or
  **OBS Studio** (free, more control, saves a local MP4 directly)
- Zoom your terminal font to at least 16-18pt before recording — small
  text is unreadable in a shared video
- Do one practice run without recording first so the commands don't error
  live (they shouldn't — every command above was verified working)
- Export as MP4 and upload to your LinkedIn/GitHub README (embed as a link
  or GIF preview, since GitHub READMEs don't play MP4 directly — use a
  short GIF or link to a hosted video)
