# health.aw.md

# Takt: Health Recovery Loop

## Purpose

`health` observes whether the Bonsai system is healthy.

The invariant is:

```text
error_count = 0  -> healthy
error_count > 0  -> unhealthy
observation failure -> unknown
```

Health does not diagnose root causes. Diagnosis belongs to `bonsai/wf-errors`.

---

## Takt

Execute the following cycle repeatedly:

```text
OBSERVE
  ↓
DETECT
  ↓
JUDGE
  ↓
ACT
  ↓
VERIFY
  ↓
RECORD
  ↺
```

### OBSERVE

Collect recent GitHub Actions workflow runs and checks for the configured repository scope.

Output:

```json
{
  "observed_at": "...",
  "repositories": [],
  "runs": []
}
```

### DETECT

Convert failed required workflow runs into normalized health errors.

An observation is an error when the relevant GitHub status/conclusion is failure.

Do not infer an error from elapsed time alone.

### JUDGE

Apply only the binary health rule:

```text
errors == 0 → healthy
errors > 0  → unhealthy
cannot observe → unknown
```

Never hide an error in order to report healthy.

### ACT

If unhealthy:

1. identify the affected repository/run;
2. create or reuse a `wf-errors` error event;
3. request the appropriate action;
4. preserve the original evidence.

Possible actions:

```text
rerun
issue
fix
prevention
```

Actions must be idempotent.

### VERIFY

After an action, observe the affected run again.

```text
failure remains → unhealthy
failure disappears → recovered
cannot observe → unknown
```

Recovery is not assumed from a successful API request. It is verified by a new observation.

### RECORD

Write the current state to `health.json`.

Minimum state:

```yaml
health: healthy | unhealthy | unknown
error_count: integer
checked_at: ISO-8601
source: github_actions
repositories: []
errors: []
last_action: null
verification: null
```

---

## Separation of concerns

```text
health
  = Is it broken?

wf-errors
  = What broke?
  = Why?
  = What should we do?

GitHub Actions
  = Execute

aw
  = Orchestrate the loop
```

---

## Takt rule

One cycle should produce one observable state transition.

Do not accumulate hidden state.

```history → latest → now → action → latest
```

The next cycle verifies the previous action.

---

## Failure safety

If any collection step fails:

```unknown
```

Never:

```collection failure → healthy
```

If an action fails, retain the original error and record the failed action.

If diagnosis is uncertain, stop at evidence/issue creation rather than inventing a root cause.

---

## Done

The implementation is complete when:

- every configured repository can be observed;
- one or more errors always produces `unhealthy`;
- collection failure produces `unknown`;
- unhealthy state can enter `wf-errors`;
- actions are followed by verification;
- the result is persisted;
- repeated Takt cycles are idempotent.


# Ecosystem Takt: Team Building

## Team

```text
github-observatory = EYES
sync-repos        = HANDS
latest            = SENSOR BUFFER
now               = MEMORY / CURRENT VIEW
health            = HEARTBEAT
wf-errors         = DEBUGGER
JEV               = JUDGE
AW                = CONDUCTOR
GitHub            = CANON
```

Each member has one job. The team communicates through observations and explicit state.

## Shared movement

```text
                 ┌─────────────────────┐
                 │ github-observatory   │
                 │       OBSERVE        │
                 └──────────┬──────────┘
                            ↓
                       Observation
                            ↓
                    ┌──── latest ────┐
                    ↓                 ↓
                  now              health
                    ↓                 ↓
              CURRENT STATE       HEALTH
                    └──────┬─────────┘
                           ↓
                       wf-errors
                           ↓
                     diagnosis/action
                           ↓
                          AW
                           ↓
                         JEV
                           ↓
                         ACTION
                           ↓
                    GitHub / system
                           ↓
                       OBSERVE ↺
```

## Team-building rule

Do not ask one agent to do the whole job.

Instead:

```text
EYES see
HANDS change
MEMORY remembers
HEARTBEAT detects
DEBUGGER explains
JUDGE chooses
CONDUCTOR coordinates
```

## Data contract

The smallest shared unit is `ObservationRecord`.

```yaml
id: unique observation id
source: producer
subject: observed entity
kind: observation kind
observed_at: timestamp
status: observed status
repository: optional repository
url: optional source URL
payload: observed facts
evidence_ref: optional evidence pointer
```

The producer records facts. Consumers may derive views, but must retain the source observation.

## Cross-repository Takt

### T0 — Observe
`github-observatory` and `sync-repos` produce observations.

### T1 — Latest
The newest observations become `latest`.

### T2 — Now
`now` integrates the newest observations into the current view.

### T3 — Health
`health` reduces the relevant observations:

```text
no error → healthy
one or more errors → unhealthy
cannot observe → unknown
```

### T4 — Diagnose
Only when unhealthy, `wf-errors` receives the failed workflow evidence.

### T5 — Judge
JEV chooses the next valid action from verified evidence.

### T6 — Act
AW executes the selected action.

### T7 — Verify
The team observes the affected entity again.

### T8 — Record
The new observation becomes `latest`, and `now` reflects the new state.

Then the next Takt begins.

## Team boundary

```text
github-observatory → facts
sync-repos        → synchronization facts
latest            → newest facts
now               → current view
health            → health predicate
wf-errors         → failure intelligence
JEV               → decision
AW                → execution
GitHub            → canonical state
```

No role silently absorbs another role.

## First vertical slice

The first useful end-to-end team test is:

```text
GitHub workflow fails
 → github-observatory observes it
 → latest receives it
 → now displays it
 → health = unhealthy
 → wf-errors builds evidence/diagnosis
 → JEV selects a permitted action
 → AW executes it
 → GitHub produces a new run
 → github-observatory observes the result
 → now shows recovered/unrecovered state
```

That is the smallest complete team.

## Takt invariant

An action without a later observation is incomplete.

A diagnosis without evidence is incomplete.

A health state without an observation timestamp is incomplete.

A current state without a source observation is incomplete.
