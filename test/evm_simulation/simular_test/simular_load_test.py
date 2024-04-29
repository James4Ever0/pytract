from simular_common import *

with open(STATEFILE_PATH, 'r') as f: # working!
    evm = simular.PyEvm.from_snapshot(f.read())

    # now check the address
    show_balance(evm=evm)
