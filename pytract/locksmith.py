from .utils import AtomicKVStore, generate_address_and_key, check_key_validity
import typing


class LockSmith:
    """Create and store Web3 accounts by name"""

    # """Create and store Web3 accounts and contracts by name"""
    def __init__(self, db_path: str):
        self.db = AtomicKVStore(db_path)

    def account(self, name: str):
        account = self.load_account(name)
        if account is None:
            account = self.create_account(name)
        return account

    def load_account(self, name: str):
        try:
            account = self.db.get(name)
            return account
        except KeyError:
            print(f"Account '{name}' does not exist.")

    def create_account(self, name: str):
        address, key = generate_address_and_key()
        ret = self.import_account(name, address, key)
        return ret

    def import_account(self, name: str, address: str, key: typing.Optional[str] = None):
        if key is not None:
            check_key_validity(address, key, enforce=True)
        ret = dict(address=address, key=key)
        self.db.set(name, ret)
        return ret

    # def new_contract(self, name:str):
    #     ...

    # def list_all(self):
    #     self.list_accounts()
    #     self.list_contracts()

    def list_accounts(self):
        return list(self.db.data.keys())

    # def list_contracts(self):
    #     ...
