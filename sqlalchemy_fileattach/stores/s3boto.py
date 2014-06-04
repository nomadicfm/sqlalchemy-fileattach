import calendar
from datetime import datetime, time
from StringIO import StringIO
import mimetypes
import os
import re
from boto.exception import S3ResponseError
from boto.s3.connection import SubdomainCallingFormat, S3Connection
from boto.s3.key import Key
from sqlalchemy_fileattach.exceptions import ImproperlyConfigured, SuspiciousOperation
from sqlalchemy_fileattach.stores.base import BaseStore
from sqlalchemy_fileattach.utils import File, FileProxyMixin

try:
    import boto
except ImportError:
    raise Exception("Boto could not be imported. You must install 'boto' to use S3BotoStore")

# The contents of this file are entirely ported from Django Storages.

GZIP_CONTENT_TYPES = ('text/css', 'application/javascript', 'application/x-javascript')

def safe_join(base, *paths):
    """
    A version of django.utils._os.safe_join for S3 paths.

    Joins one or more path components to the base path component
    intelligently. Returns a normalized version of the final path.

    The final path must be located inside of the base path component
    (otherwise a ValueError is raised).

    Paths outside the base path indicate a possible security
    sensitive operation.
    """
    from urlparse import urljoin
    # TODO: Consider importing Django's force_unicode function if necessary
    # base_path = force_unicode(base)
    base_path = base
    base_path = base_path.rstrip('/')
    # TODO: Consider importing Django's force_unicode function if necessary
    # paths = [force_unicode(p) for p in paths]

    final_path = base_path
    for path in paths:
        final_path = urljoin(final_path.rstrip('/') + "/", path.rstrip("/"))

    # Ensure final_path starts with base_path and that the next character after
    # the final path is '/' (or nothing, in which case final_path must be
    # equal to base_path).
    base_path_len = len(base_path)
    if not final_path.startswith(base_path) \
       or final_path[base_path_len:base_path_len + 1] not in ('', '/'):
        raise ValueError('the joined path is located outside of the base path'
                         ' component')

    return final_path.lstrip('/')

# Dates returned from S3's API look something like this:
# "Sun, 11 Mar 2012 17:01:41 GMT"
MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
DATESTR_RE = re.compile(r"^.+, (?P<day>\d{1,2}) (?P<month_name>%s) (?P<year>\d{4}) (?P<hour>\d{1,2}):(?P<minute>\d{1,2}):(?P<second>\d{1,2}) (GMT|UTC)$" % ("|".join(MONTH_NAMES)))
def _parse_datestring(dstr):
    """
    Parse a simple datestring returned by the S3 API and returns
    a datetime object in the local timezone.
    """
    # This regular expression and thus this function
    # assumes the date is GMT/UTC
    m = DATESTR_RE.match(dstr)
    if m:
        # This code could raise a ValueError if there is some
        # bad data or the date is invalid.
        datedict = m.groupdict()
        utc_datetime = datetime(
            int(datedict['year']),
            int(MONTH_NAMES.index(datedict['month_name'])) + 1,
            int(datedict['day']),
            int(datedict['hour']),
            int(datedict['minute']),
            int(datedict['second']),
        )

        # Convert the UTC datetime object to local time.
        return datetime(*time.localtime(calendar.timegm(utc_datetime.timetuple()))[:6])
    else:
        raise ValueError("Could not parse date string: " + dstr)


