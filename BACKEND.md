# Motion Presets backend · v0.4.1

## Commands and schema

Primary/secondary actions in exact advertised order: `apply`, `restore`, `favorite`, `capture`, `import`, `export-preset`, `compare`, `preview`, `confirm` (Keep).

```
/usr/bin/python3 runtime/0.4.1/backend.py catalog
/usr/bin/python3 runtime/0.4.1/backend.py action --id reduced --verb apply --apply
/usr/bin/python3 runtime/0.4.1/backend.py action --id off --verb preview --apply
/usr/bin/python3 runtime/0.4.1/backend.py action --id off --verb confirm --apply
/usr/bin/python3 runtime/0.4.1/backend.py action --id restore:last --verb restore --apply
/usr/bin/python3 runtime/0.4.1/backend.py preferences --apply --payload '{"options":{"showDiffs":false}}'
```

Apply persists for the session without a timer; Preview starts the independent 15-second rollback. Rows: `reduced`, `direct`, `wraparound`, `off`, plus named captures. The allowlist is exactly boolean `animations.enabled` and `animations.workspace_wraparound`. Bundled rows never enable animations. Captures/imports may remember true as inert data, but Apply/Preview/Compare clamp that field to false if the current animation setting is disabled. Explicit Restore may restore the actual prior enabled state.

## Preview as the primary action

Saved `primaryAction` is enum `apply` (default) / `preview`. The catalogue keeps
its existing advertised action order, including `preview`. The UI chooses the
saved primary only when that action is advertised; configuration never invokes
it. Explicit Apply remains untimed and Preview remains a 15-second trial.

```
/usr/bin/python3 runtime/0.4.1/backend.py preferences --apply --payload '{"options":{"primaryAction":"preview"}}'
```

## Motion-specific scope

The requested **subtle/snappy/smooth/expressive modes and animation speed are incomplete**, not renamed copies of scalar toggles. Inspected qualified source exposes `hl.animation({leaf,enabled,speed,bezier|spring,style})` as a setter, with no matching exact getter or unoverride operation. `hyprctl -j animations` serializes speed using two decimal places and exposes inheritance/overridden state that this setter cannot restore. Installed animation-tree headers likewise offer no public Lua inverse. Taking rounded/inherited values as an exact backup would regress the existing Restore guarantee. This candidate therefore does not write curves, animation leaves, speed, styles or inheritance, and does not advertise a nonfunctional speed setting. Parent must resolve this API/acceptance conflict before claiming the complete six-mode feature.

## Provider and trust boundary

System `/usr/bin/python3`, Python standard library and installed `hyprctl`; the adapter is qualified for **Hyprland Lua 0.56.2 only** and rejects other versions. Runtime paths derive from `__file__`, never cwd. Each package includes its own runtime helpers; no sibling plugin is required. Native shell code is unsandboxed at runtime; the development runner is not a runtime security sandbox.

Only `hyprctl -j version`, `hyprctl -j getoption <allowlisted dotted key>` and generated fixed-key `hyprctl eval` are used. Generated Lua uses `hl.get_config` for compare-before-write and `hl.config({[known_key]=typed_literal})` for mutation. Gap tables have named `top/right/bottom/left` fields. Strings use decimal-escaped UTF-8 bytes. No `repl`, bare print, arbitrary Lua, shell evaluation, dispatcher, installer, reload or configuration-file rewrite is used.

Every write/action requires `--apply`; success is JSON with `ok:true`, failure is nonzero JSON with plain bounded text and no traceback. Unexpected options, inappropriate payloads and invalid membership fail closed. CLI payloads are JSON objects limited to **16384 UTF-8 bytes**; duplicate keys, nonfinite numbers, malformed Unicode and nesting beyond 12 levels are rejected. ID strings never become commands or output paths. Catalogue reads do no IPC or writes and expose fresh rows, `preferences` and `settingsSchema`.

## v0.4.0 display preferences

