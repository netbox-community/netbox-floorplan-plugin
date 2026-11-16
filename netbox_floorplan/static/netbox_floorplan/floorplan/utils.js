export {
    resize_canvas,
    export_svg,
    enable_button_selection,
    disable_button_selection,
    updateColorPickers,
    prevent_leaving_canvas,
    wheel_zoom,
    reset_zoom,
    fit_to_objects,
    visible_scene_rect,
    center_on_object,
    set_relative_zoom,
    relative_zoom,
    handle_window_resize,
    stop_pan,
    start_pan,
    move_pan,
    init_floor_plan,
    floorplan_image_url,
    apply_background,
    canvas_to_json,
    is_itext,
    is_text
};

// Properties that must survive serialisation. Fabric 7's canvas.toJSON() takes no arguments and
// drops them; toObject() is the call that honours the list. models.py depends on custom_meta
// to reconcile racks and devices, so losing it silently unlinks every placed object.
const CANVAS_PROPS = ["id", "text", "_controlsVisibility", "custom_meta", "lockMovementY", "lockMovementX", "evented", "selectable"];

function canvas_to_json(canvas) {
    const doc = canvas.toObject(CANVAS_PROPS);
    // The saved view is a property of the floorplan, not of any object, so it is kept at the
    // top level of the document. resync_canvas() only rewrites "objects" and leaves it alone.
    if (canvas.saved_view) {
        doc.saved_view = canvas.saved_view;
    }
    return doc;
}

// A saved view as stored in the document: a rectangle in scene coordinates. Anything else
// (missing, hand-edited, from a newer version) is ignored and the floorplan fits as usual.
function valid_view(view) {
    if (!view || typeof view !== "object") {
        return null;
    }
    const keys = ["left", "top", "width", "height"];
    if (!keys.every((key) => typeof view[key] === "number" && isFinite(view[key]))) {
        return null;
    }
    if (view.width <= 0 || view.height <= 0) {
        return null;
    }
    return { left: view.left, top: view.top, width: view.width, height: view.height };
}


// Fabric 7 keeps reporting the Fabric 5 spellings from object.type ("i-text", "textbox") even
// though it serialises the class name ("IText"), so test the in-memory type, not the stored one.
function is_itext(object) {
    return object.type === "i-text";
}

function is_text(object) {
    return is_itext(object) || object.type === "textbox";
}


// Viewport ------------------------------------------------------------------------------------
//
// The drawing is stored in scene coordinates; what is visible is decided by the canvas size and
// the viewport transform alone. Everything here computes the transform from scratch rather than
// panning relative to whatever it was before, so the result does not depend on earlier zooming.

// Margin kept around the drawing when it is fitted, as a fraction of the canvas on each side.
const FIT_MARGIN = 0.03;
// Margin when centring on a single object, which should keep some surroundings in view.
const OBJECT_FIT_MARGIN = 0.3;
const MIN_ZOOM = 0.01;
const MAX_ZOOM = 20;
// Smallest canvas height, so a short window or a floorplan far down the page stays usable.
const MIN_CANVAS_HEIGHT = 400;
// Space kept free below the canvas, so it ends above the bottom of the window.
const CANVAS_BOTTOM_GAP = 24;

function clamp_zoom(zoom) {
    return Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoom));
}

function find_boundary(canvas) {
    return canvas.getObjects().find(
        (object) => object.custom_meta && object.custom_meta.object_type == "floorplan_boundry"
    );
}

// Axis-aligned bounds of objects in scene coordinates, or null if there is nothing to measure.
// Fabric 7's getBoundingRect() works in scene coordinates, independent of the viewport.
function scene_bounds(objects) {
    let left = Infinity, top = Infinity, right = -Infinity, bottom = -Infinity;
    objects.forEach((object) => {
        object.setCoords();
        const rect = object.getBoundingRect();
        left = Math.min(left, rect.left);
        top = Math.min(top, rect.top);
        right = Math.max(right, rect.left + rect.width);
        bottom = Math.max(bottom, rect.top + rect.height);
    });
    if (!isFinite(left) || right <= left || bottom <= top) {
        return null;
    }
    return { left: left, top: top, width: right - left, height: bottom - top };
}

