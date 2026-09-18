# Branching

This plugin works with [netbox-branching](https://github.com/netboxlabs/netbox-branching) with no additional configuration. Both `Floorplan` and `FloorplanImage` inherit `NetBoxModel`, and therefore `ChangeLoggingMixin`, so both are branch-aware automatically: floorplans can be created, modified, and deleted inside a branch, and those changes merge into main along with everything else.

Nothing needs to be registered, and no resolver or validator has to be written.

There are, however, three behaviours specific to this plugin that are worth understanding before drawing floorplans inside branches. None of them prevent branching from working, but two can surprise you.

## Uploaded Images Are Not Branched

This is the most important caveat. A [Floorplan Image](models/floorplanimage.md) has two halves: a database row, which *is* branched, and an uploaded file in NetBox's media storage, which is **not**. Media storage is shared across all schemas.

The consequences:

* Uploading an image inside a branch writes the file to shared storage immediately. The file is readable from main and from every other branch, even though the database row is not.
* Deleting an image inside a branch deletes the file from storage immediately, because `FloorplanImage.delete()` removes it from disk as well as the database.
* **Reverting or discarding that branch restores the database row but not the file.** The row will point at a file that no longer exists.

netbox-branching tolerates this rather than failing: on merge it validates each replayed object with a file check that suppresses "file not found" and logs a warning, so a missing file does not abort the merge.

!!! warning
    Avoid deleting Floorplan Images inside a branch you might revert. Delete them from main, once you are certain, or use the External URL field instead of an upload — a URL is just a string, and is branched cleanly with the row.

## Viewing a Floorplan Can Produce a Change

Floorplans reconcile themselves against NetBox whenever they are viewed. `resync_canvas()` updates the stored labels of placed racks and devices, and removes objects whose rack or device no longer exists — and if anything changed, it saves the floorplan.

Inside a branch that is an ordinary branch-local write, which means it is recorded as an `ObjectChange` and will be merged. So a floorplan can appear in a branch's diff even though nobody edited it, simply because a rack was renamed and someone opened the drawing.

This is harmless, but it explains diffs that otherwise look inexplicable. It only happens when the underlying data actually drifted; opening an up-to-date floorplan writes nothing.

## Canvas Conflicts Are All Or Nothing

The whole drawing is stored as a single JSON document in the `canvas` field. netbox-branching detects conflicts per field, so two branches that both touch the same floorplan conflict on `canvas` as a whole — even if one moved a rack in the north-west corner and the other added a wall in the south-east.

There is no partial merge of a drawing. Resolve it by choosing one version and reapplying the other change by hand.

!!! tip
    Where two people need to work on the same room concurrently, sequence the work rather than branching it. Branching is a good fit for *adding* floorplans alongside other infrastructure changes, and a poor fit for collaborative editing of one drawing.

## Placed Object References Survive a Merge

The canvas stores the racks and devices it places by raw ID, inside the JSON document, rather than as foreign keys. That looks fragile — the database cannot rewrite an ID buried in a JSON blob — so it is worth stating plainly that it is safe.

netbox-branching preserves primary keys when replaying changes into main: a created object is deserialized with `pk` set to the ID it had in the branch. A floorplan created in a branch that places racks also created in that branch therefore still references the correct objects after the merge.

## Do Not Exempt This Plugin

`Floorplan` holds foreign keys to `dcim.Site` and `dcim.Location`, both of which are branch-aware. netbox-branching requires that any model referencing branch-aware data is itself branch-aware, so exempting the plugin breaks referential integrity between a branch and main.

```python
# Unsupported — will corrupt relations between branches and main
PLUGINS_CONFIG = {
    'netbox_branching': {
        'exempt_models': ['netbox_floorplan.*'],
    },
}
```

!!! warning
    This applies to `netbox_floorplan.floorplan` individually too, not just the wildcard. Exempting it alone is equally unsafe, because floorplans reference Sites and Locations that branches do track.

Exempting `netbox_floorplan.floorplanimage` on its own is less dangerous, since it references nothing branch-aware — but a `Floorplan` points at it, so a floorplan inside a branch could reference an image row that main cannot see. It is not recommended.

## Install Before Branching

As with any plugin, install or upgrade `netbox-floorplan-plugin` *before* creating branches where you can. Branches provisioned against an older schema do not receive new migrations automatically: they enter the **Pending Migrations** status and need the **Migrate** action before they can be activated or merged.

A branch created before the plugin was installed will not know about its models at all, though this generally will not impede the branch's other work.

## What Is Covered

| Concern | Status |
|---|---|
| `Floorplan` and `FloorplanImage` | Branch-aware automatically via `NetBoxModel` |
| Multi-table inheritance | Not used; both models are plain `NetBoxModel` subclasses |
| Data migrations | None. All 13 migrations are schema-only, so no `fake_on_branch` declaration is needed |
| Placed object IDs in `canvas` | Safe — primary keys are preserved when changes are replayed into main |
| `Floorplan.clean()` validation | Honoured; merge calls `full_clean()` on each replayed object |
| Custom `save()` side effects | Validation only, with no writes to other objects |
| Custom `delete()` side effects | **Deletes the uploaded file from shared storage** — see above |
| `resync_canvas()` writing on view | Produces a legitimate branch-local change — see above |
| Uploaded image files | **Not branched.** Media storage is shared across schemas |
| Many-to-many fields | Only `tags`, handled by netbox-branching |

For plugin developers, the corresponding requirement on the contributing side is that any new *data* migration must declare `fake_on_branch`. See [CONTRIBUTING.md](https://github.com/netbox-community/netbox-floorplan-plugin/blob/main/CONTRIBUTING.md#data-migrations-and-branching).
