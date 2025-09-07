// start initial ----------------------------------------------------------------------------- !


import {
    resize_canvas,
    export_svg,
    enable_button_selection,
    disable_button_selection,
    prevent_leaving_canvas,
    wheel_zoom,
    stop_pan,
    start_pan,
    move_pan,
    reset_zoom,
    init_floor_plan
} from "/static/netbox_floorplan/floorplan/utils.js";


var csrf = document.getElementById('csrf').value;
var obj_pk = document.getElementById('obj_pk').value;
var obj_name = document.getElementById('obj_name').value;
var record_type = document.getElementById('record_type').value;
var site_id = document.getElementById('site_id').value;
var location_id = document.getElementById('location_id').value;

htmx.ajax('GET', `/plugins/floorplan/floorplans/racks/?floorplan_id=${obj_pk}`, { source: '#rack-card', target: '#rack-card', swap: 'innerHTML', trigger: 'load' })
htmx.ajax('GET', `/plugins/floorplan/floorplans/devices/?floorplan_id=${obj_pk}`, { source: '#unrack-card', target: '#unrack-card', swap: 'innerHTML', trigger: 'load' })


fabric.Object.prototype.set({
    snapThreshold: 45,
    snapAngle: 45
});

var current_zoom = 1;

var canvas = new fabric.Canvas('canvas'),
    canvasWidth = document.getElementById('canvas').width,
    canvasHeight = document.getElementById('canvas').height;

// end initial ----------------------------------------------------------------------------- !


// start motion events ----------------------------------------------------------------------------- !

canvas.on({
    "selection:updated": enable_button_selection,
    "selection:created": enable_button_selection,
    "selection:cleared": disable_button_selection,
});

canvas.on('object:moving', function (opt) {
    prevent_leaving_canvas(opt, canvas);
});

// end motion events ----------------------------------------------------------------------------- !

// start grid ----------------------------------------------------------------------------- !
var grid = 8;

canvas.on('object:moving', function (options) {
    options.target.set({
        left: Math.round(options.target.left / grid) * grid,
        top: Math.round(options.target.top / grid) * grid
    });
});

// end grid ----------------------------------------------------------------------------- !

// start zoom, pan control & resizing ----------------------------------------------------------------------------- !

$(window).resize(resize_canvas(canvas, window));

canvas.on('mouse:wheel', function (opt) {
    wheel_zoom(opt, canvas);
});

canvas.on('mouse:down', function (opt) {
    start_pan(opt, canvas);
});

canvas.on('mouse:move', function (opt) {
    move_pan(opt, canvas);
});
canvas.on('mouse:up', function (opt) {
    stop_pan(canvas);
});

// start zoom, pan control & resizing ----------------------------------------------------------------------------- !

// start buttons ----------------------------------------------------------------------------- !

document.getElementById('reset_zoom').addEventListener('click', () => {
    reset_zoom(canvas);
});

document.getElementById('export_svg').addEventListener('click', () => {
    export_svg(canvas);
});

function add_wall() {
    var wall = new fabric.Rect({
        top: 0,
        left: 0,
        width: 10,
        height: 500,
        //fill: '#6ea8fe',
        fill: 'red',
        opacity: 0.8,
        lockRotation: false,
        originX: "center",
        originY: "center",
        cornerSize: 15,
        hasRotatingPoint: true,
        perPixelTargetFind: true,
        minScaleLimit: 1,
        maxWidth: canvasWidth,
        maxHeight: canvasHeight,
        centeredRotation: true,
        angle: 90,
        custom_meta: {
            "object_type": "wall",
        },
    });
    var group = new fabric.Group([wall]);

    group.setControlsVisibility({
        mt: true,
        mb: true,
        ml: true,
        mr: true,
        bl: false,
        br: false,
        tl: false,
        tr: false,
    })

    canvas.add(group);
    canvas.centerObject(group);
}
window.add_wall = add_wall;

function add_image() {
  let url = prompt('Please enter image URL');

  if(url==='' || url===null)
    return;

  fabric.Image.fromURL(url, function (img) {
    canvas.add(img);
    canvas.centerObject(img);
  });
}

window.add_image = add_image;