// What a reset fits to: the saved view if there is one, otherwise the floorplan boundary, or
// every object if no dimensions are set yet, or the background image if there is nothing else
// (a floorplan that is only a background).
function drawing_bounds(canvas) {
    if (canvas.saved_view) {
        return canvas.saved_view;
    }
    const boundary = find_boundary(canvas);
    if (boundary) {
        return scene_bounds([boundary]);
    }
    if (canvas.getObjects().length) {
        return scene_bounds(canvas.getObjects());
    }
    return canvas.backgroundImage ? scene_bounds([canvas.backgroundImage]) : null;
}

// The part of the drawing currently visible, in scene coordinates.
function visible_scene_rect(canvas) {
    const vpt = canvas.viewportTransform;
    const zoom = vpt[0];
    const round = (value) => Math.round(value * 100) / 100;
    return {
        left: round(-vpt[4] / zoom),
        top: round(-vpt[5] / zoom),
        width: round(canvas.getWidth() / zoom),
        height: round(canvas.getHeight() / zoom)
    };
}

function notify_viewport(canvas) {
    canvas.fire("viewport:changed", { zoom: canvas.getZoom() });
}

// Size the canvas to the element it sits in: the full content width, and the height that is
// left in the window below the canvas's position on the page. With fit_height set (the
// read-only view), the height is further limited to what the drawing needs at full width, so
// a wide floorplan does not leave a tall empty canvas under it.
function resize_canvas(canvas, options) {
    const fit_height = Boolean(options && options.fit_height);
    const container = canvas.wrapperEl.parentElement;
    const style = window.getComputedStyle(container);
    // The canvas element has a 1px border on each side, which sits outside the canvas size.
    const border = 2;
    const width = Math.max(
        1,
        Math.floor(container.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight)) - border
    );

    const page_top = container.getBoundingClientRect().top + window.scrollY;
    let height = Math.max(MIN_CANVAS_HEIGHT, window.innerHeight - page_top - CANVAS_BOTTOM_GAP - border);

    if (fit_height) {
        const bounds = drawing_bounds(canvas);
        if (bounds) {
            height = Math.min(height, Math.ceil(width * bounds.height / bounds.width));
        }
    }

    canvas.setDimensions({ width: width, height: height });
    canvas.requestRenderAll();
}

// Zoom and pan so that the given objects fill the canvas, centred, with a margin. Returns the
// zoom it set, or null if the objects have no measurable size.
function fit_to_objects(canvas, objects, margin) {
    return fit_to_bounds(canvas, scene_bounds(objects), margin);
}

// Zoom and pan so that a scene rectangle fills the canvas, centred, with a margin.
function fit_to_bounds(canvas, bounds, margin) {
    if (!bounds) {
        return null;
    }
    const fraction = 1 - 2 * (margin === undefined ? FIT_MARGIN : margin);
    const zoom = clamp_zoom(Math.min(
        canvas.getWidth() * fraction / bounds.width,
        canvas.getHeight() * fraction / bounds.height
    ));
    const center_x = bounds.left + bounds.width / 2;
    const center_y = bounds.top + bounds.height / 2;
    canvas.setViewportTransform([
        zoom, 0, 0, zoom,
        canvas.getWidth() / 2 - center_x * zoom,
        canvas.getHeight() / 2 - center_y * zoom
    ]);
    notify_viewport(canvas);
    return zoom;
}

// Show the saved view, or the whole floorplan. The zoom this produces is the reference for the
// editor's zoom slider, and until the user zooms or pans again the drawing is refitted on window
// resize. A saved view is fitted without a margin: it is exactly the area that was chosen.
function reset_zoom(canvas) {
    const zoom = fit_to_bounds(canvas, drawing_bounds(canvas), canvas.saved_view ? 0 : FIT_MARGIN);
    if (zoom === null) {
        canvas.setViewportTransform([1, 0, 0, 1, 0, 0]);
        notify_viewport(canvas);
    }
    canvas.fit_zoom = zoom || 1;
    canvas.user_viewport = false;
    // Again, now that fit_zoom is the new reference: listeners such as the zoom slider read it.
    notify_viewport(canvas);
}

