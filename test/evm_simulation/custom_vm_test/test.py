# import sys

# sys.path.append("../../../")
import pytract
import os
import shutil
# TODO: setup named account and contracts, accessible by name locally, so each user can lookup their own account/contract database via name without disturbing privacy


def main():
    db_path = os.path.abspath("./db.json")
    contract_data_dir = os.path.abspath("./contract_data")

    def test():
        vm = pytract.vm.VM(db_path, contract_data_dir)
        account_1 = vm.create_account(init_balance=10)
        account_2 = vm.create_account(init_balance=2)
        # breakpoint()

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
