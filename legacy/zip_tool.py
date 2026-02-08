import tarfile
import os

def zip_to_targz(input_files: list, targz_path: str) -> None:
    """Compress files to tar.gz"""
    with tarfile.open(targz_path, "w:gz") as tar:
        for input in input_files:
            if os.path.exists(input):
                tar.add(input, arcname=os.path.basename(input))

def unzip_from_targz(targz_path: str, output_dir: str) -> None:
    """Decompress tar.gz to files"""
    if not os.path.exists(output_dir):
        os.system(f'mkdir {output_dir} -p')
    with tarfile.open(targz_path, "r:gz") as tar:
        tar.extractall(path=output_dir)