import os.path
from sqlalchemy_fileattach.utils import random_string


class ShardGenerator(object):

    def __init__(self, depth=2, size=2):
        self.depth = depth
        self.size = size

    def __call__(self, name):
        shards = [random_string(size=self.size) for x in range(0, self.depth)]
        path_parts = shards + [name.lstrip(os.path.sep)]
        return os.path.join(*path_parts)

shard = ShardGenerator