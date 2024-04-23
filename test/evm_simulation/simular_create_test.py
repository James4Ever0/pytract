from simular_common import *

simular.create_account(evm, address=TEST_ACCOUNT_ADDRESS, value = 1)
# print(account_address)

with open(STATEFILE_PATH, 'w+') as f:
    f.write(evm.create_snapshot())