# Floorplan Image

A background image for a floorplan. Images are modelled separately from floorplans so that one image can be reused across several, and managed independently of the drawings that reference it.

Floorplan Images are listed under **Plugins → Netbox Floorplan → Floorplan Images**.

## Fields

### Name

A label used to identify the image when selecting a background. Required.

### File

An uploaded image, stored under `netbox-floorplan/` in NetBox's media directory.

### External URL

A URL referencing an image hosted elsewhere.

!!! warning
    Exactly one of File or External URL must be set. Supplying both, or neither, is rejected.

### Comments

Free-form notes, rendered as Markdown.

## Properties

### `filename`

The base name of the uploaded file, without its directory.

### `size`

The size of the uploaded file in bytes, or `None` when it cannot be determined.

An image which uses External URL has no file to measure, and one whose file is missing from storage cannot be read. Both cases return `None` rather than raising, so the detail view still renders.

## Behaviour

### Deletion

Deleting an image with an uploaded file removes the file from storage as well as the database record. Deleting an image which only carries an external URL removes just the record; the remote file is untouched.

A floorplan referencing a deleted image is not deleted with it — the reference is cleared and the floorplan keeps its drawing, losing only the background.

## Choosing Between a File and a URL

| | Upload | External URL |
|---|---|---|
| Availability | Served by NetBox, always available to viewers | Depends on the remote host being reachable from the browser |
| Storage | Consumes NetBox media storage | None |
| Backups | Included in NetBox media backups | Not covered |
| Best for | The common case | Images already published on an internal file server or wiki |

!!! tip
    Keep uploaded images modest in size. The background is transferred to every viewer of every floorplan that uses it, so a large architectural scan makes the editor noticeably slower. Downscale to roughly the pixel dimensions the canvas will display.

## Permissions

Standard NetBox object permissions apply: `netbox_floorplan.view_floorplanimage`, `add_floorplanimage`, `change_floorplanimage`, and `delete_floorplanimage`.
