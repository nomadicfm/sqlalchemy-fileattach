# coding=utf-8
import os.path

from unittest import TestCase
from sqlalchemy import Column, Integer
from sqlalchemy_fileattach.types import FileType
from tests.utils import Base, test_files_path, BaseTestCase


class Author(Base):
    id = Column(Integer(), primary_key=True)
    image = Column(FileType())
    __tablename__ = 'author'


class AuthorFnGen(Base):
    id = Column(Integer(), primary_key=True)
    image = Column(FileType(file_name_generator=lambda n: 'abc123_%s' % n))
    __tablename__ = 'author_fngen'


class FieldFileTestCase(TestCase):
    pass


class FileTypeTestCase(BaseTestCase):

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