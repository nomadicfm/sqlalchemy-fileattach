import tempfile
from unittest import TestCase
from path import path

from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, StaticPool
from sqlalchemy_fileattach.stores.fs import FileSystemStore
from sqlalchemy_fileattach.utils import set_default_store

test_files_path = path(__file__).dirname() / 'files'

DEFAULT_DATABASE_URL = 'sqlite://'
ECHO_SQL = False

Base = declarative_base()
Session = sessionmaker()


class BaseTestCase(TestCase):

    def setUp(self):
        self.session = get_session()
        if hasattr(self, '_store'):
            del self._store
        set_default_store(self.store)

    def tearDown(self):
        rollback_session(self.session)

    @property
    def store(self):
        if hasattr(self, '_store'):
            return self._store

        self._store = self.make_store()
        return self._store

    def make_store(self):
        tmp_dir = tempfile.mkdtemp(prefix=self.id())
        return FileSystemStore(tmp_dir, 'http://example.com/static')


def get_session():
    connect_args = {}
    options = {'connect_args': connect_args, 'poolclass': NullPool}
    # We have to use SQLite :memory: database across multiple threads
    # for testing.  http://bit.ly/sqlalchemy-sqlite-memory-multithread
    connect_args['check_same_thread'] = False
    options['poolclass'] = StaticPool
    engine = create_engine(DEFAULT_DATABASE_URL, echo=ECHO_SQL, **options)
    metadata = Base.metadata
    metadata.drop_all(bind=engine)
    metadata.create_all(bind=engine)
    session = Session(bind=engine, autocommit=True)
    return session

def rollback_session(session):
    engine = session.bind
    session.rollback()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()