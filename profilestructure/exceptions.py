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

class UnknownKeyError(Exception):
    """
    Exception raised when a key is not found in a profile.
    """
    pass

class DuplicatedKeyError(Exception):
    """
    Exception raised when a duplicated key is encountered.
    """
    pass