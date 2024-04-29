from simular_common import *

evm.create_account( address=TEST_ACCOUNT_ADDRESSES[0], balance = 10)
evm.create_account( address=TEST_ACCOUNT_ADDRESSES[1], balance = 10)

show_balance()
print()

evm.transfer(TEST_ACCOUNT_ADDRESSES[0], TEST_ACCOUNT_ADDRESSES[1], 1)

show_balance()

# but you do not have key, therefore there is no access control.
# you may add one extra layer of security via valid ethereum address and keys.

# print(account_address)

with open(STATEFILE_PATH, 'w+') as f:
    f.write(evm.create_snapshot())