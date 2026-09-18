# REST API

The plugin exposes both of its models through NetBox's REST API, under `/api/plugins/floorplan/`. Authentication, pagination, filtering, and the `?brief=1` parameter behave as they do elsewhere in NetBox.

## Endpoints

| Endpoint | Model |
|---|---|
| `/api/plugins/floorplan/floorplans/` | [Floorplan](models/floorplan.md) |
| `/api/plugins/floorplan/floorplanimages/` | [Floorplan Image](models/floorplanimage.md) |

## Floorplans

### Listing

```
GET /api/plugins/floorplan/floorplans/
```

Supported filters are `id`, `site`, `location`, and `q`. The `q` search matches the name of the assigned site or location.

```
GET /api/plugins/floorplan/floorplans/?site=3
GET /api/plugins/floorplan/floorplans/?q=amsterdam
```

### Creating

Exactly one of `site` or `location` must be given:

```
POST /api/plugins/floorplan/floorplans/
```

```json
{
  "site": 3,
  "width": "12.00",
  "height": "8.00",
  "measurement_unit": "m"
}
```

Supplying both `site` and `location`, or neither, returns `400` with the validation error against the object.

### The canvas field

`canvas` holds the serialised drawing. It is writable, but is produced by the browser-side editor and is not a documented interchange format — its structure is described in [Floorplan: Canvas](models/floorplan.md#canvas) for reference rather than as an API contract.

!!! warning
    Writing `canvas` directly is not recommended. A malformed document will not be rejected by the API, and may render as an empty or broken floorplan. Prefer the editor.

!!! note
    `canvas` can be large. Use `?brief=1` when listing floorplans if you only need to identify them.

## Floorplan Images

```
GET /api/plugins/floorplan/floorplanimages/
POST /api/plugins/floorplan/floorplanimages/
```

Exactly one of `file` or `external_url` must be set. Creating an image with an external URL is a plain JSON request:

```json
{
  "name": "Floor 2 architectural",
  "external_url": "https://files.example.com/floor2.png"
}
```

Uploading a file requires a `multipart/form-data` request rather than JSON.

The read-only `filename` field returns the base name of an uploaded file.

## Brief Representations

Appending `?brief=1` returns a reduced representation, as elsewhere in NetBox:

```
GET /api/plugins/floorplan/floorplans/?brief=1
```

```json
{
  "id": 1,
  "url": "https://netbox.example.com/api/plugins/floorplan/floorplans/1/",
  "display": "Amsterdam DC Floorplan"
}
```

!!! warning
    Before v0.10.0 the Floorplan serializer declared no brief fields, so `?brief=1` returned every field including the whole `canvas` document. Clients which relied on that behaviour should stop passing the parameter.

## GraphQL

The plugin does not register GraphQL types, so its models are not available through NetBox's GraphQL API.
