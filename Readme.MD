# End of Day Reflection Agent

A short daily reflection tool — takes about 5 minutes. Asks you a few honest questions about your day, branches based on your answers, and closes with a summary of how you showed up.

No AI at runtime. Same answers always give the same path. That's the point.

---

## What's in here

```
reflection-tree.json   ← all the questions, branches, and routing
agent.html             ← open this in a browser to run it
agent.py               ← or run this in your terminal
write-up.md            ← design rationale
```

---

## Running it

### Browser (easiest)
Put `agent.html` and `reflection-tree.json` in the same folder. Open `agent.html` in any browser. That's it.

If you see a CORS error, run this instead:
```bash
python -m http.server 8000
```
Then go to `http://localhost:8000/agent.html`

### Terminal
```bash
python agent.py
```
Needs Python 3.8+. No installs required.

---

## How it works

The whole conversation lives in `reflection-tree.json` — a flat list of nodes. The agent reads the file, walks you through it one node at a time, and branches based on what you pick.

Three node types you'll interact with:
- **question** — shows options, waits for your pick
- **reflection** — shows an insight based on your path, you click continue
- **summary** — at the end, pulls together what your answers signal across all three axes

Everything else (decision, bridge, start, end) happens automatically in the background.

### How branching works

Every question feeds into a decision node that routes you based on what you picked:

```json
{ "match": ["Productive", "Mixed"], "goto": "A1_Q1_HIGH" }
{ "match": ["Tough", "Frustrating"], "goto": "A1_Q1_LOW" }
```

No randomness. No AI. Just a lookup.

### How the summary works

As you answer, each node quietly tallies a signal — `axis1:internal`, `axis2:contribution`, `axis3:other` etc. At the end, the summary counts those tallies and picks the right closing line for each axis. You never see the tallies, just the result.

---

## The three axes

The conversation moves through three questions in sequence:

| | What it's asking | Spectrum |
|---|---|---|
| Axis 1 | How did you handle things today? | Victim ↔ Victor |
| Axis 2 | What did you give today? | Entitlement ↔ Contribution |
| Axis 3 | Who were you thinking about? | Self ↔ Others |

Each axis builds on the previous one. By the time you reach Axis 3 you've already thought about your agency and your contribution — so the radius question lands differently than if you'd asked it cold.

---

## Changing the questions

Everything is in `reflection-tree.json`. You can edit any `text` or `options` field directly — no code changes needed. The agent loads whatever is in the file.

If you add a new question node, you need four things:
1. A unique `id`
2. A `parentId` pointing to its parent
3. `type: "question"` with your options listed
4. A `decision` node after it with routing rules pointing to the next destinations

The engine handles the rest.