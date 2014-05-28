# coding=utf-8
import os.path
from sqlalchemy_fileattach.stores.s3boto import S3BotoStore

from ..utils import test_files_path, BaseTestCase


class S3BotoStoreTestCase(BaseTestCase):

    def make_store(self):
        store = S3BotoStore('fileattach-test-bucket',
                            auto_create_bucket=True,
                            location=self.id(),
                            querystring_auth=False,
                            )
        for key in store.bucket.list(prefix=self.id()):
            key.delete()
        return store

    def test_save_text(self):
        name = self.store.save('my-file', content='Some sample contënt')
        file = self.store.open(name)
        self.assertEqual(file.read(), 'Some sample contënt')

    def test_save_and_open_file(self):
        with open(test_files_path / 'small.txt', 'rb') as f:
            name = self.store.save('my-file', content=f)
        file = self.store.open(name)
        self.assertEqual(file.read(), 'This is a small text file.\n\nSome Uniço∂e')

    def test_delete(self):
        with open(test_files_path / 'small.txt', 'rb') as f:
            name = self.store.save('my-file', content=f)
        self.store.delete('my-file')
        self.assertRaises(IOError, self.store.open, 'my-file')

    def test_url(self):
        self.assertTrue(self.store.url('new-file').endswith('.test_url/new-file'))

    def test_same_names(self):
        name1 = self.store.save('my-file', content="Some content")
        name2 = self.store.save('my-file', content="Some other")
        self.assertNotEqual(name1, name2)