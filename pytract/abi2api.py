from brownie import project
from brownie.network.contract import (
    ContractContainer,
    ProjectContract,
)  # , InterfaceConstructor
from brownie.project.main import Project
from brownie.network.account import Account
import pydantic
from typing import Dict, List, Optional, cast
from constants import *
from utils import *

# can you pay to a contract? or is it always payable?


class TransactionParameters(pydantic.BaseModel):
    issuer: Account
    """The Account that the transaction it sent from. If not given, the transaction is sent from the account that deployed the contract."""

    gas_limit: ...
    """The amount of gas provided for transaction execution, in wei. If not given, the gas limit is determined using web3.eth.estimate_gas."""

    gas_buffer: ...
    """A multiplier applied to web3.eth.estimate_gas when setting gas limit automatically. gas_limit and gas_buffer cannot be given at the same time."""

    gas_price: ...
    """The gas price for legacy transaction, in wei. If not given, the gas price is set according to web3.eth.gas_price."""

    max_fee: ...
    """Max fee per gas of dynamic fee transaction."""

    priority_fee: ...
    """Max priority fee per gas of dynamic fee transaction."""

    amount: ...
    """The amount of Ether to include with the transaction, in wei."""

    nonce: ...
    """The nonce for the transaction. If not given, the nonce is set according to web3.eth.get_transaction_count while taking pending transactions from the sender into account."""

    required_confs: ...
    """The required confirmations before the TransactionReceipt is processed. If none is given, defaults to 1 confirmation. If 0 is given, immediately returns a pending TransactionReceipt, while waiting for a confirmation in a separate thread."""

    allow_revert: ...
    """Boolean indicating whether the transaction should be broadcasted when it is expected to revert. If not set, the default behaviour is to allow reverting transactions in development and disallow them in a live environment."""


class ContractProperties(pydantic.BaseModel):
    @classmethod
    def from_deployed(
        cls, deployed_contract: ProjectContract, issuer: Optional[Account] = None
    ):
        return cls()


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


class FunctionInfo(pydantic.BaseModel):
    inputs: List[ParamType] = []
    outputs: List[ParamType] = []
    name: str


class ContractInfo(pydantic.BaseModel):
    contract_container: ContractContainer
    abi_list: List[ContractABI]
    deploy_abi: ContractABI
    function_info_list: List[FunctionInfo] = []


class ContractInstance:
    _project: Project
    _contract_info: ContractInfo

    def __init__(
        self, deployed_contract: ProjectContract, issuer: Optional[Account] = None
    ):  # to create you need to either deploy or load contract by address
        self._deployed_contract = deployed_contract
        self.properties = ContractProperties.from_deployed(
            deployed_contract=self._deployed_contract, issuer=issuer
        )


class ProjectInfo(pydantic.BaseModel):
    project: Project
    contracts_info: Dict[str, ContractInfo]


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


def parse_abi(abi: dict) -> ContractABI:
    abi_serialized = ContractABI.parse_obj(abi)
    return abi_serialized


def parse_function_info(abi: ContractABI) -> Optional[FunctionInfo]:
    # usually function is of our interest.
    if abi.type == FUNCTION_TYPE:
        return FunctionInfo(
            inputs=abi.inputs, outputs=abi.outputs, name=cast(str, abi.name)
        )


def parse_function_info_list(abi_list: List[ContractABI]) -> List[FunctionInfo]:
    ret = []
    for abi in abi_list:
        function_info = parse_function_info(abi)
        if function_info is not None:
            ret.append(function_info)
    return ret


def parse_abi_list(abi_list: List[dict]) -> List[ContractABI]:
    ret = []
    for it in abi_list:
        ret.append(parse_abi(it))
    return ret


# def load_project_and_generate_api_code(project_path: str):


def load_project_and_get_project_info(project_path: str):
    # generate api code for every possible contract
    # for every contract one can load, deploy and call meth  # this is the constructor abi, which can be used for getting all allowed parameters.od
    # you should mark the absolute path of the contract source file in the generated api code.

    _project: Project = project.load(project_path)

    contracts: Dict[str, ContractContainer] = _project.dict()
    ContractContainer.at

    contracts_info: Dict[str, ContractInfo] = {}

    # interfaces: Dict[str, InterfaceConstructor] = {
    #     key: value
    #     for key, value in project.interface.__dict__.items()
    #     if not key.startswith("_")
    # }

    for k, v in contracts.items():
        # it.deploy()  # how to deploy successfully?
        deploy_abi = parse_abi(v.deploy.abi)
        abi_list = parse_abi_list(v.abi)
        function_info_list = parse_function_info_list(abi_list)
        contracts_info[k] = ContractInfo(
            contract_container=v,
            abi_list=abi_list,
            deploy_abi=deploy_abi,
            function_info_list=function_info_list,
        )
        # abi.inputs  # this is the constructor abi, which can be used for getting all allowed parameters.
        # constructor does not return anything.
        # actually calling account.deploy
        # it.deploy() # what will it return, if success?
        # parse_abi(it.abi)

    project_info = ProjectInfo(project=_project, contracts_info=contracts_info)
    return project_info

    # # write to '<project_path>/api'
    # api_code_directory_path = os.path.join(project_path, API_RELATIVE_DIR)
    # ensure_dir(api_code_directory_path)
