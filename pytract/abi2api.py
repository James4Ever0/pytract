from brownie import project
import os


def load_project_and_generate_api_code(project_path: str):
    # generate api code for every possible contract
    # for every contract one can load, deploy and call method
    # you should mark the absolute path of the contract source file in the generated api code.

    proj = project.load(project_path)

    # write to <project_path>/api
    api_path = os.path.join(project_path, "api")
