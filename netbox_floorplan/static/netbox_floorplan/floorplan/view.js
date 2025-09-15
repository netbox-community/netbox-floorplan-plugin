import {
    resize_canvas,
    export_svg,
    wheel_zoom,
    stop_pan,
    move_pan,
    start_pan,
    reset_zoom,
    init_floor_plan
} from "/static/netbox_floorplan/floorplan/utils.js";

var canvas = new fabric.Canvas('canvas');

canvas.on('mouse:over', function (options) {
    if (options.target) {
        if (options.target.hasOwnProperty("custom_meta")) {
            options.target.hoverCursor = "pointer";
        }

    }
});

canvas.on('mouse:down', function (options) {
    if (options.target) {
        if (options.target.hasOwnProperty("custom_meta")) {
            window.location.href = options.target.custom_meta.object_url;
        }
    }
});

// start zoom, pan control & resizing ----------------------------------------------------------------------------- !

$(window).resize(function() {
    resize_canvas(canvas, window);
});

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

// end start zoom, pan control & resizing ----------------------------------------------------------------------------- !


document.getElementById('export_svg').addEventListener('click', () => {
    export_svg(canvas);
});


let floorplan_id = document.getElementById('floorplan_id').value;
document.addEventListener("DOMContentLoaded", function() {
    init_floor_plan(floorplan_id, canvas, "readonly");
});
