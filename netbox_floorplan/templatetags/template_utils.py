from django import template
from django.utils.html import escapejs
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag()
def denormalize_measurement(unit, value):
    # print(unit, value)

    if unit == 'ft':
        return round(
            (round(float(value), 2) * 3.28 / 100),
            2
        )
    else:
        return round(
            (float(value) / 100),
            2
        )


@register.filter
def js_str(value):
    """
    Render a value as a quoted JavaScript string literal.

    The floorplan tables build onclick handlers containing JavaScript string literals.
    Interpolating a value directly is unsafe: Django escapes a quote to the HTML entity
    &#x27;, which the browser decodes back to a quote before the JavaScript is parsed,
    so a rack or device named e.g. O'Brien breaks the handler. escapejs() emits a
    JavaScript escape sequence instead, which survives HTML attribute decoding.

    A value of None renders as the string 'None', matching Django's default rendering of
    None in a template, so this only changes escaping and not what is emitted.
    """
    return mark_safe(f"'{escapejs(value)}'")


@register.filter
def rack_outer_js(rack, dimension):
    """
    Return a rack's outer dimension as a JavaScript literal, or `null` if it is unset.

    `dimension` is one of 'width', 'depth' or 'unit'.

    Rack.outer_width / outer_depth / outer_unit are deprecated as of NetBox 4.7 and are
    to be inferred from the rack's assigned RackType in v5.0. NetBox currently copies
    these values down from the RackType whenever a Rack or RackType is saved, so the
    RackType is consulted first and the Rack's own field is used as a fallback. That is
    equivalent on 4.7, preserves the behaviour of racks with no RackType assigned, and
    keeps working once the fields are removed from Rack.
    """
    value = None

    rack_type = getattr(rack, 'rack_type', None)
    if rack_type is not None:
        value = getattr(rack_type, f'outer_{dimension}', None)
    if not value:
        value = getattr(rack, f'outer_{dimension}', None)

    # A falsy value renders as null, matching the behaviour this replaced.
    if not value:
        return mark_safe('null')

    # The unit is a string and must be quoted; the dimensions are numeric.
    if dimension == 'unit':
        return mark_safe(f"'{escapejs(value)}'")

    return mark_safe(str(value))