function add_area() {
    var wall = new fabric.Rect({
        top: 0,
        left: 0,
        width: 300,
        height: 300,
        fill: '#6ea8fe',
        opacity: 0.5,
        lockRotation: false,
        originX: "center",
        originY: "center",
        cornerSize: 15,
        hasRotatingPoint: true,
        perPixelTargetFind: true,
        minScaleLimit: 1,
        maxWidth: canvasWidth,
        maxHeight: canvasHeight,
        centeredRotation: true,
        angle: 90,
        custom_meta: {
            "object_type": "area",
        },
    });
    var group = new fabric.Group([wall]);

   group.setControlsVisibility({
        mt: true,
        mb: true,
        ml: true,
        mr: true,
        bl: false,
        br: false,
        tl: false,
        tr: false,
    })
    canvas.add(group);
    canvas.centerObject(group);
    canvas.requestRenderAll();
}
window.add_area = add_area;

/*
*  lock_floorplan_object: Toggle function to enable/disable movement and resize of objects
*  Uses object.custom_meta.object_type to determine which controls to enable/disable
*  for walls/area, mtr, mt, mb, ml, mr and movement/rotation are all enabled/disabled.
*  for racks, only mtr and movement/roatation are enabled/disabled.
*/
function lock_floorplan_object() {
    var object = canvas.getActiveObject();
    if (object) {
        if (object.lockMovementX) {
            object.set({
                'lockMovementX': false,
                'lockMovementY': false,
                'lockRotation': false
            });
            object.setControlsVisibility({
                mtr: true,
            });
            if ( object._objects[0].custom_meta.object_type === "wall" ||
            object._objects[0].custom_meta.object_type === "area" ) {
                object.setControlsVisibility({
                    mt: true,
                    mb: true,
                    ml: true,
                    mr: true,
                });
            };
        } else {
            object.set({
                'lockMovementX': true,
                'lockMovementY': true,
                'lockRotation': true
            });
            object.setControlsVisibility({
                mtr: false,
            });
            if ( object._objects[0].custom_meta.object_type === "wall" ||
                object._objects[0].custom_meta.object_type === "area" ) {
                object.setControlsVisibility({
                    mt: false,
                    mb: false,
                    ml: false,
                    mr: false,
                });
            };
        };
    };
    canvas.renderAll();
    return;
}
window.lock_floorplan_object = lock_floorplan_object;

function bring_forward() {
    var object = canvas.getActiveObject();
    if (object) {
        object.bringForward();
        canvas.renderAll();
    }
}
window.bring_forward = bring_forward;

function send_back() {
    var object = canvas.getActiveObject();
    if (object) {
        object.sendBackwards();
        canvas.renderAll();
    }
}
window.send_back = send_back;

function set_dimensions() {
    $('#control_unit_modal').modal('show');
}
function set_background() {
    $('#background_unit_modal').modal('show');
}

window.set_background = set_background;
window.set_dimensions = set_dimensions;

function add_text() {
    var object = new fabric.IText("Label", {
        fontFamily: "Courier New",
        left: 150,
        top: 100,
        fontSize: 12,
        textAlign: "left",
        fill: "#fff"
    });
    canvas.add(object);
    canvas.centerObject(object);
}
window.add_text = add_text;

