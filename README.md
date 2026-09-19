# health

GitHub / Bonsai ecosystem の **健康状態を判定するための最小状態モデル**。

## Definition

健康かどうかは複雑なスコアにしない。

- `healthy`: 対象範囲にエラーがない
- `unhealthy`: 対象範囲にエラーが1件以上ある
- `unknown`: 状態を取得できない

つまり、`error_count > 0 => unhealthy`。

## What counts as an error

主に GitHub Actions を対象にする。

- workflow run: `failure`
- 必須チェックの失敗
- health collector 自体の取得失敗

## Separation

```text
health      → 壊れているか
wf-errors   → 何が壊れたか / なぜか / どう直すか
```

health は判定を単純に保ち、診断は `bonsai/wf-errors` に委譲する。

## State

```yaml
health: healthy | unhealthy | unknown
error_count: 0
checked_at: ISO-8601
source: github_actions
repository: bonsai/health
```

`error_count > 0` の場合、必ず `health: unhealthy`。

## Future

- Bonsai 複数 repository の横断チェック
- `latest → now` の current state
- HTML dashboard
- GAS / Chrome extension からの参照