// Zoom to one object, keeping some of the floorplan around it in view.
function center_on_object(canvas, object) {
    if (object && fit_to_objects(canvas, [object], OBJECT_FIT_MARGIN) !== null) {
        canvas.user_viewport = true;
    }
}

// Zoom as a power of two of the fitted zoom: 0 shows the whole floorplan, 1 is twice as close.
// Keeps the point at the centre of the canvas where it is.
function relative_zoom(canvas) {
    return Math.log2(canvas.getZoom() / (canvas.fit_zoom || 1));
}

function set_relative_zoom(canvas, level) {
    const zoom = clamp_zoom((canvas.fit_zoom || 1) * Math.pow(2, level));
    canvas.zoomToPoint(new fabric.Point(canvas.getWidth() / 2, canvas.getHeight() / 2), zoom);
    canvas.user_viewport = true;
    notify_viewport(canvas);
}

// Resize to the new window. An untouched view is refitted; a view the user has zoomed or
// panned keeps the same scene point at the centre of the canvas.
function handle_window_resize(canvas, options) {
    const old_width = canvas.getWidth();
    const old_height = canvas.getHeight();
    resize_canvas(canvas, options);
    if (!canvas.user_viewport) {
        reset_zoom(canvas);
        return;
    }
    const vpt = canvas.viewportTransform.slice();
    vpt[4] += (canvas.getWidth() - old_width) / 2;
    vpt[5] += (canvas.getHeight() - old_height) / 2;
    canvas.setViewportTransform(vpt);
    notify_viewport(canvas);
}

function export_svg(canvas) {
    var filedata = canvas.toSVG();
    var locfile = new Blob([filedata], { type: "image/svg+xml;charset=utf-8" });
    var locfilesrc = URL.createObjectURL(locfile);
    var link = document.createElement('a');
    link.style.display = 'none';
    link.href = locfilesrc;
    link.download = "floorplan.svg";
    link.click();
    // Clean up the URL object to prevent memory leaks
    setTimeout(function() {
        URL.revokeObjectURL(locfilesrc);
    }, 100);
}

function enable_button_selection() {
    // Get current colors from selected object and update color pickers
    updateColorPickers();
    $(".tools").removeClass("disabled");
    
    // Update text visibility controls. Needed when rack or device is selected
    // to make function exists before calling it
    if (typeof window.update_text_visibility_controls === 'function') {
        window.update_text_visibility_controls();
    }
}

function updateColorPickers() {
    var canvas = window.canvas;
    if (!canvas) {
        return;
    }
    
    var object = canvas.getActiveObject();
    var objectColor = "#000000"; // Default
    var textColor = "#6EA8FE"; // Default
    
    if (object) {
        // For single text objects
        if (is_text(object)) {
            objectColor = textColor = object.fill || "#000000";
        }
        // For groups (like racks/devices)
        else if (object._objects) {
            // Get object color from first object (usually the rectangle)
            if (object._objects[0]) {
                objectColor = object._objects[0].fill || "#000000";
            }
            
            // Get text color from first text object found
            for (var i = 0; i < object._objects.length; i++) {
                if (is_text(object._objects[i])) {
                    textColor = object._objects[i].fill || "#6EA8FE";
                    break;
                }
            }
        }
    }

    // Convert colors to hex format using Fabric.js Color class
    try {
        objectColor = "#" + new fabric.Color(objectColor).toHex();
    } catch (e) {
        objectColor = "#000000"; // Fallback to default
    }
    
    try {
        textColor = "#" + new fabric.Color(textColor).toHex();
    } catch (e) {
        textColor = "#6EA8FE"; // Fallback to default
    }

    // Update color picker values
    document.getElementById("selected_color").value = objectColor;
    document.getElementById("selected_text_color").value = textColor;
}

function disable_button_selection() {
    // set color to default
    document.getElementById("selected_color").value = "#000000"; // Default color black
    document.getElementById("selected_text_color").value = "#6EA8FE"; // Default color blue
    $(".tools").addClass("disabled");
    
    // Update text visibility controls. Needed when rack or device is selected
    // to make function exists before calling it
    if (typeof window.update_text_visibility_controls === 'function') {
        window.update_text_visibility_controls();
    }
}

