export {
    resize_canvas,
    export_svg,
    enable_button_selection,
    disable_button_selection,
    updateColorPickers,
    prevent_leaving_canvas,
    wheel_zoom,
    reset_zoom,
    stop_pan,
    start_pan,
    move_pan,
    init_floor_plan,
    floorplan_image_url
};


function resize_canvas(canvas, window) {
    var bob_width = $("#content-container").width();
    var window_width = $(window).width();
    window_width = Math.min(window_width, bob_width);
    var window_height = $(window).height();
    var canvas_width = window_width;
    var canvas_height = window_height - 100;
    canvas.setWidth(canvas_width);
    canvas.setHeight(canvas_height);
//    canvas.backgroundImage.scaleToWidth(canvas_width);
//    canvas.backgroundImage.scaleToHeight(canvas_height);
    canvas.renderAll();
}

function reset_zoom(canvas) {

    var objs = canvas.getObjects();
    for (var i = 0; i < objs.length; i++) {
        if (objs[i].custom_meta) {
            if (objs[i].custom_meta.object_type == "floorplan_boundry") {
                canvas.setActiveObject(objs[i]);
                let pan_x = 0
                let pan_y = 0
                let object = canvas.getActiveObject()
                let obj_wdth = object.getScaledWidth()
                let obj_hgt = object.getScaledHeight()
                let rect_cooords = object.getBoundingRect();
                let zoom_level = Math.min(canvas.width / rect_cooords.width, canvas.height / rect_cooords.height);

                canvas.setZoom(zoom_level * 0.7);
                let zoom = canvas.getZoom()
                pan_x = ((canvas.getWidth() / zoom / 2) - (object.aCoords.tl.x) - (obj_wdth / 2)) * zoom
                pan_y = ((canvas.getHeight() / zoom / 2) - (object.aCoords.tl.y) - (obj_hgt / 2)) * zoom
                pan_x = (canvas.getVpCenter().x - object.getCenterPoint().x) * zoom
                pan_y = ((canvas.getVpCenter().y - object.getCenterPoint().y) * zoom)
                canvas.relativePan({ x: pan_x, y: pan_y })
                canvas.requestRenderAll()
                canvas.discardActiveObject();
            }
        }
    }
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
        if (object.type === "i-text" || object.type === "textbox") {
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
                if (object._objects[i].type === "i-text" || object._objects[i].type === "textbox") {
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

function prevent_leaving_canvas(e, canvas) {
    var obj = e.target;
    obj.setCoords();
    var current_zoom = obj.canvas.getZoom();
    if (obj.getScaledHeight() > obj.canvas.height || obj.getScaledWidth() > obj.canvas.width) {
        return;
    }
    if (obj.getBoundingRect().top < 0 || obj.getBoundingRect().left < 0) {
        obj.top = Math.max(obj.top * current_zoom, obj.top * current_zoom - obj.getBoundingRect().top) / current_zoom;
        obj.left = Math.max(obj.left * current_zoom, obj.left * current_zoom - obj.getBoundingRect().left) / current_zoom;
    }
    if (obj.getBoundingRect().top + obj.getBoundingRect().height > obj.canvas.height || obj.getBoundingRect().left + obj.getBoundingRect().width > obj.canvas.width) {
        obj.top = Math.min(obj.top * current_zoom, obj.canvas.height - obj.getBoundingRect().height + obj.top * current_zoom - obj.getBoundingRect().top) / current_zoom;
        obj.left = Math.min(obj.left * current_zoom, obj.canvas.width - obj.getBoundingRect().width + obj.left * current_zoom - obj.getBoundingRect().left) / current_zoom;
    }
};


function wheel_zoom(opt, canvas) {
    var delta = opt.e.deltaY;
    var zoom = canvas.getZoom();
    zoom *= 0.999 ** delta;
    if (zoom > 20) zoom = 20;
    if (zoom < 0.01) zoom = 0.01;
    canvas.zoomToPoint({ x: opt.e.offsetX, y: opt.e.offsetY }, zoom);
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
        canvas.requestRenderAll();
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
        canvas.setBackgroundImage(null, canvas.renderAll.bind(canvas));
        finish();
        return;
    }

    fabric.Image.fromURL(floorplan_image_url(floorplan.assigned_image), function (img) {
        const boundary = canvas.getObjects().find(
            (object) => object.custom_meta
                && object.custom_meta.object_type == "floorplan_boundry"
        );

        if (boundary && boundary.width && boundary.height) {
            canvas.setBackgroundImage(img, canvas.renderAll.bind(canvas), {
                scaleX: boundary.width / img.width,
                scaleY: boundary.height / img.height,
                left: boundary.left,
                top: boundary.top
            });
        } else {
            const scale = Math.max(canvas.width / img.width, canvas.height / img.height);
            canvas.setBackgroundImage(img, canvas.renderAll.bind(canvas), {
                scaleX: scale,
                scaleY: scale,
                left: canvas.width / 2,
                top: canvas.height / 2,
                originX: 'middle',
                originY: 'middle'
            });
        }

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
            canvas.loadFromJSON(
                JSON.stringify(canvas_json),
                // Completion: every object has been deserialised and added to the canvas, so
                // the floorplan boundary now exists and the background can be fitted to it.
                function () {
                    apply_background(canvas, floorplan, function () {
                        reset_zoom(canvas);
                        resize_canvas(canvas, window);
                        canvas.renderAll();
                    });
                },
                // Reviver: called once per object, while the canvas is still empty.
                function (o, object) {
                    if (mode == "readonly") {
                        object.set('selectable', false);
                    }
                }
            );
        });
    }).fail(function (jq_xhr, text_status, error_thrown) {
        console.log(`error: ${error_thrown} - ${text_status}`);
    });
};