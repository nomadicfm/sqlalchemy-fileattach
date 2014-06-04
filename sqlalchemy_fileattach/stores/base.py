import os.path
import itertools

__all__ = 'BaseStore',


class BaseStore(object):

    def __init__(self, **kwargs):
        pass

    def save(self, name, content):
        raise NotImplementedError('save() has to be implemented')

    def delete(self, name):
        raise NotImplementedError('delete() has to be implemented')

    def open(self, name):
        raise NotImplementedError('open() has to be implemented')

    def exists(self, name):
        raise NotImplementedError('exists() has to be implemented')

    def size(self, name):
        raise NotImplementedError('size() has to be implemented')

    def url(self, name):
        raise NotImplementedError('url() has to be implemented')

    def path(self, name):
        """
        Returns a local filesystem path where the file can be retrieved using
        Python's built-in open() function. Storage systems that can't be
        accessed using open() should *not* implement this method.
        """
        raise NotImplementedError("This backend doesn't support absolute paths.")

    def get_available_name(self, name):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        """
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        # If the filename already exists, add an underscore and a number (before
        # the file extension, if one exists) to the filename until the generated
        # filename doesn't exist.
        count = itertools.count(1)
        while self.exists(name):
            # file_ext includes the dot.
            name = os.path.join(dir_name, "%s_%s%s" % (file_root, next(count), file_ext))

        return name