from .abi2api import generate_api_code_for_project
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Generate API code for a given project"
    )

    # Create subparsers for different keywords
    subparsers = parser.add_subparsers(dest='keyword', title='Keywords', metavar='<keyword>')

    # Subparser for the 'set' keyword
    set_parser = subparsers.add_parser('process', help='Process a given project')
    set_parser.add_argument('project_path', type=str, help='Path of the project to process')

    arguments = parser.parse_args()
    if arguments.keyword == 'process':
        project_path = arguments.project_path
        generate_api_code_for_project(project_path)
    else:
        raise Exception(f"Invalid keyword argument: '{arguments.keyword}'")
