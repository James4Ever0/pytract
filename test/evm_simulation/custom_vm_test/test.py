# import sys

# sys.path.append("../../../")
import pytract
import os
import shutil

# TODO: setup named account and contracts, accessible by name locally, so each user can lookup their own account/contract database via name without disturbing privacy

# def simple_decorator(func):
#     def decorated_func(*args, **kwargs):
#         print("Args:", args)
#         print('Kwargs:', kwargs)
#         return func(*args, **kwargs)
#     return decorated_func

class TestContract(pytract.vm.SmartContract):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def calculate(self, a: int, b: int):
        return a + b
    
    # @pytract.vm.payable
    @pytract.vm.payable
    def make_donation(self):
        print("Donation from:", self._caller_account)
        print("Donation amount:", self._transfer_amount)


def main():
    db_path = os.path.abspath("./db.json")
    contract_data_dir = os.path.abspath("./contract_data")

    def test():
        vm = pytract.vm.VM(db_path, contract_data_dir)
        account_1 = vm.create_account(init_balance=10)
        account_2 = vm.create_account(init_balance=2)

        contract_1 = TestContract.create(
            issuer=account_1,
            vm=vm,
        )
        # breakpoint()

        with contract_1.receive(1, account_1) as contract:
            print("Transfer amount:", contract._transfer_amount)

        # with contract_1.engage(account_1) as contract:
        #     with contract.receive(1) as cont:
        
        contract_1.make_donation(account_1, 1)

        print("Contract balance:", contract_1.balance)

        def check_balance():
            print("Account 1:", account_1.balance)
            print("Account 2:", account_2.balance)

        def main_test():
            print("Before pay:")
            check_balance()
            print()
            account_1.pay(2, account_2)
            print("After pay:")
            check_balance()

        main_test()

    def test_and_cleanup():
        try:
            test()
        finally:
            os.remove(db_path)
            shutil.rmtree(contract_data_dir)

    test_and_cleanup()


if __name__ == "__main__":
    main()
