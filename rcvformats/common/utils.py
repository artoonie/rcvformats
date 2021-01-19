"""
A collection of shared helper utilities
"""

import io
import os


def is_file_obj(filename_or_fileobj):
    """ Is the given argument a File-like object? """
    if isinstance(filename_or_fileobj, io.IOBase):
        return True
    if hasattr(filename_or_fileobj, 'read') and hasattr(filename_or_fileobj, 'seek'):
        return True
    return False


def is_filename(filename_or_fileobj):
    """ Is the given argument a filename? """
    return os.path.isfile(filename_or_fileobj)
