import os


def ensure_dir(dir_path: str):
    if os.path.exists(dir_path):
        assert os.path.isdir(
            dir_path
        ), f"Path '{dir_path}' already exists and is not a directory"
    else:
        os.mkdir(dir_path)
