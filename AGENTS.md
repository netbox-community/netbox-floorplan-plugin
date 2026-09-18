# AGENTS.md — netbox-floorplan-plugin

## Repository Overview

`netbox-floorplan-plugin` is a NetBox plugin that adds spatial floorplans to sites and locations. A **floorplan** is a canvas on which racks and unracked devices are placed, so that the drawing reflects where equipment physically sits within a room. Each placed object references the NetBox record it represents, and is reconciled against NetBox every time the floorplan is viewed.

The plugin has real models and migrations, UI views, a REST API, and a substantial browser-side editor built on Fabric.js. It has **no configuration parameters** — nothing goes in `PLUGINS_CONFIG` — and no GraphQL API. The supported NetBox range is in `COMPATIBILITY.md`.

## Tech Stack

- Python (defer to `setup.py`; currently `>=3.12`)
- NetBox (host app — minimum and maximum versions are pinned in `netbox_floorplan/__init__.py`)
- Django + Django REST Framework (provided by NetBox)
- [Fabric.js](http://fabricjs.com/) **5.2.1** — the canvas library, vendored at
  `static/netbox_floorplan/vendors/fabric-js-5.2.1.js`, along with jQuery and htmx.
  Consult the **v5** documentation: the callback APIs the plugin relies on
  (`loadFromJSON(json, callback, reviver)`, `fabric.Image.fromURL(url, callback)`,
  `setBackgroundImage(img, callback, options)`) were all replaced by promises in v6, so v6 docs
  give systematically wrong answers. The file was previously misnamed `fabric-js-6.0.2.js`
  despite containing 5.2.1; verify the version in the file itself (`var fabric={version:"…"}`
  on line 1) rather than trusting the filename.
- Django's test runner via NetBox (`manage.py test netbox_floorplan`), run inside Docker
- flake8 for lint (config split across `.flake8` and `setup.cfg`)
- mkdocs + mkdocs-material for user-facing docs

The plugin declares **no** `install_requires`. Defer version pins to `setup.py` and `netbox_floorplan/__init__.py`.

## Repository Map

```text
.
├── netbox_floorplan/
│   ├── __init__.py              — FloorplanConfig (PluginConfig): NetBox min/max version.
│   │                              No default_settings; the plugin has no settings.
│   ├── models.py                — Floorplan and FloorplanImage. Holds resync_canvas().
│   ├── views.py                 — Generic views for FloorplanImage, plus bare Views for the
│   │                              canvas editor and the add-by-query-param flow, plus the
│   │                              Site/Location tab views.
│   ├── forms.py, tables.py, filtersets.py
│   ├── urls.py                  — Explicit paths plus get_model_urls() for FloorplanImage.
│   ├── navigation.py            — Plugin menu (Floorplan Images only).
│   ├── utils.py                 — file_upload() path helper.
│   ├── templatetags/
│   │   └── template_utils.py    — denormalize_measurement, js_str, rack_outer_js.
│   ├── api/                     — serializers, views, urls (REST only; no GraphQL).
│   ├── migrations/              — 13 migrations. Never hand-write these.
│   ├── static/netbox_floorplan/
│   │   ├── floorplan/           — edit.js, view.js, utils.js: the editor.
│   │   └── vendors/             — Fabric.js, jQuery, htmx. Do not edit.
│   ├── templates/netbox_floorplan/
│   └── tests/                   — Runs under NetBox's test runner; needs Postgres.
├── develop/                     — Docker Compose dev stack, driven by the Makefile.
│   ├── Dockerfile               — Clones NetBox at NETBOX_VER, pip-installs the plugin -e.
│   ├── docker-compose.yml       — netbox, worker, postgres, redis.
│   ├── configuration.py         — NetBox config for the dev stack.
│   ├── local_release.yaml       — Version override; see Troubleshooting.
│   └── dev.env
├── docs/                        — mkdocs site (see mkdocs.yml for nav).
├── media/                       — Demo GIFs referenced by the README.
├── CHANGELOG.md                 — Canonical changelog; docs/changelog.md includes it.
├── CONTRIBUTING.md              — Dev environment, tests, conventions.
├── COMPATIBILITY.md             — Plugin release to NetBox version matrix.
├── netbox-plugin.yaml           — Manifest published to the NetBox plugin catalogue.
└── .github/workflows/
    ├── tests.yml                — flake8 only. The test suite does not run in CI.
    ├── manifest-modified.yaml   — Publishes netbox-plugin.yaml changes.
    └── pub-pypi.yml             — Publishes to PyPI on a published release.
```

## Architecture

### The canvas

A floorplan's drawing lives in `Floorplan.canvas`, a JSON document produced and consumed by Fabric.js in the browser. Python does not draw anything; it stores the document and reconciles the metadata inside it.

Each placed rack or device is a *group*: the group carries `custom_meta` identifying the NetBox object (`object_type`, `object_id`, `object_name`), and its members are a rectangle plus one or more text labels. Labels carry a `text_type` of `name`, `status`, or `info`, which determines how `resync_canvas()` refreshes them.

Note the asymmetry: `mapped_racks` / `mapped_devices` inspect the **members'** `custom_meta`, while `resync_canvas()` keys off the **group's** `custom_meta`. Changing one without the other will silently break the picker or the refresh.

### `resync_canvas()`

Called from the tab views and the editor on every view. It updates names, rebuilds `info` labels from current status/role/tenant, reapplies role colouring unless `manual_color` is set, and drops objects whose rack or device has been deleted. It saves only if something changed.

This is why the drawing never drifts from NetBox, and why there is no "refresh" action.

### Site XOR location

A floorplan is assigned to exactly one of a site or a location. This is validated in `clean()` (so forms and the API report a field error) **and** again in `save()` (because `FloorplanAddView` builds a `Floorplan` directly and never calls `clean()`). Keep both.

`record_type` returns `'site'` or `'location'` and is used throughout the views and templates to branch.

### Views are not all generic

`FloorplanImage` uses NetBox's generic views and `register_model_view`, so it behaves conventionally. `Floorplan` does not:

- `get_absolute_url()` points at the **canvas editor**, which is a bare `django.views.View`, not an `ObjectView`. There is no read-only detail view.
- `FloorplanAddView` is a bare `View` that creates a floorplan from a `?site=` or `?location=` query parameter and redirects to the editor. There is no create form.
- `FloorplanRackListView` / `FloorplanDeviceListView` are `ObjectListView`s over `dcim` models, filtered by `?floorplan_id=`, used as the editor's pickers.

This shapes the tests: most of NetBox's generic `ViewTestCases` do not apply to `Floorplan`.

### Deprecated rack fields

`Rack.outer_width`, `outer_depth` and `outer_unit` are deprecated in NetBox 4.7 and will be inferred from the rack's `RackType` in v5.0. Read them through the `rack_outer_js` filter, which prefers the `RackType` and falls back to the Rack's own field. Do not read them off the Rack directly.

`select_related('role', 'rack_type')` in the picker views exists to keep that lookup from becoming a query per row.

### JavaScript in table columns

The pickers build `onclick` handlers containing JavaScript string literals. **Never interpolate a value straight into one.** Django escapes a quote to `&#x27;`, which the browser decodes back to a quote *before* the JavaScript is parsed, so a rack named `O'Brien` produces a syntax error and a dead button. Use the `js_str` filter, which emits a JavaScript escape sequence that survives HTML attribute decoding.

Any `template_code` block using these filters must also `{% load template_utils %}` — a `TemplateColumn` does not inherit the loads of the page it renders into.

### Key files

| File | Why you'd open it |
|---|---|
| `netbox_floorplan/models.py` | Canvas reconciliation, validation rules |
| `netbox_floorplan/views.py` | The editor, the add flow, the pickers, the tabs |
| `netbox_floorplan/tables.py` | The picker rows and their onclick handlers |
| `netbox_floorplan/templatetags/template_utils.py` | JS escaping and deprecated-field resolution |
| `netbox_floorplan/static/netbox_floorplan/floorplan/edit.js` | Everything the editor does client-side |
| `netbox_floorplan/api/serializers.py` | REST fields and brief representations |

## Commands

| Command | What it does |
|---|---|
| `make cbuild` | Build the dev image |
| `make debug` | Run the stack in the foreground (NetBox on `:8000`) |
| `make start` / `make stop` | Run detached / tear down |
| `make destroy` | Tear down **and drop the PostgreSQL volume** |
| `make adduser` | Create a superuser |
| `make nbshell` / `make shell` | NetBox shell / Django shell |
| `make migrations` | Generate migrations after a model change |
| `make test` | Build the image, then run the full test suite |
| `make update-query-counts` | Regenerate `tests/query_counts.json` |
| `make collectstatic` | Run `collectstatic` |
| `mkdocs build --strict` | Build the docs; fails on broken internal links |

## Development

Everything runs in Docker; there is no local Python path that can run this plugin, because it needs NetBox, PostgreSQL and Redis.

`NETBOX_VER` and `PYTHON_VER` at the top of the `Makefile` control which NetBox ref the image builds from. `NETBOX_VER` is a git ref, so it can be a branch (`feature`, `main`) or a tag.

After changing `models.py`, run `make migrations` and commit the generated file with the change. Never hand-write a migration.

## Testing

- Tests use NetBox's test framework (`django.test.TestCase` and NetBox's `ViewTestCases` / `APIViewTestCases`), run with `python manage.py test netbox_floorplan` inside the container. Use `make test`.
- A real PostgreSQL database is created. Do not mock the database.
- Most of the test count comes from NetBox's base classes, so adding a model to a `ViewTestCases` / `APIViewTestCases` subclass buys a lot of coverage cheaply.

