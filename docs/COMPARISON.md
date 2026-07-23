# bounded vs. platform agent frameworks

`bounded` gets compared to full agent platforms like
[OpenClaw](https://github.com/orgs/openclaw/repositories) and
[Hermes Agent](https://github.com/nousresearch/hermes-agent) often enough
that it's worth writing down plainly: they solve a different problem, and
neither comparison makes the other worse.

## What they actually are

OpenClaw and Hermes Agent are **self-hosted personal-assistant platforms**.
You install them, they run as their own long-lived service, and they come
with a gateway to Telegram/Discord/WhatsApp/Slack/Signal/email, a scheduler
(OpenClaw's "heartbeat" wakes the agent unprompted; Hermes ships a built-in
cron), a skill marketplace (ClawHub / Skills Hub), persistent memory with
search, and (Hermes) a "closed learning loop" that writes and refines its
own skills from experience. Both are mature, widely used, and have had real
scrutiny — OpenClaw in particular has been the subject of multiple
published security/privacy analyses.

`bounded` is a **Python library with no runtime of its own**. There's no
service to deploy, no gateway, no scheduler, no skill registry. You `import
bounded` into an application that already exists and already does the
boring 90% (its own Telegram bot, its own device control, its own polling
loop) and get the primitives for the remaining 10%: a typed capability, an
LLM tool-calling loop, a context-pack builder, a provenance-ranked memory
store.

## Side by side

| | `bounded` | OpenClaw | Hermes Agent |
|---|---|---|---|
| What it is | Library (~1,180 LOC, 26 files in `src/bounded/`) | Self-hosted service | Self-hosted service |
| Runtime | None — runs inside your process | Its own Node.js process + gateway | Its own process + gateway |
| Messaging | None — bring your own | Built in: Telegram, Discord, WhatsApp, iMessage | Built in: Telegram, Discord, Slack, WhatsApp, Signal, email |
| Scheduling / proactivity | None — your app's existing scheduler calls it | Built-in "heartbeat" (agent wakes itself, unprompted) | Built-in cron scheduler |
| Tools / skills | Plain typed Python functions (`Capability`) | `AgentSkill` system + ClawHub registry | Skills Hub, `agentskills.io`-compatible |
| Memory | File-backed, provenance-ranked (`JsonlMemoryStore`, ~130 LOC) | Version-controlled local Markdown | SQLite FTS5 + LLM summarization |
| Autonomy model | Bounded — code-level `guard` before every tool call, schema-checked judge output, hard step limit | Autonomous — unprompted wake, subagent spawning | Autonomous — self-modifying skills |
| Runtime dependencies | pydantic, `openai` and `gspread` (both optional at import time), `tenacity`, `structlog` | Full Node.js/npm ecosystem | Python + subagent orchestration stack |
| License | Apache-2.0 | "Other" (custom — read the actual terms before depending on it) | MIT |
| Maturity | New; 100 tests, not yet run against a live LLM in this environment | Hundreds of thousands of stars; published security review | Backed by Nous Research; community skill directories |

## When each one is the right call

Reach for OpenClaw or Hermes Agent when the goal genuinely is "I want a
general-purpose autonomous assistant across many messaging platforms with a
skill marketplace" — that's real, hard infrastructure, already built and
hardened, and re-implementing a meaningful fraction of it yourself would be
a bad trade of your time.

Reach for `bounded` when the goal is "I have an application already — it
has its own bot, its own scheduler, its own control plane — and I want to
add one scoped, auditable, LLM-driven feature to it without adopting a
second platform." Bolting a full autonomous agent platform onto an app that
already has its own event loop and its own Telegram bot means either
running two competing services or rebuilding your existing structure inside
someone else's skill-system assumptions. Neither is worth it for a feature
that's a few hundred lines against primitives you already understand
completely.

The autonomy difference is also a genuine design choice, not just a
maturity gap: OpenClaw's heartbeat and Hermes's self-modifying skills are
*supposed* to act with less supervision — that's the product. `bounded`
goes the other way on purpose (see [`DESIGN.md`](DESIGN.md)): every LLM
decision point is bounded by code that runs before and after it. That's the
right tradeoff when the feature touches something with real-world
consequences (a physical device, a message sent on your behalf) and the
wrong one when the goal is a maximally autonomous life-assistant.
