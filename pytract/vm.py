# smart contract web3 virtual machine
import tinydb
import abc
import pydantic
import web3
import beartype
from typing_extensions import Self

def create_vm(db_path: str):
    tinydb.TinyDB(db_path)

class VM:...

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

class Account:
    def __init__(self, vm:VM, address):
        self._vm = vm
    def pay(self, recepient:Self, amount:int):
        ...
    @property
    def balance(self):
        ...
class SmartContract(abc.ABC):  # anything done to a smart contract shall be stored.
    data: pydantic.BaseModel

    def __init__(self, vm: VM, address):
        self._vm = vm
        self._serialized_data_history = self.serialize()

    def engage(self, caller_address): ...

    def serialize(self):
        return self.data.json()

    def update(self): ...

    def store(self):
        serialized_data = self.serialize()
        if serialized_data != self._serialized_data_history:
            self.update()
            self._serialized_data_history = serialized_data