Two conventions are easy to miss when subclassing those base classes from a plugin, and both fail confusingly:

- `_get_base_url()` must be overridden to return `plugins:<app_label>:<model>_{}`. NetBox's default omits the `plugins:` namespace.
- API test cases must set `view_namespace = 'plugins-api:netbox_floorplan'`. The default is derived from the app label alone and omits the `plugins-api:` prefix, giving `KeyError: 'netbox_floorplan-api'`.

| Module | Coverage area |
|---|---|
| `test_models.py` | `__str__`, validation, canvas properties, `resync_canvas()` |
| `test_api.py` | REST API via `APIViewTestCases`, plus site/location validation |
| `test_views.py` | Generic views, plus the editor, add flow, tabs and pickers |
| `test_filtersets.py` | `search()` and the explicit filters |
| `test_templatetags.py` | `js_str`, `rack_outer_js`, `denormalize_measurement` |

### Query-count baselines

NetBox asserts list views execute a known number of SQL queries, against baselines in `netbox_floorplan/tests/query_counts.json`. A missing key or changed count fails the test. Regenerate with `make update-query-counts` and review the diff — a jump usually means an N+1 was introduced, not that the baseline was stale.

## CI/CD

- **`tests.yml`** — runs flake8 only. The test suite is **not** run in CI, because it needs a NetBox checkout plus PostgreSQL and Redis. Run `make test` locally before opening a pull request.
- **`manifest-modified.yaml`** — on pushes to `main` touching `netbox-plugin.yaml`, calls netboxlabs' reusable workflow to publish the manifest.
- **`pub-pypi.yml`** — on a published GitHub release, builds and uploads to PyPI via OIDC trusted publishing.

