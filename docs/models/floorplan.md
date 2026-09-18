# Floorplan

A floorplan is the canvas for one site or one location, holding the position and appearance of the racks and devices drawn on it.

## Fields

### Site

The site this floorplan belongs to. Exactly one of Site or Location must be set.

### Location

The location this floorplan belongs to. Exactly one of Site or Location must be set.

!!! warning
    Setting both, or neither, is rejected. The rule is enforced both when validating a form or REST API request and again on save, so an invalid floorplan cannot reach the database.

### Assigned Image

An optional [Floorplan Image](floorplanimage.md) used as the canvas background. Clearing the image leaves the floorplan intact.

### Width

The physical width of the room, as a decimal. Interpreted in the unit given by Measurement Unit.

### Height

The physical height of the room, as a decimal. Interpreted in the unit given by Measurement Unit.

### Measurement Unit

The unit the width and height are expressed in.

| Value | Meaning |
|---|---|
| `m` | Metres (default) |
| `ft` | Feet |

### Canvas

The serialised drawing, stored as a JSON document. It is produced and consumed by [Fabric.js](http://fabricjs.com/) in the browser, and is not intended to be authored by hand.

Each placed rack or device is a group carrying `custom_meta` which identifies the NetBox object it represents:

```json
{
  "objects": [
    {
      "custom_meta": {
        "object_type": "rack",
        "object_id": "12",
        "object_name": "rack-1"
      },
      "objects": [
        {"type": "rect", "fill": "#000000", "custom_meta": {"object_type": "rack", "object_id": "12"}},
        {"type": "i-text", "text": "rack-1", "custom_meta": {"text_type": "name"}},
        {"type": "i-text", "text": "active", "custom_meta": {"text_type": "status"}}
      ]
    }
  ]
}
```

The `text_type` on a label determines how it is refreshed:

| `text_type` | Content |
|---|---|
| `name` | The object's name |
| `status` | The object's status (simple mode) |
| `info` | Status, role, and tenant combined (advanced mode) |

!!! note
    A `manual_color` flag on a group's `custom_meta` suppresses automatic role colouring, so a hand-picked colour is not overwritten on the next view.

## Properties

### `record_type`

Returns `site` or `location`, according to which is assigned.

### `mapped_racks`

The IDs of the racks currently placed on the canvas. Used to exclude them from the picker in the editor.

### `mapped_devices`

The IDs of the devices currently placed on the canvas.

## Behaviour

### `resync_canvas()`

Called whenever a floorplan is viewed or edited. It reconciles the canvas against current NetBox data:

* Updates the stored name of each placed rack and device, and the text of its `name` label.
* Rebuilds `info` labels from the object's current status, role, and tenant, honouring the per-label `show_status`, `show_role` and `show_tenant` flags.
* Reapplies role colouring to advanced racks, unless `manual_color` is set.
* Removes any placed object whose rack or device no longer exists.

The floorplan is saved only if something actually changed.

### Absolute URL

`get_absolute_url()` returns the canvas editor, not a read-only detail view — this plugin has no generic detail view for a floorplan.

## Permissions

Standard NetBox object permissions apply: `netbox_floorplan.view_floorplan`, `add_floorplan`, `change_floorplan`, and `delete_floorplan`.

Viewing the **Floor Plan** tab on a site or location additionally requires the relevant `dcim.view_site` or `dcim.view_location` permission.
