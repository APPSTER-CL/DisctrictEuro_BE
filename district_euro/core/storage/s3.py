import cStringIO as StringIO
import os
import random
import string

import boto

_ONE_MB = 2 ** 20
CHUNK_SIZE = _ONE_MB
MINIMUM_MULTIPART_SIZE = 5 * _ONE_MB


class S3Service:
    _connection = None

    def __init__(self, access_key, secret_key, bucket_name, policy='public-read'):
        self.default_policy = policy
        if not S3Service._connection:
            S3Service._connection = boto.connect_s3(access_key, secret_key)
        try:
            self.bucket = S3Service._connection.get_bucket(bucket_name)
        except:
            self.bucket = S3Service._connection.create_bucket(bucket_name, policy=policy)

    def upload_from_file(self, data, key_name=None, prefix=None, file_name=None):
        if not key_name:
            key_name = self.generate_random_key_name(self.get_extension(file_name))
        if prefix:
            key_name = prefix + key_name
        key = self.bucket.new_key(key_name)

        key.set_contents_from_file(data, policy=self.default_policy, rewind=True)
        return key

    def upload_from_filename(self, local_path):
        extension = os.path.splitext(local_path)[1][1:]
        key_name = self.generate_random_key_name(extension)
        key = self.bucket.new_key(key_name)
        key.set_contents_from_filename(local_path)
        key.set_acl('public-read')
        return key

    def delete_key(self, key):
        key_exists = self.bucket.get_key(key)
        if key_exists:
            return self.bucket.delete_key(key)
        return None

    @staticmethod
    def generate_random_key_name(extension):
        name = ''.join(random.choice(string.ascii_lowercase) for i in range(15))
        if extension:
            return "{0}.{1}".format(name, extension.replace(".", ""))
        return name

    @staticmethod
    def get_extension(file_name):
        if not file_name:
            return ''
        extension = file_name.split('.')[-1]
        if extension == file_name:
            return ''
        return extension


class S3ConnectionPool(object):
    def __init__(self, access_key, secret_key, bucket_name):
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.pool = []

    def get_connection(self):
        if len(self.pool):
            return self.pool.pop()
        else:
            return S3Service(self.access_key, self.secret_key, self.bucket_name)

    def return_connection(self, conn):
        assert isinstance(conn, S3Service)
        self.pool.append(conn)


_connection_pool = None


def init_connetion_pool(*args, **kwargs):
    global _connection_pool
    _connection_pool = S3ConnectionPool(*args, **kwargs)


def get_connection():
    class Connection(object):
        def __enter__(self):
            self.conn = _connection_pool.get_connection()
            return self.conn

        def __exit__(self, exc_type, exc_val, exc_tb):
            _connection_pool.return_connection(self.conn)
            self.conn = None
    return Connection()

