"""
A collection of shared helper utilities
"""

import io


def is_file_obj(filename_or_fileobj):
    """ Is the given argument a File-like object? """
    if isinstance(filename_or_fileobj, io.IOBase):
        return True
    if hasattr(filename_or_fileobj, 'read') and hasattr(filename_or_fileobj, 'seek'):
        return True
    return False


def is_filename(filename_or_fileobj):
    """ Is the given argument a File object? """
    return isinstance(filename_or_fileobj, str)