class S3BotoStore(BaseStore):

    """
    Amazon Simple Storage Service using Boto

    This storage backend supports opening files in read or write
    mode and supports streaming(buffering) data in chunks to S3
    when writing.
    """

    def __init__(self, bucket, access_key=None,
            secret_key=None, bucket_acl='public-read', acl='public-read',
            headers=None, gzip=False,
            gzip_content_types=GZIP_CONTENT_TYPES,
            querystring_auth=True,
            querystring_expire=3600,
            reduced_redundancy=False,
            custom_domain=None,
            secure_urls=True,
            location='',
            file_name_charset='utf-8',
            preload_metadata=False,
            calling_format=SubdomainCallingFormat(),
            auto_create_bucket=False,
            file_overwrite=False,
            **kwargs):
        super(S3BotoStore, self).__init__(**kwargs)
        self.bucket_acl = bucket_acl
        self.bucket_name = bucket
        self.acl = acl
        self.headers = headers or {}
        self.preload_metadata = preload_metadata
        self.gzip = gzip
        self.gzip_content_types = gzip_content_types
        self.querystring_auth = querystring_auth
        self.querystring_expire = querystring_expire
        self.reduced_redundancy = reduced_redundancy
        self.custom_domain = custom_domain
        self.secure_urls = secure_urls
        self.location = location or ''
        self.location = self.location.lstrip('/')
        self.file_name_charset = file_name_charset
        self.auto_create_bucket = auto_create_bucket
        self.file_overwrite = file_overwrite

        if not access_key and not secret_key:
            access_key, secret_key = self._get_access_keys()

        self.connection = S3Connection(access_key, secret_key,
            calling_format=calling_format)
        self._entries = {}

    @property
    def bucket(self):
        """
        Get the current bucket. If there is no current bucket object
        create it.
        """
        if not hasattr(self, '_bucket'):
            self._bucket = self._get_or_create_bucket(self.bucket_name)
        return self._bucket

    @property
    def entries(self):
        """
        Get the locally cached files for the bucket.
        """
        if self.preload_metadata and not self._entries:
            self._entries = dict((self._decode_name(entry.key), entry)
                                for entry in self.bucket.list())
        return self._entries

    def _get_access_keys(self):
        """
        Gets the access keys to use when accessing S3. If none
        are provided to the class in the constructor or in the
        settings then get them from the environment variables.
        """
        access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

        if access_key and secret_key:
            return access_key, secret_key

        return None, None

    def _get_or_create_bucket(self, name):
        """Retrieves a bucket if it exists, otherwise creates it."""
        try:
            return self.connection.get_bucket(name,
                validate=self.auto_create_bucket)
        except S3ResponseError:
            if self.auto_create_bucket:
                bucket = self.connection.create_bucket(name)
                bucket.set_acl(self.bucket_acl)
                return bucket
            raise ImproperlyConfigured("Bucket specified by "
                "config value 'bucket' does not exist. "
                "Buckets can be automatically created by setting "
                "auto_create_bucket=True")

    def _clean_name(self, name):
        """
        Cleans the name so that Windows style paths work
        """
        # Useful for windows' paths
        return os.path.normpath(name).replace('\\', '/')

    def _normalize_name(self, name):
        """
        Normalizes the name so that paths like /path/to/ignored/../something.txt
        work. We check to make sure that the path pointed to is not outside
        the directory specified by the LOCATION setting.
        """
        try:
            return safe_join(self.location, name)
        except ValueError:
            raise SuspiciousOperation("Attempted access to '%s' denied." %
                                      name)

    def _encode_name(self, name):
        # TODO: Consider importing Django's smart_str function if necessary
        # return smart_str(name, encoding=self.file_name_charset)
        return name

    def _decode_name(self, name):
        # TODO: Consider importing Django's smart_str function if necessary
        # return force_unicode(name, encoding=self.file_name_charset)
        return name

    def _compress_content(self, content):
        """Gzip a given string content."""
        from gzip import GzipFile

        zbuf = StringIO()
        zfile = GzipFile(mode='wb', compresslevel=6, fileobj=zbuf)
        zfile.write(content.read())
        zfile.close()
        content.file = zbuf
        return content

    def open(self, name, mode='rb'):
        name = self._normalize_name(self._clean_name(name))
        f = S3BotoStorageFile(name, mode, self)
        if not f.key:
            raise IOError('File does not exist: %s' % name)
        return f

    def save(self, name, content):
        if isinstance(content, (str, unicode)):
            # Support saving of string values
            content = StringIO(content)
        elif isinstance(content, file):
            # file objects don't support setting the 'name'
            # property. So wrap it in a FileProxyMixin
            f = FileProxyMixin()
            f.file = content
            content = f
        cleaned_name = self._clean_name(name)
        cleaned_name = self.get_available_name(cleaned_name)
        name = self._normalize_name(cleaned_name)
        headers = self.headers.copy()
        content_type = getattr(content, 'content_type',
            mimetypes.guess_type(name)[0] or Key.DefaultContentType)

        if self.gzip and content_type in self.gzip_content_types:
            content = self._compress_content(content)
            headers.update({'Content-Encoding': 'gzip'})

        content.name = cleaned_name
        encoded_name = self._encode_name(name)
        key = self.bucket.get_key(encoded_name)
        if not key:
            key = self.bucket.new_key(encoded_name)
        if self.preload_metadata:
            self._entries[encoded_name] = key

        key.set_metadata('Content-Type', content_type)
        key.set_contents_from_file(content, headers=headers, policy=self.acl,
                                   reduced_redundancy=self.reduced_redundancy,
                                   rewind=True)
        return cleaned_name

    def delete(self, name):
        name = self._normalize_name(self._clean_name(name))
        self.bucket.delete_key(self._encode_name(name))

    def exists(self, name):
        name = self._normalize_name(self._clean_name(name))
        if self.entries:
            return name in self.entries
        k = self.bucket.new_key(self._encode_name(name))
        return k.exists()

    def listdir(self, name):
        name = self._normalize_name(self._clean_name(name))
        # for the bucket.list and logic below name needs to end in /
        # But for the root path "" we leave it as an empty string
        if name:
            name += '/'

        dirlist = self.bucket.list(self._encode_name(name))
        files = []
        dirs = set()
        base_parts = name.split("/")[:-1]
        for item in dirlist:
            parts = item.name.split("/")
            parts = parts[len(base_parts):]
            if len(parts) == 1:
                # File
                files.append(parts[0])
            elif len(parts) > 1:
                # Directory
                dirs.add(parts[0])
        return list(dirs), files

    def size(self, name):
        name = self._normalize_name(self._clean_name(name))
        if self.entries:
            entry = self.entries.get(name)
            if entry:
                return entry.size
            return 0
        return self.bucket.get_key(self._encode_name(name)).size

    def modified_time(self, name):
        name = self._normalize_name(self._clean_name(name))
        entry = self.entries.get(name)
        if entry is None:
            entry = self.bucket.get_key(self._encode_name(name))

        # Parse the last_modified string to a local datetime object.
        return _parse_datestring(entry.last_modified)

    def url(self, name):
        name = self._normalize_name(self._clean_name(name))
        if self.custom_domain:
            return "%s://%s/%s" % ('https' if self.secure_urls else 'http',
                                   self.custom_domain, name)
        return self.connection.generate_url(self.querystring_expire,
            method='GET', bucket=self.bucket.name, key=self._encode_name(name),
            query_auth=self.querystring_auth, force_http=not self.secure_urls)

    def get_available_name(self, name):
        """ Overwrite existing file with the same name. """
        if self.file_overwrite:
            name = self._clean_name(name)
            return name
        return super(S3BotoStore, self).get_available_name(name)






    def path(self, name):
        return super(S3BotoStore, self).path(name)



