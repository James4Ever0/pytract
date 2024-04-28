# smart contract web3 virtual machine
import tinydb

# import abc
import pydantic
import web3
import beartype

try:
    from typing_extensions import Self
except:
    from typing import Self
try:
    from typing_extensions import Optional
except:
    from typing import Optional
try:
    from typing_extensions import Literal
except:
    from typing import Literal

from typing import Union
from contextlib import contextmanager
import os
import pathlib
import filelock
import functools
import json
import hashlib

# import dill
import typing

Number = Union[int, float]


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


def generate_account_static_info():
    account = web3.Account.create()
    ret = AccountStaticInfo(address=account.address, key=account.key.hex())
    return ret


def check_key_validity(address: str, key: str):
    ret = False
    try:
        account = web3.Account.from_key(key)
        assert account.address == address, f"Key '{key}' is not for address '{address}'"
        ret = True
    except:
        pass
    return ret


def check_if_serializable(data) -> bool:
    serializable = False
    try:
        json.dumps(data, ensure_ascii=False)
        serializable = True
    except:
        print("data not serializable")
    return serializable


_default_vm: Optional["VM"] = None


class EngageException(Exception): ...


class AccountBase(pydantic.BaseModel):
    type: Literal["account"] = "account"


class AccountStaticInfo(pydantic.BaseModel):
    address: str
    key: str

    @pydantic.validator("address", "key")
    def validate_account(cls, v, values):
        if "address" in values and "key" in values:
            address, key = values["address"], values["key"]
            assert check_key_validity(
                address, key
            ), f"Key '{key} is not valid for {address}"
        return v


class AccountVolatileInfo(pydantic.BaseModel):
    balance: Number

    @pydantic.validator("balance")
    def validate_balance(cls, v):
        assert v >= 0, "Balance must be non-negative"
        return v


class AccountInfo(AccountBase, AccountStaticInfo, AccountVolatileInfo): ...


def get_vm_with_fallback(vm: Optional["VM"]):
    global _default_vm
    if vm is None:
        if _default_vm is None:
            raise EngageException("VM not engaged")
        else:
            return _default_vm
    else:
        return vm


def ensure_dir(dirpath: Union[str, pathlib.Path]):
    if os.path.exists(dirpath):
        assert os.path.isdir(dirpath), f"Path '{dirpath}' is not a directory."
    else:
        os.mkdir(dirpath)


