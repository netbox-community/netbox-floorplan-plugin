# Contributing

Thanks for contributing to `netbox-floorplan-plugin`. This document covers the
development environment, the test workflow, and the conventions to follow when adding to
the plugin.

## Requirements

* Docker with Compose v2 (`docker compose`, not `docker-compose`)
* GNU Make

Everything runs inside a Docker Compose stack, so no local Python environment or
PostgreSQL install is needed.

## Branches

Development happens on `feature`, which targets the upcoming NetBox release. Branch from
`feature` and open pull requests against it. `main` holds the released code and is the
branch releases are cut from.

## Development environment

`develop/` contains a Compose stack (NetBox + worker + PostgreSQL + Redis). The plugin
source is bind-mounted into the NetBox container, so edits on the host apply after a
container restart, or immediately under `runserver` autoreload.

Always drive the stack through `make` rather than raw `docker compose`, so the project
name and compose file stay consistent.

| Command | What it does |
|---|---|
| `make cbuild` | Build the dev image |
| `make debug` | Run the stack in the foreground (NetBox on `:8000`) |
| `make start` | Run the stack detached |
| `make stop` | Stop the stack |
| `make destroy` | Stop the stack **and drop the PostgreSQL volume** |
| `make adduser` | Create a superuser |
| `make nbshell` / `make shell` | NetBox shell / Django shell |
| `make migrations` | Generate migrations for the plugin |
| `make test` | Build the image, then run the test suite |
| `make update-query-counts` | Regenerate the query-count baselines (see below) |
| `make collectstatic` | Run `collectstatic` |

`NETBOX_VER` and `PYTHON_VER` at the top of the `Makefile` control which NetBox ref the
image is built from. `NETBOX_VER` is a git ref, so it can be a branch (`feature`, `main`)
or a tag.

### The version override

`develop/local_release.yaml` declares the NetBox version the dev stack reports, and is
mounted over `local/release.yaml` inside the container.

This exists because NetBox's `feature` branch continues to report the *previous*
release in its own `release.yaml` until a release is cut. The plugin declares
`min_version = "4.7.0"`, so without the override NetBox refuses to load it:

```
Unable to load plugin netbox_floorplan: Plugin netbox_floorplan requires NetBox
minimum version 4.7.0 (current: 4.6.8).
```

Remove the override once `NETBOX_VER` points at a real 4.7 tag.

## Tests

```
make test
```

This builds the image and runs `python manage.py test netbox_floorplan` inside the
container. To run a single test:

```
docker compose -f develop/docker-compose.yml -p netbox_floorplan run --rm netbox \
  python manage.py test netbox_floorplan.tests.test_models.FloorplanTestCase.test_record_type
```

Tests live in `netbox_floorplan/tests/`, mirroring the structure of the plugin:

| File | Covers |
|---|---|
| `test_models.py` | `__str__`, `clean()` validation, canvas properties, `resync_canvas()` |
| `test_api.py` | REST API, via NetBox's `APIViewTestCases` |
| `test_views.py` | UI views, via NetBox's `ViewTestCases`, plus the custom views |
| `test_filtersets.py` | FilterSet `search()` and explicit filter fields |
| `test_templatetags.py` | The `template_utils` filters |

Most of the test count comes from NetBox's base classes rather than explicit `test_*`
methods, so adding a model to a `ViewTestCases`/`APIViewTestCases` subclass pulls in a
large amount of coverage for free.

Two conventions are easy to miss when using those base classes from a plugin:

* `_get_base_url()` must be overridden to return `plugins:<app_label>:<model>_{}`. The
  default omits the `plugins:` namespace.
* API test cases must set `view_namespace = 'plugins-api:netbox_floorplan'`. The default
  is derived from the app label alone and omits the `plugins-api:` prefix.

Not every generic case applies. `Floorplan` has no detail or edit view —
`get_absolute_url()` points at the canvas editor, which is a plain Django `View` rather
than an `ObjectView` — and `FloorplanTable` has no linkified column, so the generic list
case (which asserts each object's URL appears in the rendered list) is excluded in favour
of a targeted test.

### Query-count baselines

NetBox asserts that list views execute a known number of SQL queries, using per-app
baselines committed at `netbox_floorplan/tests/query_counts.json`. A test fails if the
recorded key is missing or the count has changed.

If you add a model with a list view, or change prefetching, serializers, or table columns
in a way that moves the query count, regenerate the baselines and commit the result:

```
make update-query-counts
```

This runs the suite with `UPDATE_QUERY_COUNTS=1`, which records observed counts instead of
asserting them. It must run serially. Review the diff before committing: an unexpected
jump usually means an N+1 was introduced rather than that the baseline was stale.

## Migrations

Never hand-write migrations. After any change to `models.py`:

```
make migrations
```

This runs `makemigrations` inside the container and writes into
`netbox_floorplan/migrations/`. Commit the generated file with the model change.

### Data migrations and branching

Schema-only migrations need nothing special. A migration that also *moves data* — a
`RunPython` or `RunSQL` operation — must declare how it behaves inside a
[netbox-branching](https://github.com/netboxlabs/netbox-branching) branch schema, by
setting `fake_on_branch` on the `Migration` class:

```python
class Migration(migrations.Migration):
    # Data already migrated in main; branch schemas inherit the result.
    fake_on_branch = True
```

`True` always fakes the migration on a branch, `False` always runs it, and leaving it unset
falls back to netbox-branching's heuristic. Set it explicitly rather than relying on the
heuristic: a data migration that re-runs against a branch schema can operate on the wrong
rows.

All 13 existing migrations are schema-only, so none carries the flag.

See [Branching](docs/branching.md) for the plugin's overall branching behaviour, including
the fact that uploaded image files are not branched.

## Deprecated NetBox fields

`Rack.outer_width`, `outer_depth` and `outer_unit` are deprecated as of NetBox 4.7 and
will be inferred from the rack's `RackType` in v5.0. Read them through the
`rack_outer_js` filter in `templatetags/template_utils.py`, which prefers the `RackType`
and falls back to the Rack's own field, rather than off the Rack directly.

## JavaScript in templates

The rack and device tables build `onclick` handlers containing JavaScript string
literals. Never interpolate a value straight into one: Django escapes a quote to the HTML
entity `&#x27;`, which the browser decodes back to a quote *before* the JavaScript is
parsed, so a rack named `O'Brien` breaks the handler. Use the `js_str` filter, which
emits a JavaScript escape sequence that survives HTML attribute decoding.

## Coding standards

`flake8` runs in CI (`.github/workflows/tests.yml`). Configuration lives in `.flake8` and
`setup.cfg`.

## Compatibility and releases

The supported NetBox range is declared by `min_version` / `max_version` in
`netbox_floorplan/__init__.py`. When it changes, update all three of:

* `netbox_floorplan/__init__.py`
* `COMPATIBILITY.md`
* `netbox-plugin.yaml` — the manifest published to the NetBox plugin catalogue

`make relpatch` bumps the patch version and pushes a release branch.