function add_floorplan_object(top, left, width, height, unit, fill, rotation, object_id, object_name, object_type, status, image) {
    var object_width;
    var object_height;
    if ( !width || !height || !unit ){
        object_width = 60;
        object_height = 91;
    } else {
        var conversion_scale = 100;
        console.log("width: " + width)
        console.log("unit: " + unit)
        console.log("height: " + height)
        if (unit == "in") {
            var new_width = (width * 0.0254) * conversion_scale;
            var new_height = (height * 0.0254) * conversion_scale;
        } else {
            var new_width = (width / 1000) * conversion_scale;
            var new_height = (height / 1000) * conversion_scale;
        }
    
        object_width = parseFloat(new_width.toFixed(2));
        console.log(object_width)
        object_height = parseFloat(new_height.toFixed(2));
        console.log(object_height)
    }
    document.getElementById(`object_${object_type}_${object_id}`).remove();
    /* if we have an image, we display the text below, otherwise we display the text within */
    var rect, text_offset = 0;
    if (!image) {
        rect = new fabric.Rect({
            top: top,
            name: "rectangle",
            left: left,
            width: object_width,
            height: object_height,
            fill: fill,
            opacity: 0.8,
            lockRotation: false,
            originX: "center",
            originY: "center",
            cornerSize: 15,
            hasRotatingPoint: true,
            perPixelTargetFind: true,
            minScaleLimit: 1,
            maxWidth: canvasWidth,
            maxHeight: canvasHeight,
            centeredRotation: true,
            custom_meta: {
                "object_type": object_type,
                "object_id": object_id,
                "object_name": object_name,
                "object_url": "/dcim/" + object_type + "s/" + object_id + "/",
            },
        });
    } else {
        object_height = object_width;
        text_offset = object_height/2 + 4;
        rect = new fabric.Image(null, {
            top: top,
            name: "rectangle",
            left: left,
            width: object_width,
            height: object_height,
            opacity: 1,
            lockRotation: false,
            originX: "center",
            originY: "center",
            cornerSize: 15,
            hasRotatingPoint: true,
            perPixelTargetFind: true,
            minScaleLimit: 1,
            maxWidth: canvasWidth,
            maxHeight: canvasHeight,
            centeredRotation: true,
            shadow: new fabric.Shadow({
                color: "red",
                blur: 15,
            }),
            custom_meta: {
                "object_type": object_type,
                "object_id": object_id,
                "object_name": object_name,
                "object_url": "/dcim/" + object_type + "s/" + object_id + "/",
            },
        });
        rect.setSrc("/media/" + image, function(img){
            img.scaleX =  object_width / img.width;
            img.scaleY =  object_height / img.height;
            canvas.renderAll();
        });
    }

    var text = new fabric.Textbox(object_name, {
        fontFamily: "Courier New",
        fontSize: 16,
        splitByGrapheme: text_offset? null : true,
        fill: "#FFFF",
        width: object_width,
        textAlign: "center",
        originX: "center",
        originY: "center",
        left: left,
        top: top + text_offset,
        excludeFromExport: false,
        includeDefaultValues: true,
        centeredRotation: true,
        stroke: "#000",
        strokeWidth: 2,
        paintFirst: 'stroke',
        custom_meta: {
            "text_type": "name",
        }
    });

    var button = new fabric.IText(status, {
        fontFamily: "Courier New",
        fontSize: 13,
        fill: "#6ea8fe",
        borderColor: "6ea8fe",
        textAlign: "center",
        originX: "center",
        originY: "center",
        left: left,
        top: top + text_offset + 16,
        excludeFromExport: false,
        includeDefaultValues: true,
        centeredRotation: true,
        shadow: text_offset? new fabric.Shadow({
            color: '#FFF',
            blur: 1
        }) : null,
        custom_meta: {
            "text_type": "status",
        }
    });

    var group = new fabric.Group([rect, text, button]);
    group.custom_meta = {
        "object_type": object_type,
        "object_id": object_id,
        "object_name": object_name,
        "object_url": "/dcim/" + object_type + "s/" + object_id + "/",
    }
    group.setControlsVisibility({
        mt: false,
        mb: false,
        ml: false,
        mr: false,
        bl: false,
        br: false,
        tl: false,
        tr: false,
    })

    if (object_id) {
        group.set('id', object_id);
    }

    canvas.add(group);
    canvas.centerObject(group);
    //canvas.bringToFront(group);
}
window.add_floorplan_object = add_floorplan_object;

function delete_floorplan_object() {
    var object = canvas.getActiveObject();
    if (object) {
        canvas.remove(object);
        canvas.renderAll();
    }
    save_floorplan();
    setTimeout(() => {
        htmx.ajax('GET', `/plugins/floorplan/floorplans/racks/?floorplan_id=${obj_pk}`, { target: '#rack-card', swap: 'innerHTML' });
        htmx.ajax('GET', `/plugins/floorplan/floorplans/devices/?floorplan_id=${obj_pk}`, { target: '#unrack-card', swap: 'innerHTML' });
    }, 1500);
};
window.delete_floorplan_object = delete_floorplan_object;

function set_color(color) {
    var object = canvas.getActiveObject();
    if (object) {
        if (object.type == "i-text") {
            object.set('fill', color);
            canvas.renderAll();
            return;
        }
        object._objects[0].set('fill', color);
        canvas.renderAll();
        return;
    }
}
window.set_color = set_color;

