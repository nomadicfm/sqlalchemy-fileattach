# coding=utf-8
import tempfile
import os.path
from unittest.case import TestCase

from sqlalchemy_fileattach.stores.fs import FileSystemStore
from sqlalchemy_fileattach.utils import set_default_store
from ..utils import test_files_path
from tests.utils import get_session, rollback_session


class FileSystemStoreTestCase(TestCase):

    def setUp(self):
        tmp_dir = tempfile.mkdtemp(prefix=self.id())
        self.store = FileSystemStore(tmp_dir, 'http://example.com/static/')
        self.session = get_session()
        set_default_store(self.store)

    def tearDown(self):
        rollback_session(self.session)

    def test_save_text(self):
        name = self.store.save('my-file', content='Some sample contënt')
        path = self.store.path(name)
        with open(path, 'rb') as f:
            self.assertEqual(f.read(), 'Some sample contënt')

    def test_save_file(self):
        with open(test_files_path / 'small.txt', 'rb') as f:
            name = self.store.save('my-file', content=f)
        path = self.store.path(name)
        with open(path, 'rb') as f:
            self.assertEqual(f.read(), 'This is a small text file.\n\nSome Uniço∂e')

    def test_open(self):
        with open(self.store.path('new-file'), 'wb+') as f:
            f.write('Test contentś')
        f = self.store.open('new-file')
        self.assertEqual(f.read(), 'Test contentś')

    def test_delete(self):
        path = self.store.path('new-file')
        with open(path, 'wb+') as f:
            f.write('Test contentś')
        self.store.delete('new-file')
        self.assertFalse(os.path.exists(path))

    def test_url(self):
        self.assertEqual(self.store.url('new-file'), 'http://example.com/static/new-file')
        self.assertEqual(self.store.url('/new-file'), 'http://example.com/static/new-file')