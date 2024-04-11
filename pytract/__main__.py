from .abi2api import generate_api_code_for_project
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Generate API code for a given project"
    )
    parser.add_argument("process", nargs=1, help="Project path to process", type=str)
    arguments = parser.parse_args()
    project_path = arguments.process[0]
    generate_api_code_for_project(project_path)