// Keep a moved object inside the floorplan boundary. Both rectangles are in scene coordinates,
// so this holds at any zoom or pan; comparing against the canvas size in screen pixels, as
// before, pushed objects around as soon as the view was zoomed. Without a boundary (no
// dimensions set yet) objects move freely, and an object larger than the boundary is left alone.
function prevent_leaving_canvas(e, canvas) {
    const obj = e.target;
    const boundary = find_boundary(obj.canvas);
    if (!boundary || obj === boundary) {
        return;
    }
    const area = scene_bounds([boundary]);
    obj.setCoords();
    const rect = obj.getBoundingRect();
    if (!area || rect.width > area.width || rect.height > area.height) {
        return;
    }
    let dx = 0, dy = 0;
    if (rect.left < area.left) {
        dx = area.left - rect.left;
    } else if (rect.left + rect.width > area.left + area.width) {
        dx = area.left + area.width - (rect.left + rect.width);
    }
    if (rect.top < area.top) {
        dy = area.top - rect.top;
    } else if (rect.top + rect.height > area.top + area.height) {
        dy = area.top + area.height - (rect.top + rect.height);
    }
    if (dx || dy) {
        obj.set({ left: obj.left + dx, top: obj.top + dy });
        obj.setCoords();
    }
};


function wheel_zoom(opt, canvas) {
    var delta = opt.e.deltaY;
    var zoom = canvas.getZoom();
    zoom = clamp_zoom(zoom * 0.999 ** delta);
    canvas.zoomToPoint(new fabric.Point(opt.e.offsetX, opt.e.offsetY), zoom);
    canvas.user_viewport = true;
    notify_viewport(canvas);
    opt.e.preventDefault();
    opt.e.stopPropagation();
}

function stop_pan(canvas) {
    canvas.setViewportTransform(canvas.viewportTransform);
    canvas.isDragging = false;
    canvas.selection = true;
}

function start_pan(opt, canvas) {
    var evt = opt.e;
    if (evt.altKey === true) {
        canvas.isDragging = true;
        canvas.selection = false;
        canvas.lastPosX = evt.clientX;
        canvas.lastPosY = evt.clientY;
    }
}

function move_pan(opt, canvas) {
    if (canvas.isDragging) {
        var e = opt.e;
        var vpt = canvas.viewportTransform;
        vpt[4] += e.clientX - canvas.lastPosX;
        vpt[5] += e.clientY - canvas.lastPosY;
        canvas.setViewportTransform(vpt);
        canvas.user_viewport = true;
        canvas.lastPosX = e.clientX;
        canvas.lastPosY = e.clientY;
    }
}




// NetBox's MEDIA_URL, published by the floorplan templates from Django settings. The literal
// is only a fallback for a page that did not set it.
const MEDIA_URL = (typeof window !== "undefined" && window.NETBOX_MEDIA_URL) || "/media/";


// Rewrite absolute media URLs in a stored canvas document to root-relative paths, so that
// floorplans saved before this fix still load when NetBox is reached through a different
// hostname than the one that saved them (a reverse proxy, for example).
//
// Only URLs whose path sits under MEDIA_URL are touched, and only the host is removed, so an
// externally-hosted background image is left exactly as it is. Device images are always
// loaded from MEDIA_URL, so this cannot affect remote storage.
//
// Operates on the parsed document before Fabric sees it, which keeps it a pure data
// transform: idempotent, and unable to interfere with rendering.
function normalize_media_urls(node, media_url) {
    // With remote storage MEDIA_URL is itself absolute, so there is no same-origin media path
    // to normalise and every stored URL is already correct. Nothing to do.
    if (!media_url || /^https?:\/\//i.test(media_url)) {
        return node;
    }

    if (node === null || typeof node !== "object") {
        return node;
    }

    if (Array.isArray(node)) {
        node.forEach((item) => normalize_media_urls(item, media_url));
        return node;
    }

    if (typeof node.src === "string" && /^https?:\/\//i.test(node.src)) {
        try {
            const parsed = new URL(node.src);
            if (parsed.pathname.startsWith(media_url)) {
                node.src = parsed.pathname + parsed.search;
            }
        } catch (e) {
            // Not a URL we can parse; leave it untouched.
        }
    }

    Object.values(node).forEach((value) => normalize_media_urls(value, media_url));
    return node;
}


