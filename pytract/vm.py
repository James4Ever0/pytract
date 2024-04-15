# smart contract web3 virtual machine
import tinydb
import abc
import pydantic
import web3
import beartype
from typing_extensions import Self, Optional, Literal
from contextlib import contextmanager
import os
import pathlib

def create_tinydb(db_path: str):
    return tinydb.TinyDB(db_path)


_default_vm: Optional["VM"] = None


class EngageException(Exception): ...


class AccountBase(pydantic.BaseModel):
    type: Literal["account"] = "account"


class AccountStaticInfo(pydantic.BaseModel):
    address: str
    key: str


class AccountVolatileInfo(pydantic.BaseModel):
    balance: float

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


class VM:
    def __init__(self, db_path: str, contract_data_dir: str) -> None:
        self._db = create_tinydb(db_path)
        self._contract_data_dir = pathlib.Path(contract_data_dir)
        self._contract_data_db_dir = self._contract_data_dir / 'db'
        self._contract_data_lock_dir = self._contract_data_dir / '.lock'

    def transfer(self, sender: "Account", receiver: "Account", amount: float):
        assert amount > 0, "Transfer amount must be positive"
        sender_balance = sender.balance
        sender_new_balance = sender_balance - amount
        if sender_new_balance > 0:
            # able to transact
            receiver_new_balance = receiver.balance + amount
            # this is atomic operation.
            self.set_balance(sender, sender_new_balance)
            self.set_balance(receiver, receiver_new_balance)

    def set_balance(self, account: "Account", balance: float):
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
            return candidates[0].doc_id # cause Document class is more than a dict
        else:
            raise Exception(f"Multiple accounts found for address '{account._address}'")

    def balance(self, account: "Account"):
        doc_id = self.query_for_single_account_document_id(account)
        document = self._db.get(doc_id=doc_id)
        balance = AccountInfo.parse_obj(document).balance
        return balance

    def update(self, contract: "SmartContract"):
        """Update data of smart contract"""
        address = contract._address
        contract_data_filepath = self._contract_data_db_dir/f"{address}.json"
        contract_data_filepath = self._contract_data_lock_dir/ f".{address}.lock"
        data = contract._export_data()
        # you may need filelock.
        with open(contract_data_filepath, 'w+') as f:
            f.write(data)

    def create_account(self, init_balance: float = 0):
        assert init_balance >= 0, "Initial balance must be non-negative"
        account = web3.Account.create()
        address = account.address
        key = account.key.hex()  # private key
        self._db.insert(
            AccountInfo(address=address, key=key, balance=init_balance).dict()
        )
        return Account(address, key, vm=self)

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
def check_key_validity(address: str, key: str):
    ret = False
    try:
        account = web3.Account.from_key(key)
        assert account.address == address, f"Key '{key}' is not for address '{address}'"
        ret = True
    except:
        pass
    return ret


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

    def pay(self, amount: int, recepient: Optional[Self] = None):
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
        self._vm.balance(self)

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


class SmartContract(abc.ABC):  # anything done to a smart contract shall be stored.
    _data: pydantic.BaseModel
    _subcontracts: dict[str, Self]  # this is something also need to be stored.

    def __setattr__(self, name, value):
        if name != "_data":
            raise AttributeError("Cannot set attribute directly")
        else:
            super().__setattr__(name, value)

    def __getattr__(self, name): ...

    def __init__(
        self, address, issuer: Optional[Account] = None, vm: Optional[VM] = None
    ):
        self._vm = get_vm_with_fallback(vm)
        self._address = address

        # self._account = Account(vm, issuer)
        self._serialized_data_history = self.serialize()
        self._default_account = None
        self._issuer = issuer

    def _engage(self, account: Account):
        if self._default_account is not None:
            raise EngageException("Contract already engaged")
        else:
            self._default_account = account

    def _disengage(self):
        self._default_account = None

    @contextmanager
    def engage(self, account: Account):
        try:
            self._engage(account)
            yield self
        finally:
            self._disengage()

    def serialize(self):
        return self._data.json()

    def update(self):
        # submit to vm
        self._vm.update(self)

    def store(self):
        serialized_data = self.serialize()
        if serialized_data != self._serialized_data_history:
            self.update()
            self._serialized_data_history = serialized_data
