import os
import functools
import beartype
import filelock
import tinydb
import json
import typing_extensions

from contextlib import contextmanager
from beartype.vale import Is
import web3


def generate_address_and_key():
    account = web3.Account.create()
    address = account.address
    key = account.key.hex()
    return address, key

@beartype.beartype
def check_key_validity(address: str, key: str, enforce: bool = False):
    ret = False
    try:
        account = web3.Account.from_key(key)
        ret = account.address == address
    except:
        pass
    if enforce:
        assert ret, f"Key '{key}' is not for address '{address}'"
    return ret


def check_if_serializable(data:object) -> bool:
    serializable = False
    try:
        json.dumps(data, ensure_ascii=False)
        serializable = True
    except:
        print("data not serializable")
    return serializable


JSONSerializableObject = typing_extensions.Annotated[object, Is[check_if_serializable]]


def ensure_dir(dir_path: str):
    if os.path.exists(dir_path):
        assert os.path.isdir(
            dir_path
        ), f"Path '{dir_path}' already exists and is not a directory"
    else:
        os.mkdir(dir_path)


# TODO: use tinydb context with filelock to ensure data consistency
@contextmanager
def tinydb_context(db_path: str):
    prefix, suffix = os.path.split(db_path)
    db_lockpath = os.path.join(prefix, f".{suffix}.lock")
    with filelock.FileLock(db_lockpath):
        with tinydb.TinyDB(db_path) as db:
            yield db


@beartype.beartype
class AtomicTinyDB:
    def __init__(self, db_path: str):
        self._db_context_builder = functools.partial(tinydb_context, db_path)

    def update(self, *args, **kwargs):
        with self._db_context_builder() as db:
            return db.update(*args, **kwargs)

    def search(self, *args, **kwargs):
        with self._db_context_builder() as db:
            return db.search(*args, **kwargs)

    def get(self, *args, **kwargs):
        with self._db_context_builder() as db:
            return db.get(*args, **kwargs)

    def insert(self, *args, **kwargs):
        with self._db_context_builder() as db:
            return db.insert(*args, **kwargs)


@beartype.beartype
class AtomicKVStore:
    def __init__(self, storage_location: str, readonly_keys: list[str] = []):
        self.storage_location = storage_location
        self.readonly_keys = readonly_keys
        self.load_data()

    def load_data(self):
        if os.path.exists(self.storage_location):
            with open(self.storage_location, "r") as f:
                self.data = json.loads(f.read())
        else:
            self.data = {}
            self.persist_data()

    def persist_data(self):
        with open(self.storage_location, "w+") as f:
            f.write(json.dumps(self.data, ensure_ascii=False))

    def set(
        self, key: str, value: JSONSerializableObject
    ):  # value shall be json serializable
        if key in self.readonly_keys:
            if key in self.data.keys():
                raise Exception(f"Cannot set readonly key '{key}' twice")
        self.data[key] = value
        self.persist_data()

    def get(self, key: str) -> JSONSerializableObject:
        return self.data[key]

    @contextmanager
    def context(self):
        try:
            yield self
        finally:
            self.persist_data()
