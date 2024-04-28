import sys
sys.path.append('../../../')
import pytract
import os

db_path = os.path.abspath('./db')
contract_data_dir= os.path.abspath('./contract_data')


vm = pytract.vm.VM(db_path,contract_data_dir)
