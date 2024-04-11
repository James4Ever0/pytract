import brownie
from brownie.network.contract import ContractContainer  # , InterfaceConstructor
from brownie.project.main import Project
from brownie.network.account import Account
import pydantic
from typing import Dict, List, Optional
from constants import *
from utils import *

# can you pay to a contract? or is it always payable?


class ParamType(pydantic.BaseModel):
    type: str
    name: str
    internalType: str


class ContractABI(pydantic.BaseModel):
    inputs: List[ParamType] = []
    outputs: List[ParamType] = []
    type: Optional[str] = None
    stateMutability: Optional[str] = None
    name: Optional[str] = None


class ContractTemplateInfo(pydantic.BaseModel): ...


class ContractDeployParameters(pydantic.BaseModel):
    issuer: Account  # can you validate that in pydantic? otherwise just use normal class instead, or beartype it.
    args: List = []
    kwargs: Dict = {}

    @pydantic.validator("kwargs")
    def validate_kwargs(self, kwargs: dict):
        ret = {}
        for k, v in kwargs.items():
            if k == CONTRACT_DEPLOYER_KEY:
                print(
                    f"Warning: '{CONTRACT_DEPLOYER_KEY}' detected in kwargs, which will be skipped. You should pass it to 'issuer' instead"
                )
                continue
            else:
                ret[k] = v
        return ret

    def to_args(self):
        args = (*self.args, {CONTRACT_DEPLOYER_KEY: self.issuer, **self.kwargs})
        return args


# Account.deploy()
# brownie.accounts

# it is using setattr under the hood, to create methods for deployed contracts.


def parse_abi(abi: dict):
    abi_serialized = ContractABI.parse_obj(abi)
    # usually function is of our interest.
    if abi_serialized.type == FUNCTION_TYPE:
        for it in abi_serialized.inputs:
            print("input param name:", it.name, "type:", it.type)


def parse_abi_list(abi_list: List[dict]):
    for it in abi_list:
        parse_abi(it)


def load_project_and_generate_api_code(project_path: str):
    # generate api code for every possible contract
<<<<<<< HEAD
    # for every contract one can load, deploy and call method
    # you should mark the absolute path of the contract source file in the generated api code.

    proj = project.load(project_path)

    # write to <project_path>/api
    api_path = os.path.join(project_path, "api")
=======
    # for every contract one can load, deploy and call meth  # this is the constructor abi, which can be used for getting all allowed parameters.od
    # you should mark the absolute path of the contract source file in the generated api code.

    project: Project = brownie.project.load(project_path)

    contracts: Dict[str, ContractContainer] = project.dict()

    # interfaces: Dict[str, InterfaceConstructor] = {
    #     key: value
    #     for key, value in project.interface.__dict__.items()
    #     if not key.startswith("_")
    # }

    for it in contracts.values():
        # it.deploy()  # how to deploy successfully?
        abi = ContractABI.parse_obj(it.deploy.abi)
        abi.inputs  # this is the constructor abi, which can be used for getting all allowed parameters.
        # constructor does not return anything.
        # actually calling account.deploy
        # it.deploy() # what will it return, if success?
        # parse_abi(it.abi)
        ...

    # write to '<project_path>/api'
    api_code_directory_path = os.path.join(project_path, API_RELATIVE_DIR)
    ensure_dir(api_code_directory_path)
>>>>>>> e28706b (update)
