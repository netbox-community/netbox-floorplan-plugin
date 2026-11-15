# Drawing a Floorplan

A floorplan belongs to a site or a location, and is reached from the **Floor Plan** tab on that object rather than from a top-level menu.

## Creating a Floorplan

1. Open a site or location detail view.
2. Select the **Floor Plan** tab.
3. Choose **Add**.

The floorplan is created immediately and you are taken straight to the canvas editor — there is no create form. A site or location may have only one floorplan.

## Setting the Dimensions

Set the physical width and height of the room, and the unit (metres or feet), using **Set dimensions**. The canvas is scaled from these values, so setting them before placing objects saves rescaling later.

Dimensions may be changed at any time with **Update dimensions**.

## Adding a Background Image

A background image is useful for tracing an existing architectural drawing. Images are managed as separate [Floorplan Image](models/floorplanimage.md) objects, so one image can be reused across floorplans:

1. Create the image under **Plugins → Netbox Floorplan → Floorplan Images**, either uploading a file or giving an external URL.
2. In the editor, choose **Set background** and select it.

Use **Update background** to change or clear it later.

!!! tip
    Keep uploaded images modest in size. The background is served to every viewer of the floorplan, and a multi-megabyte scan will make the editor sluggish.

## Placing Racks and Devices

The editor lists the racks and unracked devices belonging to the floorplan's site or location, excluding any already placed. Each row offers two buttons:

* **Simple** — draws the object with its name and status.
* **Advanced** — additionally draws the role name, the tenant, and colours the object by its role colour.

Racks are drawn to scale from the outer width and depth of their assigned rack type. See [Rack Dimensions](index.md#rack-dimensions).

!!! note
    Only *unracked* devices are offered. A device mounted in a rack is represented by the rack it sits in.

## Annotation

Three annotation tools are available alongside the placed objects:

| Tool | Purpose |
|---|---|
| **Add text** | A free-form text label |
| **Add area** | A filled rectangle, for rooms, zones, or cages |
| **Add wall** | A line, for walls and partitions |

Areas and walls sit behind or in front of other objects depending on their stacking order — use **Bring forward** and **Send back** to adjust.

## Keyboard Controls

With an object selected:

| Key | Action |
|---|---|
| <kbd>←</kbd> <kbd>→</kbd> <kbd>↑</kbd> <kbd>↓</kbd> | Move the object by 5 units |
| <kbd>Shift</kbd> + <kbd>←</kbd> | Rotate 45° anticlockwise |
| <kbd>Shift</kbd> + <kbd>→</kbd> | Rotate 45° clockwise |
| <kbd>Delete</kbd> | Remove the object from the floorplan |

Deleting a placed object removes it from the drawing only. The rack or device itself is untouched, and becomes available in the picker again.

## Locking and Navigation

* **Lock** fixes an object in place so it cannot be dragged or resized accidentally. Useful for walls and areas once the outline is right.
* **Center on selected object** pans the canvas to the current selection, which helps on large floorplans.
* **Zoom** with the mouse wheel or the slider, and pan by dragging with <kbd>Alt</kbd> held. The slider is relative to the fitted view: 0 shows the whole floorplan, and each step doubles or halves the zoom. **Reset Zoom** returns to the fitted view.

## Saved View

By default the Floor Plan tab fits the whole floorplan into the page. To show a particular part instead, zoom and pan the editor to it, then choose **Use as View** and **Save**. The Floor Plan tab and **Reset Zoom** then fit that area.

The view is stored as an area of the drawing, not as a zoom level or a canvas size, so it shows the same part of the floorplan on any screen, scaled to fit the page. **Clear View** goes back to fitting the whole floorplan.

## Saving

Changes are held in the browser until you **Save**. Saving serialises the canvas to JSON and stores it on the floorplan, then returns you to the object view.

!!! warning
    Navigating away without saving discards the changes.

## Exporting

**Export SVG** downloads the current drawing as a vector image, from both the editor and the read-only view. The export is a snapshot: it does not stay in step with NetBox.

## Keeping in Step with NetBox

Each time a floorplan is viewed, the placed objects are reconciled against NetBox:

* Renamed racks and devices have their labels updated.
* Status, role, and tenant labels on advanced objects are refreshed.
* Role colouring is reapplied, unless the colour was set by hand.
* Objects whose rack or device has been deleted are removed from the drawing.

This means the drawing does not drift from the source of truth, and no manual refresh is needed after changes elsewhere in NetBox.