@beartype.beartype
class VM:
    def __init__(self, db_path: str, contract_data_dir: str) -> None:
        self._db = AtomicTinyDB(db_path)
        self._contract_data_dir = pathlib.Path(contract_data_dir)
        self._contract_data_db_dir = self._contract_data_dir / "db"
        self._contract_data_lock_dir = self._contract_data_dir / ".lock"
        ensure_dir(self._contract_data_dir)
        ensure_dir(self._contract_data_db_dir)
        ensure_dir(self._contract_data_lock_dir)

    def transfer(self, sender: "Account", receiver: "Account", amount: Number):
        assert amount > 0, "Transfer amount must be positive"
        sender_balance = sender.balance
        sender_new_balance = sender_balance - amount
        if sender_new_balance > 0:
            # able to transact
            receiver_new_balance = receiver.balance + amount
            # this is atomic operation.
            self.set_balance(sender, sender_new_balance)
            self.set_balance(receiver, receiver_new_balance)

    def set_balance(self, account: "Account", balance: Number):
        assert balance >= 0, "Balance must be non-negative"
        doc_id = self.query_for_single_account_document_id(account)
        updated_ids = self._db.update(
            AccountVolatileInfo(balance=balance).dict(), doc_ids=[doc_id]
        )
        assert len(updated_ids) == 1, "Failed to set balance because of having "

    def query_for_single_account_document_id(self, account: "Account"):
        candidates = self._db.search(cond=tinydb.Query().address == account._address)
        if candidates == []:
            raise Exception("Account does not exist")
        elif len(candidates) == 1:
            return candidates[0].doc_id  # cause Document class is more than a dict
        else:
            raise Exception(f"Multiple accounts found for address '{account._address}'")

    def balance(self, account: "Account"):
        doc_id = self.query_for_single_account_document_id(account)
        document = self._db.get(doc_id=doc_id)
        balance = AccountInfo.parse_obj(document).balance
        return balance

    def get_contract_db_and_lock_filepaths(self, contract: "SmartContract"):

        address = contract._address
        contract_db_filepath = self._contract_data_db_dir / f"{address}.json"
        contract_lock_filepath = self._contract_data_lock_dir / f".{address}.lock"
        return contract_db_filepath, contract_lock_filepath

    def load_contract_data(self, contract: "SmartContract"):

        contract_db_filepath, contract_lock_filepath = (
            self.get_contract_db_and_lock_filepaths(contract)
        )
        if os.path.exists(contract_db_filepath):
            with filelock.FileLock(contract_lock_filepath):
                with open(contract_db_filepath, "r") as f:
                    # loaded_contract = typing.cast(SmartContract, dill.loads(f.read()))
                    data = typing.cast(dict, json.loads(f.read()))
                    return data

    def persist_contract_data(self, contract: "SmartContract"):
        """Update data of smart contract"""

        contract_db_filepath, contract_lock_filepath = (
            self.get_contract_db_and_lock_filepaths(contract)
        )

        with filelock.FileLock(contract_lock_filepath):
            data = contract.serialize()
            # you may need filelock.
            with open(contract_db_filepath, "w+") as f:
                f.write(data)

    def create_account(self, init_balance: Number = 0):
        assert init_balance >= 0, "Initial balance must be non-negative"
        account_static_info = generate_account_static_info()
        # private key
        self._db.insert(
            AccountInfo(**account_static_info.dict(), balance=init_balance).dict()
        )

        return Account(account_static_info.address, account_static_info.key, vm=self)

    def _engage(self):
        global _default_vm
        if _default_vm is None:
            _default_vm = self
        else:
            raise EngageException("VM already engaged")

    def _disengage(self):
        global _default_vm
        _default_vm = None

    @contextmanager
    def engage(self):
        try:
            self._engage()
            yield self
        finally:
            self._disengage()


# contract1 = vm.Contract() # create a new contract, no owner specified
# contract2 = vm.Contract(issuer) # create a new contract with issuer
# contract3 = vm.Contract(contract_address)
# contract4 = vm.Contract(unlocked_account)

# contract1.func1()
# contract1.func2()

# SmartContract[*ParamSpec]


# vm.create_contract(Contract1)(*contract1_init_arguments)
# vm.create_contract()
# account = vm.create_account()


@beartype.beartype
class Account:
    def __init__(
        self, address: str, key: Optional[str] = None, vm: Optional[VM] = None
    ):
        self._vm = get_vm_with_fallback(vm)
        self._address = address
        if key is not None:
            if not check_key_validity(address, key):
                raise Exception("Key invalid. Cannot create account.")
        self._key = key
        self._default_receipent = None

    def unlock(self, key: str):
        if self._key is not None:
            raise Exception("Account already unlocked")
        if check_key_validity(self._address, key):
            self._key = key
        else:
            raise Exception("Key invalid. Cannot unlock account.")

    def pay(self, amount: Number, recepient: Optional[Self] = None):
        if self._key is None:
            raise Exception("Account is not unlocked.")
        if recepient is None:
            if self._default_receipent is None:
                raise EngageException("Account not engaged")
            else:
                recepient = self._default_receipent
        self._vm.transfer(self, recepient, amount)

    @property
    def balance(self):
        return self._vm.balance(self)

    def _engage(self, recepient: Self):
        if self._default_receipent is not None:
            raise EngageException("Account already engaged")
        else:
            self._default_receipent = recepient

    def _disengage(self):
        self._default_receipent = None

    @contextmanager
    def engage(self, recepient: Self):
        try:
            self._engage(recepient)
            yield self
        finally:
            self._disengage()


