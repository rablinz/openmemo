import os
import mimetypes 
import logging
from fs.errors import FSError
from .exceptions import ConversionFailure

log = logging.getLogger(__name__)

def resource_from_file(dir, path):
    try:
        with dir.open(path, 'rb') as file:
            data = file.read()
    except FSError, e:
        raise ConversionFailure(str(e))
    
    resource = dict(
        filename = os.path.basename(path),
        data = data,
        mime_type = mimetypes.guess_type(path)[0]
    )       
    return resource