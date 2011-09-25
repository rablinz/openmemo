
class OpenMemoException (Exception):
    def __init__(self, msg=None, **kwargs):
        super(OpenMemoException, self).__init__((msg % kwargs) if msg else None)

class ConversionFailure (OpenMemoException):
    pass