class PersistantDataDict(dict):
    def __init__(self, contract: "SmartContract", data: dict = {}):
        self.contract = contract
        self.ISSUER_KEY = "_issuer"
        self.read_only_keys = [self.ISSUER_KEY]
        super().__init__(**data)

    def init_issuer(self, issuer: Account):
        with self.persist_context() as data_context:
            data_context[data_context.ISSUER_KEY] = issuer._address

    @contextmanager
    def persist_context(self):
        try:
            yield self
        finally:
            self.persist()

    def check_key_if_is_readonly(self, key):
        for it in self.read_only_keys:
            if key == it:
                if key in self.keys():
                    # this is readonly. refuse to set it again.
                    raise Exception(f"Cannot reset read-only key '{it}'")

    def __setitem__(
        self, key, value
    ):  # TODO: to handle nested statement like a[0][0] = 0, we need to use a contextmanager approach instead of this.
        self.check_key_if_is_readonly(key)
        super().__setitem__(key, value)
        self.persist()

    def __delitem__(self, key):
        super().__delitem__(key)
        self.persist()

    def persist(self):
        self.contract.store()

    # def __setattr__(self, name, value):
    #     self.contract.store()
    #     super().__setattr__(name, value)

    # def __getattribute__(self, name):
    #     self.contract.store()
    #     super().__getattribute__(name)

    # def __delattr__(self, name):
    #     self.contract.store()
    #     super().__delattr__(name)


# ref:
# https://docs.python.org/3/library/shelve.html
# https://docs.python.org/3/library/dbm.html
# https://github.com/dagnelies/pysos
# https://github.com/balena/python-pqueue (persistent queue)
# https://github.com/croqaz/Stones (with credits)
class SmartContract:  # anything done to a smart contract shall be stored.
    def __init__(
        self, address, issuer: Optional[Account] = None, vm: Optional[VM] = None
    ):
        # if contract found at address, just load it from dill.
        self._address = address
        self._issuer = issuer
        self._vm = get_vm_with_fallback(vm)

        self.load_data_and_register_issuer()

        # if contract not found at address, then create new one.
        self._serialized_data_history_hash = self._data_hash
        # self._account = Account(vm, issuer)
        self._default_account = None
        self.store()

    @classmethod
    def load(cls, address, issuer: Optional[Account] = None, vm: Optional[VM] = None):
        return cls(address=address, issuer=issuer, vm=vm)

    @classmethod
    def create(cls, address, issuer: Account, vm: Optional[VM] = None):
        return cls(address=address, issuer=issuer, vm=vm)

    def load_data_and_register_issuer(self):
        data = self._vm.load_contract_data(self)
        if data is not None:
            self._data = PersistantDataDict(self, data)
        else:
            self._data = PersistantDataDict(self, {})
            if self._issuer is not None:
                self.data.init_issuer(self._issuer)
            else:
                raise Exception("Cannot create new contract without specifying issuer")

    @property
    def data(self):
        return self._data

    def _engage(self, account: Account):
        if self._default_account is not None:
            raise EngageException("Contract already engaged")
        else:
            self._default_account = account

    def _disengage(self):
        self._default_account = None
        self.persist_contract_data()

    @contextmanager
    def engage(self, account: Account):
        try:
            self._engage(account)
            yield self
        finally:
            self._disengage()

    def serialize(self):
        # return dill.dumps(self)
        return json.dumps(self.data, ensure_ascii=False)

    def persist_contract_data(self):
        # submit to vm
        self._vm.persist_contract_data(self)

    @property
    def _data_hash(self):
        serialized_data = self.serialize()
        serialized_data_hash = hashlib.sha256(serialized_data.encode()).hexdigest()
        return serialized_data_hash

    def store(self):
        serialized_data_hash = self._data_hash
        if serialized_data_hash != self._serialized_data_history_hash:
            self.persist_contract_data()
            self._serialized_data_history_hash = serialized_data_hash
