# NetBox Floorplan Plugin

<img src="https://github.com/netbox-community/netbox-floorplan-plugin/actions/workflows/tests.yml/badge.svg" alt="Tests"/>

This [NetBox](http://netboxlabs.com/oss/netbox/) plugin provides floorplan mapping for sites and locations. Racks and unracked devices are drawn on a canvas, positioned to match the physical room, and clicked through to the objects they represent.

* Graphical placement of racks and unracked devices on a floorplan
* Metadata such as labels, areas, walls, and colouring
* A floorplan is assigned to a site or a location, with click-through to racks and devices
* Keyboard controls
* Export to SVG
* A background image per floorplan, uploaded or linked

See the [compatibility matrix](COMPATIBILITY.md) for supported NetBox versions, and the [changelog](CHANGELOG.md) for release notes.

> [!TIP]
> This plugin is compatible with [netbox-branching](https://github.com/netboxlabs/netbox-branching) out of the box. See [Branching](docs/branching.md) for three behaviours worth knowing before drawing floorplans inside branches.

> [!IMPORTANT]
> For racks to display at their true proportions, assign a rack type to the rack and set the outer width and depth on that type. Racks without those dimensions are drawn at a default size.

## Demo

![demo](media/demo.gif)

Advanced rack rendering, showing role colouring, status, and tenant:

![advanced racks](media/new-floorplan-demo.gif)

## Installation

Brief installation instructions are provided below. For a complete installation guide, please refer to the included [documentation](docs/installation.md).

1. Install the plugin from [PyPI](https://pypi.org/project/netbox-floorplan-plugin/):

```
$ pip install netbox-floorplan-plugin
```

2. Add `netbox_floorplan` to `PLUGINS` in `configuration.py`:

```python
PLUGINS = [
    # ...
    'netbox_floorplan',
]
```

3. Run the migrations and collect static files (paths may vary with your runtime environment):

```
$ cd /opt/netbox
$ sudo ./venv/bin/python3 netbox/manage.py migrate
$ sudo ./venv/bin/python3 netbox/manage.py collectstatic
```

4. Add `netbox-floorplan-plugin` to `local_requirements.txt` so the plugin survives future upgrades, then restart NetBox:

```
$ sudo systemctl restart netbox netbox-rq
```

## Documentation

* [Introduction](docs/index.md) — what the plugin does and how a floorplan is put together
* [Installation](docs/installation.md) — full installation guide
* [Drawing a Floorplan](docs/usage.md) — the canvas editor, keyboard controls, and export
* [Branching](docs/branching.md) — using floorplans with netbox-branching
* [Data Model](docs/models/floorplan.md) — Floorplan and Floorplan Image
* [REST API](docs/rest-api.md)
* [Change Log](CHANGELOG.md)

## Contributing

Issues and pull requests are welcomed. See [CONTRIBUTING.md](CONTRIBUTING.md) for the development environment and test workflow.

This repository follows the same two-branch model as NetBox itself:

* `feature` — active development of future releases. **Base your pull requests on this branch.**
* `main` — the released code. Releases are cut from here; `feature` is merged into `main` to release.

GitHub defaults the base branch to `main`, so remember to switch the base to `feature` when opening a pull request.

## Mentions

Originally forked from [tbotnz/netbox_floorplan](https://github.com/tbotnz/netbox_floorplan).

Special thanks to the Ziply Fiber network automation team for helping to conceive this during the NANOG hackathon.