The exact enum keys are `density` (`comfortable` default, `compact`), `layout`
(`list` default, `grid`), and `sortOrder` (`default` default, `name`,
`favorites-first`). They affect native catalogue presentation only. Existing
stores without these keys receive defaults without an implicit write; Reset
returns those defaults. The UI owns stable sorting and fresh action admission.
All settings writes remain local preference operations, never compositor setters.

## Preferences

`PREFERENCE_SCHEMA` is passed to the bundled `preferences.py` helper's exact `read`, `change`, `reset`, `toggle`, `remember` APIs. Storage is `${XDG_CONFIG_HOME:-$HOME/.config}/omarchy/lego/<slug>/preferences.json`, outside the installed source. The helper bounds reads, rejects unsafe files/ancestor symlinks, locks updates and uses fsync plus atomic replacement. Corrupt preferences are not silently reset.

```
/usr/bin/python3 runtime/0.4.1/backend.py preferences
/usr/bin/python3 runtime/0.4.1/backend.py preferences --apply --payload '{"reset":true}'
/usr/bin/python3 runtime/0.4.1/backend.py preferences --apply --payload '{"favorites":["known-id"],"collections":{"Desk":["known-id"]}}'
```

Reads return `{ok,preferences,settingsSchema,message}`. Patches accept only `options`, `favorites`, `collections`; recent/version cannot be written. Reset is the sole-key `{reset:true}` request and resets **only preferences**, never custom presets, generated effects or transaction journals. Favorites may retain stale IDs inertly; Favorite actions require fresh membership. Recents update only after confirmed Apply/Preview/export. If recent persistence fails after an externally confirmed action, success remains truthful with a warning rather than reporting an invented action failure.

## Transaction and Restore invariants

Journals live under `${XDG_STATE_HOME:-$HOME/.local/state}/omarchy-<slug>/<sha256(instance)[:24]>/`. Plugin and session directories must be user-owned private directories, not symlinks. A nonblocking flock serializes transactions. A bounded pending journal is fsynced and atomically replaced before any setter, retaining the first actual `before`, immediately previous actual values and planned target. A final compositor readback confirms success.

Each setter guards all owned current values inside compositor Lua. Partial failures compensate only values this transaction could have written, in reverse order. Active publication uses a separate record: it cannot mutate the in-memory pending intent. Before compensation, that original pending intent must be durably republished even when active replace succeeded but acknowledgement/fsync failed. If that persistence fails, no compensating setter runs. Lost compensation acknowledgement leaves a pending journal recoverable from the real previous/target mixture, not a fabricated baseline. Failed compensation retains the receipt and reports failure.

Restore accepts any freshly known row or the exact `restore:last` alias, **only with Restore**. The exact alias/Restore pair follows only the validated receipt without loading the catalogue, so a missing, corrupt or unsafe custom store cannot block recovery; Apply, Keep and imports still require their normal validation. Active state must exactly match expected values; interrupted pending state accepts only per-key previous/target mixtures. Divergent external values block Restore/timeout without clobbering the values or journal. Unrelated options remain untouched. Successful Restore removes the receipt; a second Restore fails honestly.

This is optimistic value-level conflict detection, not a global compositor lock. Same-value **ABA edits cannot be distinguished**. Restore does not restore `setByUser` diagnostics or undo arbitrary normal provider side effects. External writers, another plugin and config reloads may create deliberate conflicts. Resolve those explicitly and retry Restore; do not delete a journal to hide failure.

Each IPC reply and preset/journal read is bounded to 64 KiB. JSON file reads use nofollow/nonblocking descriptors, require regular files, check metadata stability, reject duplicates/nonfinite/deep JSON and read at most cap+1. Each helper call has a three-second wall timeout, incremental output cap and owned-process-group kill, including helpers that close stdout then hang. Overall UI cancellation/watchdog admission belongs to the native controller; accepted external work cannot be revoked by closing a panel.

## Offline verification

Run from this checkout, with an existing approved private scratch directory:

```
TMPDIR="${TMPDIR:?Set an existing private scratch directory}" env -u PYTHONPATH PATH=/usr/bin /usr/bin/python3 scripts/run-tests.py --backend-only
```