function set_zoom(new_current_zoom) {
    current_zoom = new_current_zoom;
    canvas.setZoom(current_zoom);
    canvas.requestRenderAll()
    document.getElementById("zoom").value = current_zoom;
}
window.set_zoom = set_zoom;

function center_pan_on_slected_object() {
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

}
window.center_pan_on_slected_object = center_pan_on_slected_object;

// end buttons ----------------------------------------------------------------------------- !

// start set scale ----------------------------------------------------------------------------- !

function update_background() {
    var assigned_image = document.getElementById("id_assigned_image").value;
    if (assigned_image == "") { 
        assigned_image = null; 
        canvas.setBackgroundImage(null, canvas.renderAll.bind(canvas));
    }
    var floor_json = canvas.toJSON(["id", "text", "_controlsVisibility", "custom_meta", "lockMovementY", "lockMovementX", "evented", "selectable"]);





    $.ajax({
        type: "PATCH",
        url: `/api/plugins/floorplan/floorplans/${obj_pk}/`,
        dataType: "json",
        headers: {
            "X-CSRFToken": csrf,
            "Content-Type": "application/json"
        },
        data: JSON.stringify({
            "assigned_image": assigned_image,
            "canvas": floor_json
        }),
        error: function (err) {
            console.log(`Error: ${err}`);
        }
    }).done(function (floorplan) {
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
            $('#background_unit_modal').modal('hide');
    });
}

window.update_background = update_background;

function update_dimensions() {

    var width = document.getElementById("width_value").value;
    var height = document.getElementById("height_value").value;

    var measurement_unit = document.getElementById("measurement_unit").value;

    var conversion_scale = 100;
    if (measurement_unit == "ft") {
        var new_width = (width / 3.28) * conversion_scale;
        var new_height = (height / 3.28) * conversion_scale;
    } else {
        var new_width = width * conversion_scale;
        var new_height = height * conversion_scale;
    }

    var rounded_width = parseFloat(new_width.toFixed(2));
    var rounded_height = parseFloat(new_height.toFixed(2));

    var floor_json = canvas.toJSON(["id", "text", "_controlsVisibility", "custom_meta", "lockMovementY", "lockMovementX", "evented", "selectable"]);
    $.ajax({
        type: "PATCH",
        url: `/api/plugins/floorplan/floorplans/${obj_pk}/`,
        dataType: "json",
        headers: {
            "X-CSRFToken": csrf,
            "Content-Type": "application/json"
        },
        data: JSON.stringify({
            "width": rounded_width,
            "height": rounded_height,
            "measurement_unit": measurement_unit,
            "canvas": floor_json,
        }),
        error: function (err) {
            console.log(`Error: ${err}`);
        }
    }).done(function () {

        // set the boundry variables for zoom controls
        var center_x = rounded_width / 2;
        var center_y = rounded_height / 2;

        var rect_left = center_x;
        var rect_top = center_y;
        var rect_bottom = rounded_height;

        var rect = new fabric.Rect({
            top: rect_top,
            name: "rectangle",
            left: rect_left,
            width: rounded_width,
            height: rounded_height,
            fill: null,
            opacity: 1,
            stroke: "#6ea8fe",
            strokeWidth: 2,
            lockRotation: false,
            originX: "center",
            originY: "center",
            cornerSize: 15,
            hasRotatingPoint: true,
            perPixelTargetFind: true,
            minScaleLimit: 1,
            maxWidth: canvasWidth,
            maxHeight: canvasHeight,
            centeredRotation: true,
        });


        var text = new fabric.IText(`${obj_name}`, {
            fontFamily: "Courier New",
            fontSize: 16,
            fill: "#FFFF",
            textAlign: "center",
            originX: "center",
            originY: "center",
            left: rect_left,
            top: rect_bottom - 40,
            excludeFromExport: false,
            includeDefaultValues: true,
            centeredRotation: true,
        });

        var dimensions = new fabric.IText(`${width} ${measurement_unit} (width) x ${height} ${measurement_unit} (height)`, {
            fontFamily: "Courier New",
            fontSize: 8,
            fill: "#FFFF",
            textAlign: "center",
            originX: "center",
            originY: "center",
            left: rect_left,
            top: rect_bottom - 20,
            excludeFromExport: false,
            includeDefaultValues: true,
            centeredRotation: true,
        });

        // check if the canvas already has a floorplan boundry
        var current_angle = 0;
        canvas.getObjects().forEach(function (object) {
            if (object.custom_meta) {
                if (object.custom_meta.object_type == "floorplan_boundry") {
                    current_angle = object.angle;
                    canvas.remove(object);
                }
            }
        });

        var group = new fabric.Group([rect, text, dimensions]);
        group.angle = current_angle;
        group.lockMovementY = true;
        group.lockMovementX = true;
        group.selectable = false;
        group.evented = false;
        group.setControlsVisibility({
            mt: false,
            mb: false,
            ml: false,
            mr: false,
            bl: false,
            br: false,
            tl: false,
            tr: false,
        })
        group.set('custom_meta', {
            "object_type": "floorplan_boundry",
        });
        canvas.add(group);
        //canvas.setDimensions({ width: rounded_width, height: rounded_height }, { cssOnly: true });
        canvas.renderAll();
        save_floorplan();
        set_zoom(1);
        $('#control_unit_modal').modal('hide');
    });
};
window.update_dimensions = update_dimensions;

