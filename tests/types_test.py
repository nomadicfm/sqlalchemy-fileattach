# coding=utf-8
import tempfile
import os.path

from unittest import TestCase
from sqlalchemy import Column, Integer
from sqlalchemy_fileattach.stores.fs import FileSystemStore
from sqlalchemy_fileattach.types import FileType
from sqlalchemy_fileattach.utils import set_default_store
from tests.utils import get_session, rollback_session, Base, test_files_path


class Author(Base):
    id = Column(Integer(), primary_key=True)
    image = Column(FileType())
    __tablename__ = 'author'


class AuthorFnGen(Base):
    id = Column(Integer(), primary_key=True)
    image = Column(FileType(file_name_generator=lambda n: 'abc123_%s' % n))
    __tablename__ = 'author_fngen'


class FileSystemStoreTestCase(TestCase):

    def setUp(self):
        tmp_dir = tempfile.mkdtemp(prefix=self.id())
        self.store = FileSystemStore(tmp_dir, 'http://example.com/static')
        self.session = get_session()
        set_default_store(self.store)

    def tearDown(self):
        rollback_session(self.session)

    def test_assign(self):
        author = Author()
        author.image = open(test_files_path / 'adam.png')
        self.session.add(author)
        self.session.flush()
        self.assertEqual(author.image, 'adam.png')

    def test_delete(self):
        author = Author()
        author.image = open(test_files_path / 'adam.png')
        self.session.add(author)
        self.session.flush()
        self.assertTrue(os.path.exists(self.store.path('adam.png')))
        author.image.delete()
        self.assertEqual(author.image, None)
        self.assertFalse(os.path.exists(self.store.path('adam.png')))

    def test_save(self):
        author = Author()
        author.image = open(test_files_path / 'adam.png')
        self.session.add(author)
        self.session.flush()
        with open(test_files_path / 'small.txt', 'rb') as f:
            author.image.save(f.read())
        with open(self.store.path('adam_1.png'), 'rb') as f:
            self.assertEqual(f.read(), 'This is a small text file.\n\nSome Uniço∂e')

    def test_delete_file_name_generated(self):
        author = AuthorFnGen()
        author.image = open(test_files_path / 'adam.png')
        self.session.add(author)
        self.session.flush()
        self.assertTrue(os.path.exists(self.store.path('abc123_adam.png')))
        author.image.delete()
        self.assertEqual(author.image, None)
        self.assertFalse(os.path.exists(self.store.path('abc123_adam.png')))

    def test_save_file_name_generated(self):
        author = AuthorFnGen()
        author.image = open(test_files_path / 'adam.png')
        self.session.add(author)
        self.session.flush()
        with open(test_files_path / 'small.txt', 'rb') as f:
            author.image.save(f.read())
        self.assertEqual(author.image.name, 'abc123_adam_1.png')
        with open(self.store.path('abc123_adam_1.png'), 'rb') as f:
            self.assertEqual(f.read(), 'This is a small text file.\n\nSome Uniço∂e')