The shipped runner uses offline bwrap, unshared network, cleared environment, fresh fake HOME, hidden real HOME and `/run`, no live display/compositor sockets, read-only source/system files and fake IPC. The fake `hyprctl` executes generated Lua with the installed system Lua against an observable fake `hl` object. This proves logic/transport, not C++ compositor/GPU integration. Full native/component gate: `bash test.sh` with the same TMPDIR. Historical validation records describe their original source versions, not current-source coverage.

## Named captures, strict import/export

```
/usr/bin/python3 runtime/0.4.1/backend.py action --id capture:current --verb capture --apply --payload '{"name":"My desk"}'
/usr/bin/python3 runtime/0.4.1/backend.py action --id <known-id> --verb export-preset --apply
/usr/bin/python3 runtime/0.4.1/backend.py action --id import:preset --verb import --apply --payload '<versioned preset JSON>'
```

Capture reads actual allowlisted compositor values but calls no setter and writes no recovery journal. Import validates before storage and does no IPC. Export returns `{ok,message,preset,detail,preferences?}` containing inert JSON, never writes to a caller-chosen output path and never evaluates data. Apply is a separate explicit operation after import.

Format: `{ "version":1, "slug":"motion-presets", "name":"My desk", "settings":{...typed allowlisted fields...} }`; no other top-level or setting keys. Names are 1–80 printable characters with no edge whitespace. IDs are `custom-<sha256(name)[:16]>`, never derived as filesystem paths. At most 32 custom presets fit in the fixed private `custom-presets.json` beside preferences. Existing names/collisions/full stores are refused, never overwritten. File symlinks, special files, hardlinks, wrong ownership, public modes, corruption and oversize data fail closed. Ancestor symlinks cannot redirect imports. Storage is locked, bounded to 64 KiB and atomically replaced using a private fsynced temporary file. Preferences Reset leaves it alone.

`compare` returns `{ok,message,diff:[{key,before,after}],detail}` with actual typed changes and no setters or journal. Numeric summaries are controlled by boolean option `showDiffs` (default true); this is a catalogue preference, not a compositor setting.

## Independent timed preview

The watchdog is a detached, separately session-owned `/usr/bin/python3 backend.py watchdog --token <32 lowercase hex>` process, not a QML timer. It announces complete PID bytes using private temporary-file plus exclusive hard-link readiness publication. A replacement token/PID/deadline is published only after independent readiness. The predecessor's authority/deadline remain durable during pending transactions and spawn/unready/ready-before-publication boundaries.

Pending compensation preserves the current ready owner's token/PID/deadline. Predecessor rearming preserves its original deadline rather than extending it; a failed rearm retains the successor's pending authority. Keep verifies the matching unexpired current row, exact readback and durable receipt readback before retiring timer authority; failed Keep rearms or restores. Restore/disable retire authority only after confirmed readback. Superseded tokens do nothing. Temporary IPC loss gets bounded retry; unresolved IPC/external conflicts retain the journal for explicit Restore. The process cannot survive logout, missing runtime files or an inaccessible compositor indefinitely. It is recovery, not a promise to overwrite external edits or recover from arbitrary host failure.

Motion export/import permits a nonempty subset of its two boolean keys, matching the legacy scalar rows; Capture always reads both. No default value is invented to fill an unspecified key.

New preference writes have a separate aggregate limit of **128 KiB compact UTF-8
JSON**, checked under the store lock before mutation; rejection preserves existing
bytes. Per-field counts and the 16384-byte CLI payload limit do not increase that
aggregate. Legacy reads remain bounded to **16 MiB** and fully schema-validated,
allowing explicit Reset to shrink old valid stores without touching custom presets
or recovery journals. Reply JSON must be **strictly below 1 MiB** after UTF-8
serialization; with its terminating LF, the wire reply is **at most 1 MiB**,
matching the inclusive UI collector/parser budget. Oversized read snapshots fail
cleanly; an already confirmed action omits its optional preference snapshot with
a warning instead of fabricating an external-action failure. Ordinary preference
patches refuse an already oversized snapshot before mutation; explicit Reset
remains available.
