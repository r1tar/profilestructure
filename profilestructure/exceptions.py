class UnknownProfileError(Exception):
    """
    Exception raised when a profile is not found.
    """
    pass

class UnsupportedTypeError(Exception):
    """
    Exception raised when an unsupported type is encountered.
    """
    pass