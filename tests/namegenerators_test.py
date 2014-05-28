import re
from sqlalchemy_fileattach.namegenerators import ShardGenerator
from .utils import BaseTestCase


class ShardGeneratorTestCase(BaseTestCase):

    def test_simple(self):
        path = ShardGenerator(depth=2, size=2)('myfile.txt')
        self.assertRegexpMatches(path, r'[a-z0-9]{2}/[a-z0-9]{2}/myfile\.txt')

    def test_no_septh(self):
        path = ShardGenerator(depth=0, size=2)('myfile.txt')
        self.assertEqual(path, 'myfile.txt')

    def test_no_size(self):
        path = ShardGenerator(depth=2, size=0)('myfile.txt')
        self.assertEqual(path, 'myfile.txt')