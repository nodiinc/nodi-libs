from time import strftime, localtime
import os
import shutil

def get_files_only(dir: str) -> list:
    files = []
    for entry in os.listdir(dir):
        if os.path.isfile(os.path.join(dir, entry)):
            files.append(entry)
    return files

def get_dirs_only(dir: str) -> list:
    directories = []
    for entry in os.listdir(dir):
        if os.path.isdir(os.path.join(dir, entry)):
            directories.append(entry)
    return directories

def move_files_only(dir_from: str,
                    dir_to: str,
                    files_target: list[str] = None) -> int:
    count = 0
    if files_target is None:
        files_target = os.listdir(dir_from)
    for file_name in files_target:
        path_from = os.path.join(dir_from, file_name)
        if os.path.isfile(path_from):
            path_to = os.path.join(dir_to, file_name)
            shutil.move(path_from, path_to)
            count += 1
    return count

def copy_files_only(dir_from: str,
                    dir_to: str,
                    files_target: list[str] = None) -> int:
    count = 0
    if files_target is None:
        files_target = os.listdir(dir_from)
    for file_name in files_target:
        path_from = os.path.join(dir_from, file_name)
        if os.path.isfile(path_from):
            path_to = os.path.join(dir_to, file_name)
            shutil.copy(path_from, path_to)
            count += 1
    return count

def remove_files_only(dir_target: str,
                      files_target: list[str] = None) -> int:
    count = 0
    if files_target is None:
        files_target = os.listdir(dir_target)
    for file_name in files_target:
        path_target = os.path.join(dir_target, file_name)
        if os.path.isfile(path_target):
            os.remove(path_target)
            count += 1
    return count

def backup_files(dir_target: str,
                 files_target: list[str] = None,
                 time_given: str = None,
                 remove_original: bool = True) -> int:
    
    # If target files specified, list them
    if files_target:
        files_listed = []
        for file in files_target:
            file_path = os.path.join(dir_target, file)
            if os.path.isfile(file_path):
                files_listed.append(file)
    
    # If target files not specified, list all
    else:
        files_listed = get_files_only(dir_target)
    
    # If time given, use it
    if time_given:
        time_backup = time_given
    
    # If time not give, get current time
    else:
        time_backup = strftime('%y%m%d_%H%M%S', localtime())
    
    # Create backup dir
    dir_backup = f'{dir_target}/.bak_{time_backup}'
    os.makedirs(dir_backup, exist_ok=True)
    
    # If remove original, move files
    count = 0
    if remove_original:
        count = move_files_only(dir_target, dir_backup, files_listed)
    
    # If not remove original, copy files
    else:
        count = copy_files_only(dir_target, dir_backup, files_listed)
    
    # Return count
    return count