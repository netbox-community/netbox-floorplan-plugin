# Installation

Unlike many NetBox plugins, this one adds models, so installing it requires running migrations and collecting static files. It has no configuration parameters.

!!! note
    Check the [compatibility matrix](https://github.com/netbox-community/netbox-floorplan-plugin/blob/main/COMPATIBILITY.md) before installing, and choose a plugin release which supports your NetBox version.

## 1. Virtual Environment

The plugin is distributed on [PyPI](https://pypi.org/project/netbox-floorplan-plugin/). If NetBox was installed following the standard installation instructions, first activate its Python virtual environment (typically located at `/opt/netbox/venv/`):

```
source /opt/netbox/venv/bin/activate
```

!!! note
    You may need to modify the `source` command above if your virtual environment has been installed in a different location.

## 2. Python Package

Use `pip` to install the Python package:

```
pip install netbox-floorplan-plugin
```

The plugin declares no third-party dependencies; the canvas library is vendored with it.

## 3. Enable Plugin

Add `netbox_floorplan` to the `PLUGINS` list in `configuration.py`, which is normally located at `/opt/netbox/netbox/netbox/configuration.py`:

```python
PLUGINS = [
    # ...
    'netbox_floorplan',
]
```

!!! note
    If there are no plugins already installed, you might need to create this parameter. If so, be sure to define `PLUGINS` as a list _containing_ the plugin name as above, rather than just the name.

There is nothing to add to `PLUGINS_CONFIG` — the plugin has no settings.

## 4. Run Migrations

The plugin adds two models, so its migrations must be applied. Paths may vary with your runtime environment:

```
cd /opt/netbox
sudo ./venv/bin/python3 netbox/manage.py migrate
```

## 5. Collect Static Files

The canvas editor ships JavaScript, which must be collected so NetBox can serve it:

```
sudo ./venv/bin/python3 netbox/manage.py collectstatic
```

!!! warning
    Skipping this step leaves the floorplan editor unable to load its JavaScript, so the canvas will appear blank with errors in the browser console.

## 6. Persist the Installation

Add the package to `local_requirements.txt` so that it is reinstalled automatically when NetBox is upgraded:

```
echo netbox-floorplan-plugin >> /opt/netbox/local_requirements.txt
```

!!! warning
    Skipping this step means the plugin will be missing after the next NetBox upgrade, and NetBox will fail to start because `configuration.py` still references it.

## 7. Restart NetBox

Restart the NetBox services to load the plugin:

```
sudo systemctl restart netbox netbox-rq
```

A **Floor Plan** tab should now appear on site and location detail views, and a **Netbox Floorplan** section should appear in the Plugins menu.

## Upgrading

Upgrade the package, then re-run the migration and static file steps:

```
source /opt/netbox/venv/bin/activate
pip install --upgrade netbox-floorplan-plugin
cd /opt/netbox
sudo ./venv/bin/python3 netbox/manage.py migrate
sudo ./venv/bin/python3 netbox/manage.py collectstatic
sudo systemctl restart netbox netbox-rq
```

Existing floorplans are unaffected by upgrades: the canvas document is stored as JSON and is re-read against current NetBox data whenever a floorplan is viewed.

## Development Environment

A Docker Compose environment is included for plugin development. It builds NetBox from source and mounts the plugin in editable mode:

```
make cbuild
make debug
```

NetBox is then available at `http://localhost:8000`. Use `make adduser` to create a superuser, `make test` to run the test suite, and `make stop` to shut the environment down.

See [CONTRIBUTING.md](https://github.com/netbox-community/netbox-floorplan-plugin/blob/main/CONTRIBUTING.md) for the full development and test workflow, including the version override the dev stack needs while NetBox 4.7 is unreleased.
