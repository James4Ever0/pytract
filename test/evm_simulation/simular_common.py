import simular

# create an account with initial balance of 1 wei, test if it can persist

evm = simular.PyEvm()

# ]'call', 'create_account', 'create_snapshot', 'deploy', 'from_fork', 'from_snapshot', 'get_balance', 'simulate', 'transact', 'transfer']

STATEFILE_PATH = "state.json"

TEST_ACCOUNT_ADDRESS = "0x04dca00d0a8a6dcb7cb8ba43219b46603d66e96f"