## Common Tasks

### Add a field to a model

1. Edit `netbox_floorplan/models.py`.
2. `make migrations`, and commit the generated migration.
3. Thread it through `forms.py`, `tables.py`, `filtersets.py`, `api/serializers.py` (both `fields` and `brief_fields` if relevant), and the templates.
4. Document it under `docs/models/`.
5. Add tests.
6. Add a `CHANGELOG.md` entry.

### Change the editor

The client-side code is in `static/netbox_floorplan/floorplan/`. There is no build step or bundler — the files are served as-is, so `make collectstatic` (or a container restart) is all that is needed. Do not edit anything under `vendors/`.

Remember that the canvas document is persisted, so a change to the structure the editor writes must remain readable by `resync_canvas()` on the Python side, and must tolerate documents written by earlier versions.

### Bump the supported NetBox version

1. Update `min_version` / `max_version` in `netbox_floorplan/__init__.py`.
2. Add a row to `COMPATIBILITY.md`.
3. Add an entry to `netbox-plugin.yaml` — this is the manifest published to the plugin catalogue, and is easy to forget.
4. Update `NETBOX_VER` in the `Makefile` if the dev stack should track a new ref.
5. Review `develop/local_release.yaml` (see Troubleshooting).

## Conventions and Patterns

- **Branches.** `feature` is active development and the base for pull requests. `main` is released code and what releases are cut from. GitHub defaults new PRs to `main`, so the base usually needs changing.
- **Changelog.** User-visible changes get an entry in the root `CHANGELOG.md`. Do not edit `docs/changelog.md` — it is a one-line `pymdownx.snippets` include (`--8<-- "CHANGELOG.md"`) so there is a single source of truth.
- **Never read deprecated NetBox fields directly.** See Architecture.
- **Never interpolate values into JavaScript without `js_str`.** See Architecture.
- **The plugin has no settings.** Resist adding `PLUGINS_CONFIG` options for things that belong on the model.
- **`display` and `brief_fields`** belong on every serializer. A brief representation with no human-readable label is not useful.

## Troubleshooting

**The plugin silently does nothing — no tab, no menu, no template tags.** It failed to load. NetBox logs a warning at startup rather than erroring:

```
Unable to load plugin netbox_floorplan: Plugin netbox_floorplan requires NetBox
minimum version 4.7.0 (current: 4.6.8).
```

NetBox's `feature` branch keeps reporting the *previous* release in its `release.yaml` until a release is cut, so a `min_version` pinned to the upcoming version rejects it. The dev stack works around this with `develop/local_release.yaml`, mounted over `local/release.yaml` in the container, which NetBox overlays onto its own release data. Remove it once `NETBOX_VER` points at a real tag.

**`'template_utils' is not a registered tag library`.** Almost always the same problem as above: the app is not installed, so its `templatetags` package is never discovered. Check for the load warning at startup before suspecting the template.

**The canvas is blank with console errors.** `collectstatic` has not been run, so the editor's JavaScript is not being served.

**A rack is drawn at the wrong size.** It has no rack type, or its rack type has no outer width and depth. The plugin falls back to a default size.

**A picker button does nothing.** Look for a JavaScript syntax error in the console caused by an unescaped value in the `onclick` handler — see the JavaScript section under Architecture.

## References

- User documentation: `docs/` (built with mkdocs; `mkdocs.yml` has the nav)
- Development and test workflow: `CONTRIBUTING.md`
- Supported NetBox versions: `COMPATIBILITY.md`
- [NetBox plugin development docs](https://netboxlabs.com/docs/netbox/plugins/development/)
- [Fabric.js documentation](http://fabricjs.com/docs/) — the canvas library
- Originally forked from [tbotnz/netbox_floorplan](https://github.com/tbotnz/netbox_floorplan)