class S3BotoStorageFile(File):
    """
    The default file object used by the S3BotoStorage backend.

    This file implements file streaming using boto's multipart
    uploading functionality. The file can be opened in read or
    write mode.

    This class extends Django's File class. However, the contained
    data is only the data contained in the current buffer. So you
    should not access the contained file object directly. You should
    access the data via this class.

    Warning: This file *must* be closed using the close() method in
    order to properly write the file to S3. Be sure to close the file
    in your application.
    """
    # TODO: Read/Write (rw) mode may be a bit undefined at the moment. Needs testing.
    # TODO: When Django drops support for Python 2.5, rewrite to use the
    #       BufferedIO streams in the Python 2.6 io module.

    def __init__(self, name, mode, storage, buffer_size=5242880):
        self._storage = storage
        self.name = name[len(self._storage.location):].lstrip('/')
        self._mode = mode
        self.key = storage.bucket.get_key(self._storage._encode_name(name))
        if not self.key and 'w' in mode:
            self.key = storage.bucket.new_key(storage._encode_name(name))
        self._is_dirty = False
        self._file = None
        self._multipart = None
        # 5 MB is the minimum part size (if there is more than one part).
        # Amazon allows up to 10,000 parts.  The default supports uploads
        # up to roughly 50 GB.  Increase the part size to accommodate
        # for files larger than this.
        self._write_buffer_size = buffer_size
        self._write_counter = 0

    @property
    def size(self):
        return self.key.size

    @property
    def file(self):
        if self._file is None:
            self._file = StringIO()
            if 'r' in self._mode:
                self._is_dirty = False
                self.key.get_contents_to_file(self._file)
                self._file.seek(0)
        return self._file

    def read(self, *args, **kwargs):
        if 'r' not in self._mode:
            raise AttributeError("File was not opened in read mode.")
        return super(S3BotoStorageFile, self).read(*args, **kwargs)

    def write(self, *args, **kwargs):
        if 'w' not in self._mode:
            raise AttributeError("File was not opened in write mode.")
        self._is_dirty = True
        if self._multipart is None:
            provider = self.key.bucket.connection.provider
            upload_headers = {
                provider.acl_header: self._storage.acl
            }
            upload_headers.update(self._storage.headers)
            self._multipart = self._storage.bucket.initiate_multipart_upload(
                self.key.name,
                headers = upload_headers,
                reduced_redundancy = self._storage.reduced_redundancy
            )
        if self._write_buffer_size <= self._buffer_file_size:
            self._flush_write_buffer()
        return super(S3BotoStorageFile, self).write(*args, **kwargs)

    @property
    def _buffer_file_size(self):
        pos = self.file.tell()
        self.file.seek(0,os.SEEK_END)
        length = self.file.tell()
        self.file.seek(pos)
        return length

    def _flush_write_buffer(self):
        """
        Flushes the write buffer.
        """
        if self._buffer_file_size:
            self._write_counter += 1
            self.file.seek(0)
            self._multipart.upload_part_from_file(
                self.file,
                self._write_counter,
                headers=self._storage.headers
            )
            self.file.close()
            self._file = None

    def close(self):
        if self._is_dirty:
            self._flush_write_buffer()
            self._multipart.complete_upload()
        else:
            if not self._multipart is None:
                self._multipart.cancel_upload()
        self.key.close()