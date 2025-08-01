def file_upload(instance, filename):
    """
    Return a path for uploading image attchments.
    Adapted from netbox/extras/utils.py
    """
    path = 'netbox-floorplan/'

    return f'{path}{filename}'
