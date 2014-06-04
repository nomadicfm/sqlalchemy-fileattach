import os.path
import os
import shutil
import errno
from sqlalchemy_fileattach.exceptions import InvalidPathError

from sqlalchemy_fileattach.stores.base import BaseStore
from sqlalchemy_fileattach.utils import random_string


class FileSystemStore(BaseStore):

    def __init__(self, base_path, base_url, **kwargs):
        super(FileSystemStore, self).__init__(**kwargs)
        self.base_path = base_path.rstrip('/')
        self.base_url = base_url.rstrip('/')

    def save(self, name, content):
        name = self.get_available_name(name)
        path = self.path(name)
        try:
            os.makedirs(os.path.dirname(path))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        with open(path, 'wb') as dst:
            if hasattr(content, 'read'):
                shutil.copyfileobj(content, dst)
            else:
                dst.write(content)
        return name

    def open(self, name):
        return open(self.path(name), 'rb')

    def delete(self, name):
        assert name, "The name argument is not allowed to be empty."
        path = self.path(name)
        try:
            os.remove(path)
        except OSError as e:
            # ENOENT = No such file or directory
            if e.errno != errno.ENOENT:
                raise

    def size(self, name):
        return os.path.getsize(self.path(name))

    def url(self, name):
        return '%s/%s' % (self.base_url, name.lstrip('/'))

    def path(self, name):
        path = os.path.join(self.base_path, name)
        path = os.path.normpath(path)
        if not path.startswith(self.base_path):
            raise InvalidPathError('Path resolves to location outside of base_path')
        return path

    def exists(self, name):
        return os.path.exists(self.path(name))