// end set scale ----------------------------------------------------------------------------- !

// start keyboard/mouse controls ----------------------------------------------------------------------------- !

function move_active_object(x, y) {
    var object = canvas.getActiveObject();
    if (object) {
        object.set({
            left: object.left + x,
            top: object.top + y
        });
        canvas.renderAll();
    }
}

function rotate_active_object(angle) {
    var object = canvas.getActiveObject();
    if (object) {
        object.rotate(object.angle + angle);
        canvas.renderAll();
    }
}

// key down events for object control
document.addEventListener('keydown', function (e) {
    // delete key
    if (e.keyCode == 46) {
        delete_floorplan_object();
    }
    // events for arrows to move active object
    if (e.keyCode == 37) {
        move_active_object(-5, 0);
    } else if (e.keyCode == 38) {
        move_active_object(0, -5);
    } else if (e.keyCode == 39) {
        move_active_object(5, 0);
    } else if (e.keyCode == 40) {
        move_active_object(0, 5);
    }
    // when shift and arrow is pressed, rotate active object
    if (e.shiftKey && e.keyCode == 37) {
        rotate_active_object(-45);
    } else if (e.shiftKey && e.keyCode == 39) {
        rotate_active_object(45);
    }
});


// end keyboard/mouse controls ----------------------------------------------------------------------------- !

// start save floorplan ----------------------------------------------------------------------------- !

function save_floorplan() {
    var floor_json = canvas.toJSON(["id", "text", "_controlsVisibility", "custom_meta", "lockMovementY", "lockMovementX", "evented", "selectable"]);
    $.ajax({
        type: "PATCH",
        url: `/api/plugins/floorplan/floorplans/${obj_pk}/`,
        dataType: "json",
        headers: {
            "X-CSRFToken": csrf,
            "Content-Type": "application/json"
        },
        data: JSON.stringify({
            "canvas": floor_json,
        }),
        error: function (err) {
            console.log(`Error: ${err}`);
        }
    });
}

function save_and_redirect() {
    var floor_json = canvas.toJSON(["id", "text", "_controlsVisibility", "custom_meta", "lockMovementY", "lockMovementX", "evented", "selectable"]);
    $.ajax({
        type: "PATCH",
        url: `/api/plugins/floorplan/floorplans/${obj_pk}/`,
        dataType: "json",
        headers: {
            "X-CSRFToken": csrf,
            "Content-Type": "application/json"
        },
        data: JSON.stringify({
            "canvas": floor_json,
        }),
        error: function (err) {
            console.log(`Error: ${err}`);
        }
    }).done(function () {
        if (record_type == "site") {
            window.location.href = `/dcim/sites/${site_id}/floorplans/`;
        } else {
            window.location.href = `/dcim/locations/${location_id}/floorplans/`;
        }
    });
}



window.save_and_redirect = save_and_redirect;
// end save floorplan ----------------------------------------------------------------------------- !

// start initialize load ----------------------------------------------------------------------------- !
document.addEventListener("DOMContentLoaded", init_floor_plan(obj_pk, canvas, "edit"));
// end initialize load ----------------------------------------------------------------------------- !
