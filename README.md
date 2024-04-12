# pytract

Smart contract Python API generator.

It works by interpreting smart contract ABI and generate corresponding Python API code.

## Usage

Install from PyPI:

```bash
pip install pytract
```

Create Python API code for your `brownie` project:

```bash
usage: pytract process [-h] project_path

positional arguments:
  project_path  Path of the project to process

optional arguments:
  -h, --help    show this help message and exit
```

And you shall import all available contracts and programmatically.

If your project folder name is `brownie_project` then write:

```python
from brownie_project.api import project_info, contracts

print(dir(contracts)) # list available contract classes
print(dir(project_info)) # list project info attributes
```

Note the difference of using it with `brownie` alone, you now have a fully portable python package, which you can write static typed code without the need for copying and pasting from `brownie console`.

You can view all generated API code under folder `<your brownie project>/api`.

Example generated contract API class is given below:

```python
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


```

## Roadmap

- [x] Create a binding to smart contract and APIs for Brownie
