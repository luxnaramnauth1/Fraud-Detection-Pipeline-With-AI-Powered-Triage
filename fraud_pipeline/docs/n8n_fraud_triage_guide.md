# Fraud Alert Triage & Enrichment Agent (n8n + AI)

An AI agent, built in n8n, that picks up flagged transactions from the
fraud-detection ETL pipeline, enriches them with a plain-language risk
summary using an LLM, and routes them to the right Slack channel based on
severity — with a human analyst always making the final call.

This workflow was built and validated in this project: the JSON file
(`fraud_triage_agent.json`) was successfully imported into a real n8n
instance and round-tripped without errors, so it is a genuinely importable,
structurally valid workflow — not just a diagram.

## How it connects to your existing fraud pipeline

This agent is designed to sit **downstream** of the `flagged_transactions`
dbt model from the ETL fraud pipeline project. The story for your CV/interview:

> "I built a data pipeline that flags suspicious transactions using SQL
> rules, then built an AI agent on top of it that enriches each flag with
> a human-readable risk summary and routes it to the right review queue —
> so the output of the data pipeline becomes something a fraud analyst can
> act on immediately, not just a row in a table."

## Workflow Steps (as built in `fraud_triage_agent.json`)

1. **Schedule Trigger** — runs every 15 minutes (simulates near-real-time monitoring)
2. **Fetch New Flagged Transactions** — queries `flagged_transactions` for
   rows where `is_flagged = true AND reviewed = false`
3. **Split Into Batches** — processes one transaction at a time (keeps AI
   calls simple and traceable, avoids hitting token/rate limits)
4. **AI Enrichment** — calls an LLM API with the transaction's details and
   asks it to: explain *why* it was flagged, assign a risk level, and
   recommend a next action
5. **Extract AI Response** — pulls the model's text output into clean fields
6. **High Risk? (IF node)** — routes based on `flag_count`:
   - 2+ rules triggered → urgent Slack channel
   - 1 rule triggered → standard review queue
7. **Notify Slack** — posts the enriched alert with the AI's risk summary
8. **Mark as Reviewed** — updates the record so it isn't re-processed and
   re-alerted on the next run

**Note on human-in-the-loop:** this workflow deliberately does **not**
auto-block cards or auto-close accounts. It enriches and routes for human
review — this is intentional and worth mentioning explicitly in an
interview, since banks are very sensitive to AI systems taking autonomous
action on financial decisions without a human checkpoint.

## AI Tools You Can Use (and how to plug them in)

The workflow as built uses the **Anthropic API (Claude)** via the generic
HTTP Request node, but here are your realistic options:

| Tool | How to connect in n8n | Notes |
|---|---|---|
| **Anthropic Claude API** | HTTP Request node → `https://api.anthropic.com/v1/messages` (used in this workflow) | Good reasoning quality for writing analyst-style risk summaries |
| **OpenAI (GPT-4o / GPT-4o-mini)** | Native `OpenAI` node in n8n, or HTTP Request → `https://api.openai.com/v1/chat/completions` | n8n has a built-in node, slightly less setup than the generic HTTP approach |
| **n8n's built-in AI Agent node** (`@n8n/n8n-nodes-langchain.agent`) | Drag in the "AI Agent" node from n8n's native AI category | Lets the AI call other n8n nodes as "tools" (e.g., look up customer history) — more advanced, worth mentioning as a stretch goal |
| **Local/open-source LLM (Ollama)** | HTTP Request node → local Ollama server | Useful to mention if you want to show you understand on-premise/data-residency constraints, which matter a lot for banks |

For your CV/portfolio, using the **native AI Agent node with tool-calling**
(rather than a single HTTP call) is the more advanced/impressive version —
it can be scoped as a "next step" if you want to extend this further.

## How to Import and Run This Yourself

```bash
# 1. Install n8n
npm install -g n8n

# 2. Start n8n
n8n start
# Editor opens at http://localhost:5678

# 3. In the n8n editor: Menu (top-right) -> Import from File -> select fraud_triage_agent.json
```

To actually run it end-to-end, you'll need to:
1. Add a **Postgres credential** in n8n pointing at wherever `flagged_transactions`
   lives (see the fraud pipeline project's note on migrating from DuckDB to Postgres)
2. Add an **HTTP Header Auth credential** with your Anthropic (or OpenAI) API key
3. Add a **Slack credential** (OAuth) and update the channel names to real ones in your workspace
4. Add a `reviewed` boolean and `ai_risk_summary` text column to your `flagged_transactions` table

## Suggested CV Bullet

> *Built an AI-powered fraud alert triage agent in n8n that enriches
> SQL-flagged transactions with LLM-generated risk summaries and routes
> them to severity-based Slack channels for human review, reducing analyst
> time spent manually interpreting raw flagged records.*
