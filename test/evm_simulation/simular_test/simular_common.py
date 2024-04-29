import simular
import string

# create an account with initial balance of 1 wei, test if it can persist

evm = simular.PyEvm()
# ['call', 'create_account', 'create_snapshot', 'deploy', 'from_fork', 'from_snapshot', 'get_balance', 'simulate', 'transact', 'transfer']

STATEFILE_PATH = "state.json"

# total 16 items
TEST_ACCOUNT_ADDRESSES = [
    f"0x04dca00d0a8a6dcb7cb8ba43219b46603d66e96{it}"
    for it in string.digits + 'abcdef'
]


def show_balance(evm=evm):
    print("Account 0:", TEST_ACCOUNT_ADDRESSES[0], evm.get_balance(TEST_ACCOUNT_ADDRESSES[0]))
    print("Account 1:", TEST_ACCOUNT_ADDRESSES[1], evm.get_balance(TEST_ACCOUNT_ADDRESSES[1]))