// The URL to load a floorplan image from. Prefers file_url, which the API renders using the
// storage backend (MEDIA_URL-relative for local storage, absolute for S3 or a CDN), and so
// works both behind a reverse proxy and with remote storage. Falls back to file for
// compatibility with older API responses.
function floorplan_image_url(assigned_image) {
    if (assigned_image.external_url !== "") {
        return assigned_image.external_url;
    }
    return assigned_image.file_url || assigned_image.file;
}


// Fit the assigned background image to the floorplan.
//
// Must be called once the canvas is fully populated. The floorplan boundary is one of the
// canvas objects, and the background is scaled and positioned to it; if the boundary cannot
// be found the background is instead scaled to the canvas and centred, which does not line up
// with the placed objects. Calling this from loadFromJSON's reviver — which runs per object,
// before loadFromJSON has added anything to the canvas — is what caused placed objects to
// appear shifted or compressed after a reload.
function apply_background(canvas, floorplan, done) {
    const finish = () => { if (done) { done(); } };

    if (floorplan.assigned_image == null) {
        canvas.backgroundImage = undefined;
        canvas.requestRenderAll();
        finish();
        return;
    }

    fabric.FabricImage.fromURL(floorplan_image_url(floorplan.assigned_image)).then(function (img) {
        const boundary = canvas.getObjects().find(
            (object) => object.custom_meta
                && object.custom_meta.object_type == "floorplan_boundry"
        );

        // Fabric 7 defaults every object to a centred origin; the boundary-fitted background is
        // positioned by its top-left corner, so say so.
        if (boundary && boundary.width && boundary.height) {
            const corner = boundary.getPointByOrigin('left', 'top');
            img.set({
                scaleX: boundary.width / img.width,
                scaleY: boundary.height / img.height,
                left: corner.x,
                top: corner.y,
                originX: 'left',
                originY: 'top'
            });
        } else {
            const scale = Math.max(canvas.width / img.width, canvas.height / img.height);
            img.set({
                scaleX: scale,
                scaleY: scale,
                left: canvas.width / 2,
                top: canvas.height / 2,
                originX: 'center',
                originY: 'center'
            });
        }

        canvas.backgroundImage = img;
        canvas.requestRenderAll();
        finish();
    });
}


function init_floor_plan(floorplan_id, canvas, mode) {

    if (floorplan_id === undefined || floorplan_id === null || floorplan_id === "") {
        return;
    }

    var target_image = 0;
    const floorplan_call = $.get(`/api/plugins/floorplan/floorplans/?id=${floorplan_id}`);
    floorplan_call.done(function (floorplan) {
        floorplan.results.forEach((floorplan) => {
            target_image = floorplan.assigned_image
            const canvas_json = normalize_media_urls(floorplan.canvas, MEDIA_URL);
            canvas.saved_view = valid_view(canvas_json && canvas_json.saved_view);
            canvas.loadFromJSON(
                JSON.stringify(canvas_json),
                // Reviver: called once per object, while the canvas is still empty.
                function (o, object) {
                    if (mode == "readonly") {
                        object.set('selectable', false);
                    }
                }
            ).then(function () {
                // Every object has been deserialised and added to the canvas, so the floorplan
                // boundary now exists and the background can be fitted to it.
                // Size the canvas before fitting: the fit depends on the canvas size, and fitting
                // first left the drawing scaled for a canvas that was then resized under it.
                apply_background(canvas, floorplan, function () {
                    resize_canvas(canvas, { fit_height: mode == "readonly" });
                    reset_zoom(canvas);
                    canvas.renderAll();
                });
            });
        });
    }).fail(function (jq_xhr, text_status, error_thrown) {
        console.log(`error: ${error_thrown} - ${text_status}`);
    });
};