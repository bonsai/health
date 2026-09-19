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
