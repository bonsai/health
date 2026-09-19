#!/usr/bin/env python3
"""Takt-style cross-repository health observer.

Health is intentionally binary:
  error_count == 0 -> healthy
  error_count > 0  -> unhealthy
  observation failure -> unknown
"""
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPE = json.loads((ROOT / "health-scope.json").read_text())
OWNER = SCOPE["owner"]
EXCLUDE = set(SCOPE.get("exclude", []))
LIMIT = int(SCOPE.get("workflow_limit_per_repository", 20))


def gh_api(path: str):
    p = subprocess.run(
        ["gh", "api", path],
        text=True, capture_output=True, check=True
    )
    return json.loads(p.stdout)


def main():
    try:
        repos = []
        for page in gh_api(f"/users/{OWNER}/repos?per_page=100&type=owner"):
            repos.extend(page if isinstance(page, list) else [])

        errors = []
        observed_repositories = []
        for repo in repos:
            name = repo["name"]
            if name in EXCLUDE or repo.get("archived"):
                continue
            observed_repositories.append(name)
            try:
                runs = gh_api(
                    f"/repos/{OWNER}/{name}/actions/runs"
                    f"?per_page={LIMIT}&exclude_pull_requests=true"
                )
                for run in runs.get("workflow_runs", []):
                    if run.get("conclusion") == "failure":
                        errors.append({
                            "repository": f"{OWNER}/{name}",
                            "run_id": run["id"],
                            "workflow": run.get("name"),
                            "workflow_id": run.get("workflow_id"),
                            "branch": run.get("head_branch"),
                            "sha": run.get("head_sha"),
                            "url": run.get("html_url"),
                            "created_at": run.get("created_at"),
                            "updated_at": run.get("updated_at"),
                        })
            except Exception as exc:
                raise RuntimeError(f"failed to observe {OWNER}/{name}: {exc}") from exc

        state = {
            "health": "unhealthy" if errors else "healthy",
            "error_count": len(errors),
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "source": "github_actions",
            "scope": OWNER,
            "repositories_checked": len(observed_repositories),
            "repositories": observed_repositories,
            "errors": errors,
        }
    except Exception as exc:
        state = {
            "health": "unknown",
            "error_count": 0,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "source": "github_actions",
            "scope": OWNER,
            "repositories_checked": 0,
            "repositories": [],
            "errors": [],
            "observation_error": str(exc),
        }

    path = ROOT / "health.json"
    previous = json.loads(path.read_text()) if path.exists() else None

    # Takt: persist a new state only when the observable health state changes.
    comparable = lambda x: (
        x.get("health"),
        x.get("error_count"),
        [(e.get("repository"), e.get("run_id")) for e in x.get("errors", [])],
        x.get("observation_error"),
    )
    if previous is None or comparable(previous) != comparable(state):
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"changed": True, **state}, ensure_ascii=False))
    else:
        print(json.dumps({"changed": False, **state}, ensure_ascii=False))


if __name__ == "__main__":
    main()
