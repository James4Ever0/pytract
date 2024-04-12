from brownie.network.account import Account
from brownie.network.contract import Contract, ProjectContract
from pytract import abi2api
from typing import Optional, Union
from ._project import project_info


class Faucet(abi2api.ContractInstance):
    _project = project_info.project
    _contract_info = project_info.contracts_info["Faucet"]
    _contract_name = "Faucet"

    class Function(abi2api.FunctionBase):
        def returnVars(
            self,
        ):
            """
            Function Type: pure

            Inputs:
                (No parameters)

            Outputs:
                (uint256, uint256, uint256)
            """
            values = self._contract.returnVars()
            return values

        def withdraw(
            self,
            withdraw_amount,
            _txparams: Optional[abi2api.TransactionParameters] = None,
        ):
            """
            Function Type: nonpayable

            Inputs:
                withdraw_amount: uint256

            Outputs:
                (No parameters)
            """
            values = self._contract.withdraw(
                withdraw_amount, self.txparams_with_fallback(_txparams).dict()
            )
            return values

    def __init__(
        self,
        contract: Union[Contract, ProjectContract],
        issuer: Optional[Account] = None,
        _txparams: Optional[abi2api.TransactionParameters] = None,
    ):  # to create you need to either deploy or load contract by address
        super().__init__(contract, issuer)
        self.function = self.Function(contract, _txparams)
        """
        Available functions of this smart contract.
        """

    @classmethod
    def deploy(cls, _txparams: abi2api.TransactionParameters):
        """
        Inputs:
            transaction_parameters: TransactionParameters

        Output:
            contract: Faucet
        """
        args = []

        parameters = _txparams.to_contract_deploy_parameters(args)

        deployed_contract: ProjectContract = cls._contract_info.contract_container.deploy(*parameters.to_args())  # type: ignore

        return cls(deployed_contract, _txparams.issuer, _txparams)


__all__ = ["Faucet"]
