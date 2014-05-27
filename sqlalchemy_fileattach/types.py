import os.path

from sqlalchemy import TypeDecorator, Unicode
from sqlalchemy_fileattach.exceptions import NoStoreError, InvalidFieldValue
from sqlalchemy_fileattach.utils import FileProxyMixin, get_default_store


class FieldFile(FileProxyMixin):
    def __init__(self, name, store, file_name_generator):
        self.name = name
        self.store = store
        self.file_name_generator = file_name_generator or (lambda x: x)

    def __eq__(self, other):
        if hasattr(other, 'name'):
            return self.name == other.name
        else:
            return self.name == other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.name)

    def _require_file(self):
        if not self.name:
            raise ValueError("The '%s' attribute has no file associated with it." % self.field.name)

    def _get_file(self):
        self._require_file()
        if not hasattr(self, '_file') or self._file is None:
            self._file = self.store.open(self.name, 'rb')
        return self._file

    def _set_file(self, file):
        self._file = file

    def _del_file(self):
        del self._file

    file = property(_get_file, _set_file, _del_file)

    def _get_path(self):
        self._require_file()
        return self.store.path(self.name)
    path = property(_get_path)

    def _get_url(self):
        self._require_file()
        return self.store.url(self.name)
    url = property(_get_url)

    def _get_size(self):
        self._require_file()
        if not self._committed:
            return self.file.size
        return self.store.size(self.name)
    size = property(_get_size)

    def save(self, content, name=None):
        name = self.file_name_generator(name) if name else self.name
        self.name = self.store.save(name, content)

    def delete(self, save=True):
        if not self:
            return
        # Only close the file if it's already open, which we know by the
        # presence of self._file
        if hasattr(self, '_file'):
            self.close()
            del self.file

        self.store.delete(self.name)

        self.name = None

    def _get_closed(self):
        file = getattr(self, '_file', None)
        return file is None or file.closed
    closed = property(_get_closed)

    def close(self):
        file = getattr(self, '_file', None)
        if file is not None:
            file.close()


class FileType(TypeDecorator):
    impl = Unicode

    values = None

    def __init__(self, store=None, file_name_generator=None):
        super(FileType, self).__init__()
        self._store = store
        self.file_name_generator = file_name_generator

    @property
    def store(self):
        store = self._store or get_default_store()
        if not store:
            raise NoStoreError('No store was passed to constructor and no default store is configured')
        return store

    def process_bind_param(self, value, dialect):
        # Get the value ready for the DB

        if isinstance(value, file):
            name = value.name
            if self.file_name_generator:
                dir_name, file_name = os.path.split(name)
                file_name = self.file_name_generator(file_name)
                name = os.path.join(dir_name, file_name)
            name = self.store.save(os.path.basename(name), value)
        else:
            name = value.name
        return name

    def process_result_value(self, value, dialect):
        # Parse the values from the DB
        return FieldFile(value, self.store, self.file_name_generator)