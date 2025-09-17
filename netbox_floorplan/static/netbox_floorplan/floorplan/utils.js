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
    init_floor_plan
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




function init_floor_plan(floorplan_id, canvas, mode) {

    if (floorplan_id === undefined || floorplan_id === null || floorplan_id === "") {
        return;
    }

    var target_image = 0;
    const floorplan_call = $.get(`/api/plugins/floorplan/floorplans/?id=${floorplan_id}`);
    floorplan_call.done(function (floorplan) {
        floorplan.results.forEach((floorplan) => {
            target_image = floorplan.assigned_image
            canvas.loadFromJSON(JSON.stringify(floorplan.canvas), canvas.renderAll.bind(canvas), function (o, object) {
                if (mode == "readonly") {
                    object.set('selectable', false);
                }
                if (floorplan.assigned_image != null) {
                    var img_url = "";
                    if (floorplan.assigned_image.external_url != "") {
                        img_url = floorplan.assigned_image.external_url;
                    } else {
                        img_url = floorplan.assigned_image.file;
                    }


                    var img = fabric.Image.fromURL(img_url, function(img) {
                        var left = 0;
                        var top = 0;
                        var width = 0;
                        var height = 0;
                        canvas.getObjects().forEach(function (object) {
                            if (object.custom_meta) {
                                if (object.custom_meta.object_type == "floorplan_boundry") {
                                    left = object.left;
                                    top = object.top;
                                    width = object.width;
                                    height = object.height;
                                }
                            }
                        });
                        // if we have a floorplan boundary, position the image in there 
                        if (height != 0 && width != 0) {
                            let scaleRatioX = Math.max(width / img.width)
                            let scaleRatioY = Math.max(height / img.height);
                            canvas.setBackgroundImage(img, canvas.renderAll.bind(canvas), {
                                scaleX: scaleRatioX,
                                scaleY: scaleRatioY,
                                left: left,
                                top: top
                            });     
                        }
                         else
                        {
                            let scaleRatio = Math.max(canvas.width / img.width, canvas.height / img.height);
                            canvas.setBackgroundImage(img, canvas.renderAll.bind(canvas), {
                                scaleX: scaleRatio,
                                scaleY: scaleRatio,
                                left: canvas.width / 2,
                                top: canvas.height / 2,
                                originX: 'middle',
                                originY: 'middle'
                            });
                        }
                    });
                

                } else {
                    canvas.setBackgroundImage().renderAll();
                }
                canvas.renderAll();
            });
        });
        reset_zoom(canvas);
        resize_canvas(canvas, window);
    }).fail(function (jq_xhr, text_status, error_thrown) {
        console.log(`error: ${error_thrown} - ${text_status}`);
    });
};