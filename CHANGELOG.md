# Change Log

## v0.10.0

**Targets NetBox 4.7.** The supported range is declared as a minimum of 4.7.0 and a
maximum of 4.7.99; see the [compatibility matrix](https://github.com/netbox-community/netbox-floorplan-plugin/blob/main/COMPATIBILITY.md)
for earlier releases.

### Breaking Changes

* **The REST API now returns a `display` field** on both Floorplan and Floorplan Image.
  This is additive — no fields were removed — and brings the serializers in line with
  every other NetBox object.

* **`?brief=1` on the Floorplan endpoint now returns a brief representation.** Previously
  it returned every field, including the entire `canvas` document, because the serializer
  declared no `brief_fields`. It now returns `id`, `url` and `display`. Clients relying on
  `?brief=1` returning full objects must drop the parameter.

### Bug Fixes

* **The floorplan image detail page no longer renders a broken link.** Its first row printed
  `{ object.access_list.get_absolute_url }` — single braces, so Django never evaluated it and
  the literal text ended up in the `href` — against a field belonging to a different plugin
  entirely, which this one has never had. The row displayed the object's own ID and led
  nowhere; it is gone, and the ID remains visible in the page header as NetBox shows it for
  every object.

* **Fixed the unbalanced markup on the same page**, where the column `div` closed before the
  tags and comments panels, leaving them outside the column they were meant to sit in.

* **The floorplan action buttons now resolve their URLs through `{% url %}`.** They were
  hardcoded to `/plugins/floorplan/...`, which is wrong for any NetBox deployed under a
  `BASE_PATH`.

* **Floorplan images failed to load behind a reverse proxy**
  ([#96](https://github.com/netbox-community/netbox-floorplan-plugin/issues/96)). The API
  serialised the uploaded file as an absolute URL built from the request, so the hostname
  NetBox saw was baked into the page and into saved canvases. Where that hostname differs
  from the one the browser uses — the usual arrangement behind a reverse proxy — images 404.

    A new read-only `file_url` field renders the URL with the storage backend instead:
    `MEDIA_URL`-relative for local storage, so the browser resolves it against whatever
    origin it is actually using, and absolute for remote storage (S3, a CDN), so those
    deployments are unaffected. The canvas now uses this field. `file` keeps its existing
    absolute form, so API consumers are unchanged.

    Existing floorplans are repaired on load: absolute media URLs in a stored canvas are
    rewritten to paths, so no re-saving is required. Newly placed device images are stored
    relative, via Fabric's `srcFromAttribute`.

* **Placed objects appeared shifted or compressed after reloading a floorplan**
  ([#100](https://github.com/netbox-community/netbox-floorplan-plugin/issues/100)). The
  background image was positioned from inside `loadFromJSON()`'s reviver, which Fabric calls
  once per object *before* it has added any of them to the canvas. The code looked for the
  floorplan boundary among the canvas objects to scale the background to it, never found one,
  and fell back to scaling the background to the canvas and centring it — so the background no
  longer lined up with the objects placed on it. It also started one image load per object,
  racing them.

    The background is now applied once, from the completion callback, when the boundary
    genuinely exists. Zoom and resize also run after that rather than synchronously before the
    canvas has been populated.

* **Searching floorplans raised an error.** `FloorplanFilterSet.search()` filtered on a
  `description` field, which `Floorplan` does not have — it extends `NetBoxModel`, and
  only `PrimaryModel` provides `description`. Any `?q=` search therefore raised
  `FieldError`. Search now matches the name of the assigned site or location.

* **Comments on a Floorplan Image were silently discarded.** The form declared a
  `comments` field and displayed it, but omitted it from `Meta.fields`, so anything
  entered was thrown away on save.

* **Site/location validation is now reported as a form error.** A floorplan must be
  assigned to exactly one of a site or a location. This was enforced only in `save()` by
  raising `ValueError`, which surfaced as a server error; it is now validated in `clean()`
  and raises `ValidationError`, so the UI and REST API report it against the object.
  `save()` retains its own guard for code paths which never call `clean()`.

* **The size of an externally-linked image no longer errors.** `FloorplanImage.size`
  built a list of expected exceptions and then caught `NameError` instead of using it. An
  image with an external URL and no uploaded file has no file to measure, and Django
  raises `ValueError` in that state, so the detail view failed to render.

* **Rack and device names containing an apostrophe broke the floorplan editor.** The rack
  and device pickers build JavaScript `onclick` handlers, and interpolated values directly.
  Django escapes a quote to `&#x27;`, which the browser decodes back to a quote before the
  JavaScript is parsed, so a rack named `O'Brien` produced a syntax error and the button
  did nothing. Values are now escaped for JavaScript.

* **Duplicate `comments` entry** removed from the Floorplan Image form fieldsets.

* **The plugin declared no minimum NetBox version.** `min_version` was left commented out
  in `FloorplanConfig` after local testing against a pre-release NetBox `feature` build, so
  NetBox never rejected an incompatible (pre-4.7) installation. It is now set to `4.7.0`,
  matching `max_version` and the compatibility matrix.

* **Floorplan Images had no REST API filterset**, so `FloorplanImageViewSet` silently
  ignored every filter parameter, including `?q=`. Added `FloorplanImageFilterSet`,
  matching against name, external URL and comments.

* **Floorplan search now also matches the assigned image's name**, not just the site or
  location.

### Other Changes

* **The object views now use NetBox's declarative UI components instead of templates.** The
  floorplan tab on sites and locations, and the floorplan image detail page, declare a
  `layout` built from `netbox.ui` panels. The image's attribute table is now an
  `ObjectAttributesPanel` in `netbox_floorplan/ui/panels.py`, and its template is gone.

    The canvas stays a template, since a Fabric.js drawing surface has no declarative
  equivalent, but it is now a `TemplatePanel` — so the page chrome around it comes from the
  layout rather than from hand-written `content` and `breadcrumbs` blocks.
  `floorplan_view.html` keeps only the two asset blocks a panel cannot reach: the Fabric.js
  and jQuery includes, and the canvas stylesheet and module script.

    Breadcrumbs come from the layout. The site tab keeps the region and site-group ancestor
  trail the template built by hand, and the location tab now shows its location ancestors,
  matching NetBox's own location view — the template checked for a region and a group, which
  a location does not have, so it never rendered anything extra there.

* **Removed two dead templates**, `floorplan.html` and `floorplan_list.html`. Neither was
  referenced from any view, URL or template: `Floorplan.get_absolute_url()` points at the
  editor, and no detail view is registered for the model.

* **Deprecated rack fields are no longer read directly.** `Rack.outer_width`,
  `outer_depth` and `outer_unit` are deprecated in NetBox 4.7 and are to be inferred from
  the rack's `RackType` in v5.0. The rack picker now resolves them from the `RackType`,
  falling back to the Rack's own fields, so it keeps working once the fields are removed.
  `rack_type` was added to the picker's `select_related()` to avoid a query per row.

* **`FloorplanImage.filename` is now annotated as returning `str`**, silencing
  drf-spectacular type-hint warnings emitted during OpenAPI schema generation.

* **Renamed the vendored Fabric.js build to match its actual version.** The file was named
  `fabric-js-6.0.2.js` but contained 5.2.1, which is materially misleading: Fabric v6 replaced
  every callback API this plugin depends on — `loadFromJSON(json, callback, reviver)`,
  `fabric.Image.fromURL(url, callback)`, `setBackgroundImage(img, callback, options)` — with
  promises, so anyone consulting v6 documentation to reason about the editor was working from
  the wrong API. It is now `fabric-js-5.2.1.js`, with the templates updated to match. No
  library code changed.

* **Removed `admin.py`.** NetBox has not included `django.contrib.admin` in
  `INSTALLED_APPS` for several releases, so the module was never loaded.

* Declared `python_requires=">=3.12"`, matching NetBox 4.7's supported Python versions.

* Removed the invalid `min_version` and `max_version` arguments from `setup.py`, which
  setuptools silently discarded. The supported NetBox range is declared in `PluginConfig`,
  which is where it takes effect.

* `netbox-plugin.yaml` backfilled with the 0.8.0, 0.9.0, 0.9.1 and 0.9.2 releases, which
  were missing from the published compatibility manifest.

* Corrected the tests badge in the README, which pointed at a repository that no longer
  hosts this plugin.

### Housekeeping

* **Added a test suite** at `netbox_floorplan/tests/`, covering the models, the REST API,
  the views, the filterset, and the template filters. Run it with `make test`.

* **Added a development environment** under `develop/` — a Docker Compose stack of NetBox,
  a worker, PostgreSQL and Redis — driven by a new `Makefile`.

* **Added `CONTRIBUTING.md`**, documenting the development environment, the test workflow,
  the query-count baseline workflow, and the plugin's conventions.

* Documentation restructured into an MkDocs site.

* Fixed the `manifest-modified` workflow, which still triggered on pushes to `master` and
  so had stopped firing after the default branch was renamed to `main`.

---

## Earlier Releases

Releases prior to v0.10.0 predate this change log. See the
[GitHub releases page](https://github.com/netbox-community/netbox-floorplan-plugin/releases)
and the [compatibility matrix](https://github.com/netbox-community/netbox-floorplan-plugin/blob/main/COMPATIBILITY.md)
for their supported NetBox versions.
