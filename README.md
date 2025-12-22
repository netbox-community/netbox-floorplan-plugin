# NetBox Floorplan Plugin

<img src="https://github.com/netboxlabs/netbox-floorplan-plugin/workflows/tests/badge.svg" alt="Tests"/>

Originally Forked from https://github.com/tbotnz/netbox_floorplan

## Demo
![demo](/media/demo.gif)

## New Demo Showing New Plugin Behavior with Advanced Rack Behavior

![new-enhancements](/media/new-floorplan-demo.gif)

## Summary
A netbox plugin providing floorplan mapping capability for locations and sites

- provides graphical ability to draw racks & unracked devices on a floorplan
- support for metadata such as labels, areas, walls, coloring
- floorplan object mapped to sites or locations and click through rack/devices
- keyboard controls supported
- export to svg

## Compatibility

| NetBox Version | Plugin Version |
|-------------|-----------|
| 3.5         | >= 0.3.2  |
| 3.6         | >= 0.3.2  |
| 4.0.x       | 0.4.1     |
| 4.1.x       | 0.5.0     |
| 4.2.x       | 0.6.0     |
| 4.3.x       | 0.7.0     |
| 4.4.x       | 0.8.0     |
| 4.5.x       | 0.9.0     |

## Installing

The plugin is available as a Python package in pypi and can be installed with pip  


```
sudo pip install netbox-floorplan-plugin
```
Enable the plugin in /opt/netbox/netbox/netbox/configuration.py:
```
PLUGINS = ['netbox_floorplan']
```
Enable Migrations (note this may vary based on the NetBox runtime environment):
```
cd /opt/netbox
sudo ./venv/bin/python3 netbox/manage.py migrate
sudo ./venv/bin/python3 netbox/manage.py collectstatic
```

Restart NetBox and add `netbox-floorplan-plugin` to your local_requirements.txt

See [NetBox Documentation](https://docs.netbox.dev/en/stable/plugins/#installing-plugins) for details

>[!IMPORTANT]
>In order for racks to display properly, the rack type of the rack should be specified and a width/height set within the type. 

## Mentions

Forked from https://github.com/tbotnz/netbox_floorplan

Special thanks to Ziply Fiber network automation team for helping originally helping to conceive this during the NANOG hackathon

