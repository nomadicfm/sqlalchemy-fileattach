# coding=utf-8
import os.path

from ..utils import test_files_path, BaseTestCase


class FileSystemStoreTestCase(BaseTestCase):

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

    def test_same_names(self):
        name1 = self.store.save('my-file', content="Some content")
        name2 = self.store.save('my-file', content="Some other")
        self.assertNotEqual(name1, name2)