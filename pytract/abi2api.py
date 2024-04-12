from brownie import project
from brownie.network.contract import (
    ContractContainer,
    ProjectContract,
    Contract,
)  # , InterfaceConstructor
from brownie.project.main import Project
from brownie.network.account import Account
import pydantic
from typing import Dict, List, Optional, cast, Union
from .constants import *
from .utils import *
import inspect
import functools
import jinja2
from pathlib import Path
import abc
import black
import black.mode

# can you pay to a contract? or is it always payable?

_TEMPLATE_DIR = Path(os.path.dirname(__file__)) / "templates"
_API_TEMPLATE_PATH = _TEMPLATE_DIR / "api.py.j2"


class BaseConfig(pydantic.BaseModel):
    class Config:
        arbitrary_types_allowed = True


class TransactionMandatoryParameters(BaseConfig):
    issuer: Account
    """The Account that the transaction it sent from. If not given, the transaction is sent from the account that deployed the contract."""


class TransactionOptionalParameters(pydantic.BaseModel):

    gas_limit: Optional[int] = None
    """The amount of gas provided for transaction execution, in wei. If not given, the gas limit is determined using web3.eth.estimate_gas."""

    gas_buffer: Optional[int] = None
    """A multiplier applied to web3.eth.estimate_gas when setting gas limit automatically. gas_limit and gas_buffer cannot be given at the same time."""

    gas_price: Optional[int] = None
    """The gas price for legacy transaction, in wei. If not given, the gas price is set according to web3.eth.gas_price."""

    max_fee: Optional[int] = None
    """Max fee per gas of dynamic fee transaction."""

    priority_fee: Optional[int] = None
    """Max priority fee per gas of dynamic fee transaction."""

    amount: Optional[int] = None
    """The amount of Ether to include with the transaction, in wei."""

    nonce: Optional[int] = None
    """The nonce for the transaction. If not given, the nonce is set according to web3.eth.get_transaction_count while taking pending transactions from the sender into account."""

    required_confs: Optional[int] = None  # positive
    """The required confirmations before the TransactionReceipt is processed. If none is given, defaults to 1 confirmation. If 0 is given, immediately returns a pending TransactionReceipt, while waiting for a confirmation in a separate thread."""

    allow_revert: Optional[bool] = None
    """Boolean indicating whether the transaction should be broadcasted when it is expected to revert. If not set, the default behaviour is to allow reverting transactions in development and disallow them in a live environment."""


class TransactionParameters(
    TransactionMandatoryParameters, TransactionOptionalParameters
):

    @property
    def kwargs(self):
        return {k: v for k, v in self.dict().items() if v is not None}

    @property
    def optional_kwargs(self):
        return {k: v for k, v in self.kwargs.items() if k != "issuer"}

    def to_contract_deploy_parameters(self, args: list = []):
        parameters = ContractDeployParameters(
            issuer=self.issuer, args=args, kwargs=self.optional_kwargs
        )
        return parameters


class FallbackException(Exception): ...


class FunctionBase:
    def __init__(
        self,
        contract: Union[Contract, ProjectContract],
        txparams: Optional[TransactionParameters],
    ):
        self._contract = contract
        """Smart contract instance with callable functions."""
        self._txparams = txparams
        """Default transation parameters to use in function calls, if not given."""

    def txparams_with_fallback(
        self, txparams: Optional[TransactionParameters]
    ) -> TransactionParameters:
        if txparams is not None:
            return txparams
        elif self._txparams is not None:
            return self._txparams
        else:
            raise FallbackException(
                "Both given txparams and default txparams are empty."
            )


class ContractProperties(BaseConfig):
    contract: Union[Contract, ProjectContract]
    issuer: Account

    @classmethod
    def from_contract(cls, contract: Union[ProjectContract, Contract], issuer: Account):
        return cls(contract=contract, issuer=issuer)


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
    stateMutability: Optional[str] = None


class ContractInfo(BaseConfig):
    contract_container: ContractContainer
    abi_list: List[ContractABI]
    deploy_abi: ContractABI
    function_info_list: List[FunctionInfo] = []


# TODO: resolve external contract abi and generate api code for them


class ContractInstance(abc.ABC):
    """
    Abstract contract instance class. You should never instantiate it directly.
    """

    _project: Project
    _contract_info: ContractInfo
    _contract_name: str

    def __init__(
        self,
        contract: Union[ProjectContract, Contract],
        issuer: Optional[Account] = None,
    ):  # to create you need to either deploy or load contract by address
        self._contract = contract
        if issuer is None:
            issuer = cast(Account, contract.tx.sender)
        self.properties = ContractProperties.from_contract(
            contract=self._contract, issuer=issuer
        )

    @classmethod
    def from_address(cls, address: str):
        contract = Contract.from_abi(
            cls._contract_name, address, cls._contract_info.contract_container.abi
        )
        ret = cls(contract=contract)
        return ret


class ProjectInfo(BaseConfig):
    project: Project
    contracts_info: Dict[str, ContractInfo]


class ContractDeployParameters(BaseConfig):
    issuer: Account  # can you validate that in pydantic? otherwise just use normal class instead, or beartype it.
    args: List = []
    kwargs: Dict = {}

    @pydantic.validator("kwargs")
    def validate_kwargs(cls, kwargs: dict):
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
            inputs=abi.inputs,
            outputs=abi.outputs,
            name=cast(str, abi.name),
            stateMutability=abi.stateMutability,
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


def load_project_info_for_api():
    """Load the project info for the API script inside any brownie project folder."""
    caller_source_path = inspect.stack()[1].filename

    script_abspath = os.path.abspath(caller_source_path)
    project_path = functools.reduce(
        lambda x, _: os.path.dirname(x), range(2), script_abspath
    )

    project_info = load_project_and_get_project_info(project_path)
    return project_info


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


def get_names_from_list(obj):
    return [param.name for param in obj]


def get_types_from_list(obj):
    return [param.type for param in obj]


def check_function_type_not_pure(function_type):
    return function_type not in ["view", "pure"]


def generate_api_code_for_project(project_path: str):

    # write to '<project_path>/api'
    project_info = load_project_and_get_project_info(project_path)

    api_code_directory_path = os.path.join(project_path, API_RELATIVE_DIR)
    ensure_dir(api_code_directory_path)

    with open(os.path.join(api_code_directory_path, "_contracts.py"), "w+") as f:
        template = jinja2.Template(
            open(_API_TEMPLATE_PATH).read(),
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=jinja2.StrictUndefined,
        )
        template.globals.update(
            dict(
                get_names_from_list=get_names_from_list,
                get_types_from_list=get_types_from_list,
                check_function_type_not_pure=check_function_type_not_pure,
                list=list,
            )
        )
        content = template.render(project_info=project_info)
        content = black.format_str(content, mode=black.mode.Mode())
        f.write(content)

    with open(os.path.join(api_code_directory_path, "contracts.py"), "w+") as f:
        content = """from ._contracts import *"""
        f.write(content)

    with open(os.path.join(api_code_directory_path, "__init__.py"), "w+") as f:
        content = """from . import contracts
from ._project import project_info"""
        f.write(content)

    with open(os.path.join(api_code_directory_path, "_project.py"), "w+") as f:
        content = """from pytract import abi2api
project_info = abi2api.load_project_info_for_api()"""
        f.write(content)

    with open(os.path.join(project_path, "__init__.py"), "w+") as f:
        content = """from . import api"""
        f.write(content)
