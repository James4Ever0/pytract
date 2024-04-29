"""Embedded EVM, using Simular as backend."""

import simular
from contextlib import contextmanager
import os
import typing

# from .locksmith import LockSmith


class AtomicEVM:
    """
    A persistant Embedded EVM.
    """

    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.load()

    def persist(self):
        snapshot = self.evm.create_snapshot()
        with open(self.storage_path, "w+") as f:
            f.write(snapshot)

    def load(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r") as f:
                snapshot = f.read()
                self.evm = simular.PyEvm.from_snapshot(snapshot)
        else:
            self.evm = simular.PyEvm()
            self.persist()

    @contextmanager
    def context(self):
        try:
            yield self.evm
        finally:
            self.persist()

    def call(
        self,
        fn_name: str,
        args: str,
        to: str,
        abi: "simular.PyAbi",
    ) -> object:
        """
        Transaction (read) operation to a contract at the given address `to`.
        This will NOT change state in the EVM.
        """
        with self.context() as evm:
            return evm.call(fn_name, args, to, abi)

    def simulate(
        self,
        fn_name: str,
        args: str,
        caller: str,
        to: str,
        value: int,
        abi: "simular.PyAbi",
    ) -> object:
        """
        Transaction operation to a contract at the given address `to`.
        This can simulate a transact/call operation, but will NOT change state in the EVM.
        """
        with self.context() as evm:
            return evm.simulate(fn_name, args, caller, to, value, abi)

    def deploy(self, args: str, caller: str, value: int, abi: "simular.PyAbi") -> str:
        """Deploy a contract"""
        with self.context() as evm:
            return evm.deploy(args, caller, value, abi)

    def transact(
        self,
        fn_name: str,
        args: str,
        caller: str,
        to: str,
        value: int,
        abi: "simular.PyAbi",
    ) -> object:  # TODO: figure out the return type, and the "py: Python<'_>" argument
        """
        Transaction (write) operation to a contract at the given address `to`.
        This will change state in the EVM.
        """
        with self.context() as evm:
            return evm.transact(fn_name, args, caller, to, value, abi)

    def create_snapshot(self) -> str:
        """Create a `SnapShot` of the current EVM state"""
        with self.context() as evm:
            return evm.create_snapshot()

    def create_account(
        self, address: str, balance: typing.Optional[int] = None
    ) -> None:
        """Create account with an initial balance"""
        with self.context() as evm:
            return evm.create_account(address, balance)

    def get_balance(self, address: str) -> int:
        """Get the balance of the given user"""
        with self.context() as evm:
            return evm.get_balance(address)

    def transfer(self, caller: str, to: str, amount: int) -> None:
        """Transfer the amount of value from `caller` to the given recipient `to`."""
        with self.context() as evm:
            return evm.transfer(caller, to, amount)
