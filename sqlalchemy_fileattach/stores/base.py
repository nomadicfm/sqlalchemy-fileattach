__all__ = 'BaseStore',


class BaseStore(object):

    def save(self, name, content):
        raise NotImplementedError('save() has to be implemented')

    def delete(self, name):
        raise NotImplementedError('delete() has to be implemented')

    def open(self, name):
        raise NotImplementedError('open() has to be implemented')

    def url(self, name):
        raise NotImplementedError('url() has to be implemented')

    def path(self, name):
        """
        Returns a local filesystem path where the file can be retrieved using
        Python's built-in open() function. Storage systems that can't be
        accessed using open() should *not* implement this method.
        """
        raise NotImplementedError("This backend doesn't support absolute paths.")
