# coding=utf-8
import os.path

from unittest import TestCase
from sqlalchemy import Column, Integer
from sqlalchemy_fileattach.exceptions import NoFileNameError
from sqlalchemy_fileattach.types import FileType, FieldFile
from tests.utils import Base, test_files_path, BaseTestCase


class Author(Base):
    id = Column(Integer(), primary_key=True)
    image = Column(FileType())
    __tablename__ = 'author'


class AuthorFnGen(Base):
    id = Column(Integer(), primary_key=True)
    image = Column(FileType(file_name_generator=lambda n: 'abc123_%s' % n))
    __tablename__ = 'author_fngen'


class FieldFileTestCase(BaseTestCase):

    def test_eq(self):
        self.assertEqual(
            FieldFile('my-file.jpg', self.store),
            FieldFile('my-file.jpg', self.store))
        self.assertNotEqual(
            FieldFile('my-file.txt', self.store),
            FieldFile('my-file.jpg', self.store))
        self.assertNotEqual(
            FieldFile('foo-bar.jpg', self.store),
            FieldFile('my-file.jpg', self.store))
        self.assertNotEqual(
            FieldFile('my-file.JPG', self.store),
            FieldFile('my-file.jpg', self.store))

        self.assertEqual(
            FieldFile('my-file.jpg', self.store),
            'my-file.jpg')
        self.assertNotEqual(
            FieldFile('my-file.txt', self.store),
            'my-file.jpg')
        self.assertNotEqual(
            FieldFile('foo-bar.jpg', self.store),
            'my-file.jpg')
        self.assertNotEqual(
            FieldFile('my-file.JPG', self.store),
            'my-file.jpg')

        self.assertEqual(
            FieldFile(None, self.store),
            None)

    def test_file_get(self):
        self.store.save('test.txt', test_files_path / 'small.txt')
        self.assertIsInstance(
            FieldFile('test.txt', self.store).file,
            file)
        self.assertRaises(
            IOError,
            lambda: FieldFile('test-XXX.txt', self.store).file)

    def test_file_set(self):
        ff = FieldFile('test.txt', self.store)
        ff.file = open(test_files_path / 'small.txt', 'rb')
        # Setting the file doesn't really do anything
        self.assertEqual(ff.name, 'test.txt')

    def test_file_del(self):
        self.store.save('test.txt', test_files_path / 'small.txt')
        ff = FieldFile('test.txt', self.store)
        self.assertIsInstance(ff.file, file)
        del ff.file
        # Cached file is now gone
        self.assertFalse(hasattr(ff, '_file'))
        # Getting it via the property recreates it
        self.assertIsInstance(ff.file, file)
        # And check it now exists
        self.assertTrue(hasattr(ff, '_file'))

    def test_get_path(self):
        self.store.save('test.txt', test_files_path / 'small.txt')
        self.assertEqual(
            FieldFile('test.txt', self.store).path,
            self.store.path('test.txt'))
        self.assertRaises(NoFileNameError,
            lambda: FieldFile(None, self.store).path)

    def test_set_path(self):
        def fn():
            FieldFile('test.txt', self.store).path = 'x'
        self.assertRaises(AttributeError, fn)

    def test_del_path(self):
        def fn():
            ff = FieldFile('test.txt', self.store)
            del ff.path
        self.assertRaises(AttributeError, fn)

    def test_get_url(self):
        self.store.save('test.txt', test_files_path / 'small.txt')
        self.assertEqual(
            FieldFile('test.txt', self.store).url,
            self.store.url('test.txt'))
        self.assertRaises(NoFileNameError,
            lambda: FieldFile(None, self.store).url)

    def test_set_url(self):
        def fn():
            FieldFile('test.txt', self.store).url = 'x'
        self.assertRaises(AttributeError, fn)

    def test_del_url(self):
        def fn():
            ff = FieldFile('test.txt', self.store)
            del ff.url
        self.assertRaises(AttributeError, fn)

    def test_get_size(self):
        self.store.save('test.txt', test_files_path / 'small.txt')
        self.assertEqual(
            FieldFile('test.txt', self.store).size,
            64)
        self.assertRaises(NoFileNameError,
            lambda: FieldFile(None, self.store).size)

    def test_set_size(self):
        def fn():
            FieldFile('test.txt', self.store).size = 123
        self.assertRaises(AttributeError, fn)

    def test_del_size(self):
        def fn():
            ff = FieldFile('test.txt', self.store)
            del ff.size
        self.assertRaises(AttributeError, fn)

    def test_save_with_name(self):
        self.store.save('aaa.txt', test_files_path / 'small.txt')
        ff = FieldFile('aaa.txt', self.store)
        # Make it load the file
        x = ff.file

        ff.save(open(test_files_path / 'adam.png', 'rb'), 'text.txt')
        self.assertIn('text.txt', ff.file.name)


    def test_save_with_name_with_fn_gen(self):
        self.store.save('aaa.txt', test_files_path / 'small.txt')
        ff = FieldFile('aaa.txt', self.store, file_name_generator=lambda x: 'generated.foo')
        # Make it load the file
        x = ff.file

        ff.save(open(test_files_path / 'adam.png', 'rb'), 'text.txt')
        self.assertIn('generated.foo', ff.file.name)
        self.assertIn('generated.foo', ff.name)

    def test_save_without_name(self):
        self.store.save('aaa.txt', test_files_path / 'small.txt')
        ff = FieldFile('aaa.txt', self.store)
        # Make it load the file
        x = ff.file

        # Overwriting, so the new file stays in palce and this one gets '_1' appended
        ff.save(open(test_files_path / 'adam.png', 'rb'))
        self.assertIn('aaa_1.txt', ff.file.name)

    def test_delete_no_file(self):
        FieldFile(None, self.store).delete()

    def test_delete_with_file(self):
        self.store.save('aaa.txt', test_files_path / 'small.txt')
        ff = FieldFile('aaa.txt', self.store)
        # Make it load the file
        x = ff.file
        ff.delete()
        self.assertFalse(ff.has_file_handle)
        self.assertFalse(os.path.exists(self.store.path('aaa.txt')))

    def test_close(self):
        self.store.save('aaa.txt', test_files_path / 'small.txt')
        ff = FieldFile('aaa.txt', self.store)
        # Make it load the file
        x = ff.file
        ff.close()
        # Make it load the file again, just to check it can still be reopened
        ff.file.read()



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