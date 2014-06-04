from .fs import FileSystemStore
from .s3boto import S3BotoStore


def store_from_config(config, prefix='', backend=None, **backend_kwargs):

    def get_key(k):
        return '.'.join(filter(bool, [prefix, k]))

    # First get the backend
    from sqlalchemy_fileattach.stores import S3BotoStore, FileSystemStore

    backend = backend or config[get_key('backend')]
    if isinstance(backend, str):
        backend_class = {
            'fs': FileSystemStore,
            's3': S3BotoStore,
        }[backend]
    else:
        backend_class = backend

    # Now get the args to pass to the backend
    search_for = (get_key(backend) + '.') if prefix else ''
    kwargs = dict([(k.replace(search_for, ''), v) for k, v in config.items() if k.startswith(search_for)])
    kwargs.update(backend_kwargs)

    return backend_class(**kwargs)