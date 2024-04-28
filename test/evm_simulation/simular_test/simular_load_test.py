from simular_common import *

with open(STATEFILE_PATH, 'r') as f:
    evm = simular.PyEvm.from_snapshot(f.read())

# now check the address
balance = evm.get_balance(TEST_ACCOUNT_ADDRESS)

print("balance:", balance)
# balance: 1