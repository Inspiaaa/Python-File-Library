
from __future__ import annotations
from typing import Callable, List, Tuple, Union, Any
from datetime import datetime

import os
import re
import shutil
import subprocess


class SafeGuard:
    """
    An internal class used to avoid dangerous mishaps (e.g. "delete the c drive please")
    """

    _ENABLED = True
    _PROTECT_DEPTH = 7

    @staticmethod
    def enable() -> None:
        """
        Enables the SafeGuard
        """
        SafeGuard._ENABLED = True

    @staticmethod
    def disable() -> None:
        SafeGuard._ENABLED = False

    @staticmethod
    def is_enabled() -> bool:
        return SafeGuard._ENABLED

    @staticmethod
    def get_protect_depth() -> int:
        return SafeGuard._PROTECT_DEPTH

    @staticmethod
    def warn(path: str, op: str) -> None:
        """
        Warns the user that a very "low level" folder / file is going to be deleted or renamed

        :param path: The path that is being accessed
        :param op: The operation performed on the file / folder
        """

        if SafeGuard._ENABLED:
            print(f"\n[FL.SAFEGUARD]: You are attempting to {op.upper()} {path}")
            print(f"To continue the program, type 'continue' without the inverted commas")
            print(f"If this message is not needed, the SafeGuard can be disabled with fl.SafeGuard.disable()\n")

            response = input(">> ")
            if response != "continue":
                quit()


class Folder:
    """
    FileLibrary Folder type to allow high level operations on folders
    """

    def __init__(self, path=None):
        self.path: str = os.path.abspath(path)

    def __repr__(self):
        return f"Folder({self.path})"

    def __str__(self):
        return self.beautify()

    def beautify(self) -> str:
        """
        Returns a text tree visualization of the folder structure
        """

        def beautify_walk(path: str, depth: int) -> str:
            out = str()

            entries = [e for e in os.scandir(path)]
            for i, e in enumerate(entries):
                if e.is_dir():
                    out += "{}├── {}\n".format("│   " * (depth - 1), e.name)
                    out += beautify_walk(e.path, depth + 1)
                else:
                    if i != len(entries) - 1:
                        out += "{}├── {}\n".format("│   " * (depth - 1), e.name)
                    else:
                        out += "{}└── {}\n".format("│   " * (depth - 1), e.name)

            return out

        beautified = self.get_name() + "\n"
        beautified += beautify_walk(self.path, 1)

        return beautified

    def print_beautified(self) -> None:
        """
        Returns a text tree visualization of the folder structure
        """

        def beautify_walk(path: str, depth: int) -> str:
            out = str()

            entries = [e for e in os.scandir(path)]
            for i, e in enumerate(entries):
                if e.is_dir():
                    print("{}├── {}".format("│   " * (depth - 1), e.name))
                    beautify_walk(e.path, depth + 1)
                else:
                    if i != len(entries) - 1:
                        print("{}├── {}".format("│   " * (depth - 1), e.name))
                    else:
                        print("{}└── {}".format("│   " * (depth - 1), e.name))

            return out

        print(self.get_name())
        beautify_walk(self.path, 1)

    def get_name(self) -> str:
        """
        Returns the name of the folder (no path)
        """
        return os.path.basename(self.path)

    def get_path(self) -> str:
        """
        Returns the path of the folder
        """
        return self.path

    def get_folder_path(self) -> str:
        """
        Returns the path of the folder containing the folder
        """
        return os.path.dirname(self.path)

    def get_modified_time(self) -> float:
        """
        Returns the time of the last modification in seconds
        """
        return os.path.getmtime(self.path)

    def get_access_time(self) -> float:
        """
        Returns the time of the last access in seconds
        """
        return os.path.getatime(self.path)

    def get_creation_time(self) -> float:
        """
        Returns the time of the creation in seconds
        """
        return os.path.getctime(self.path)

    def walk(self, topdown=True, onerror=None, followlinks=False) -> Tuple[str, List[str], List[str]]:
        """
        See os.walk
        """
        for root, dirs, files in os.walk(self.path, topdown=topdown, onerror=onerror, followlinks=followlinks):
            yield root, dirs, files

    def foreach_file(self, func: Callable[[File], Any]) -> List[Any]:
        """
        Recursively goes through all files in the folder and executes the given function for each

        :param func: The function that is called for every file
        :return: Returns a list of the return values of each function call if the value is not none
        """

        results = []
        for root, dirs, files in self.walk():
            for name in files:
                ret = func(File(root + os.sep + name))
                if ret is not None:
                    results.append(ret)

        return results

    def foreach_folder(self, func: Callable[[Folder], Any]) -> List[Any]:
        """
        Recursively goes through all folders in the folder and executes the given function for each
        :param func: The function that is called for every folder
        :return: Returns a list of the return values of each function call if the value is not none
        """

        results = []
        for root, dirs, files in self.walk():
            for name in dirs:
                ret = func(Folder(root + os.sep + name))
                if ret is not None:
                    results.append(ret)

        return results

    def get_depth(self) -> int:
        """
        Returns the depth (layers of folders) of the folder
        """
        return len(PathHelper.split_path(self.path))

    def exists(self) -> bool:
        """
        Returns True if the folder exists
        """
        return os.path.isdir(self.path)

    def create(self) -> Folder:
        """
        Creates the given folder structure
        """
        os.makedirs(self.path, exist_ok=True)
        return self

    def delete(self) -> None:
        """
        Recursively deletes the folder and its content
        """
        if self.get_depth() <= SafeGuard.get_protect_depth():
            SafeGuard.warn(self.path, "delete")
        shutil.rmtree(self.path)

    def rename_files(self,
                     rename_func: Union[Callable[[File], str], str] = None,
                     start_depth: int = 0) -> None:
        """
        Renames all files in the folder (recursively) with the rename func

        :param rename_func: Function to rename each file
        :param start_depth: Only files of that depth or further get renamed (0 = rename all files)
        """

        if self.get_depth() <= SafeGuard.get_protect_depth():
            SafeGuard.warn(self.path, "rename files in")

        real_start_depth = self.get_depth()
        sg_enabled = SafeGuard.is_enabled()
        SafeGuard.disable()

        for root, dirs, files in self.walk():
            for name in files:
                file = File(root + os.sep + name)
                delta_depth = file.get_depth() - real_start_depth

                if delta_depth >= start_depth:
                    if isinstance(rename_func, str):
                        file.rename(RegexHelper.parse(rename_func, file))
                    else:
                        file.rename(rename_func(file))

        if sg_enabled:
            SafeGuard.enable()

    def rename_folders(self,
                       rename_func: Union[Callable[[File], str], str] = None,
                       start_depth: int = 0) -> None:
        """
        Renames all folders in the folder (recursively) with the rename func

        :param rename_func: Function to rename each folder
        :param start_depth: Only folders of that depth or further are renamed (0 = rename all folders)
        """

        if self.get_depth() <= SafeGuard.get_protect_depth():
            SafeGuard.warn(self.path, "rename folders in")

        real_start_depth = self.get_depth()
        sg_enabled = SafeGuard.is_enabled()
        SafeGuard.disable()

        for root, dirs, files in self.walk(topdown=False):
            for name in dirs:
                folder = Folder(root + os.sep + name)
                delta_depth = folder.get_depth() - real_start_depth

                if delta_depth >= start_depth:
                    if isinstance(rename_func, str):
                        folder.rename(RegexHelper.parse(rename_func, folder))
                    else:
                        folder.rename(rename_func(folder))

        if sg_enabled:
            SafeGuard.enable()

    def collapse(self,
                 start_depth: int = 0,
                 rename_func: Union[Callable[[File, List[str]], str], str] = None) -> None:
        """
        Flattens a folder Structure

        :param start_depth: Only folders of that depth or further get flattened (0 = flatten all folders within)
        :param rename_func: Function to rename each collapsed file to avoid duplicate names. Takes the file and the list of folders that were collapsed and returns the new file name (no path)
        """

        if self.get_depth() <= SafeGuard.get_protect_depth():
            SafeGuard.warn(self.path, "collapse")

        real_start_depth = self.get_depth()
        sg_enabled = SafeGuard.is_enabled()
        SafeGuard.disable()

        for root, dirs, files in self.walk(topdown=False):
            for name in files:
                file = File(root + os.sep + name)
                delta_depth = file.get_depth() - real_start_depth

                if delta_depth > start_depth:
                    target_folder = os.sep.join(
                        PathHelper.split_path(file.get_folder_path())
                        [:real_start_depth + start_depth]
                    )

                    if rename_func is None:
                        file.move(target_folder)

                    else:
                        if isinstance(rename_func, str):
                            file.move(
                                target_folder
                                + os.sep
                                + RegexHelper.parse(rename_func, file, PathHelper.split_path(file.get_folder_path())
                                [real_start_depth + start_depth:])
                            )
                        else:
                            file.move(
                                target_folder
                                + os.sep
                                + rename_func(file, PathHelper.split_path(file.get_folder_path())
                                [real_start_depth + start_depth:])
                            )

            for name in dirs:
                folder = Folder(root + os.sep + name)
                delta_depth = folder.get_depth() - real_start_depth

                if delta_depth > start_depth:
                    folder.delete()

        if sg_enabled:
            SafeGuard.enable()

    def delete_files(self, start_depth: int = 0) -> None:
        """
        Deletes all files in the folder

        :param start_depth: Only files of that depth or further get removed (0 = remove all files)
        """

        if self.get_depth() <= SafeGuard.get_protect_depth():
            SafeGuard.warn(self.path, "remove files in")

        real_start_depth = self.get_depth()
        sg_enabled = SafeGuard.is_enabled()
        SafeGuard.disable()

        for root, dirs, files in self.walk():
            for name in files:
                file = File(root + os.sep + name)
                delta_depth = file.get_depth() - real_start_depth
                if delta_depth >= start_depth:
                    file.delete()

        if sg_enabled:
            SafeGuard.enable()

    def deleteif_files(self, condition: Callable[[File], bool], start_depth: int = 0) -> None:
        """
        Recursively goes through all files and removes each if the return of the condition function is true

        :param condition: When the function returns true, the file is removed
        :param start_depth: Only files of that depth or further get checked with the condition function (0 = check all)
        """

        if self.get_depth() <= SafeGuard.get_protect_depth():
            SafeGuard.warn(self.path, "remove files in")

        real_start_depth = self.get_depth()
        sg_enabled = SafeGuard.is_enabled()
        SafeGuard.disable()

        for root, dirs, files in self.walk():
            for name in files:
                file = File(root + os.sep + name)
                delta_depth = file.get_depth() - real_start_depth

                if delta_depth >= start_depth:
                    if condition(file):
                        file.delete()

        if sg_enabled:
            SafeGuard.enable()

    def find_folders(self, query: str) -> List[Folder]:
        """
        Recursively goes through all folders in the folder and checks if the query is in the folder name
        :param query: Only folder names containing the query are returned
        :return: List of found Folder objects
        """

        results = []
        self.foreach_folder(lambda folder: results.append(folder) if query in folder.get_name() else None)
        return results

    def find_files(self, query: str) -> List[File]:
        """
        Recursively goes through all files in the folder and checks if the query is in the file name
        :param query: Only file names containing the query are returned
        :return: List of found File objects
        """

        results = []
        self.foreach_file(lambda file: results.append(file) if query in file.get_name() else None)
        return results

    def copy(self, dst: str) -> None:
        """
        Recursively copies the folder to the given destination

        :param dst: The destination path
        """
        dst = os.path.abspath(dst)
        shutil.copytree(self.path, dst)

    def rename(self, new: str) -> None:
        """
        Renames the folder to the given new name

        :param new: new name of the folder without the path
        """
        if self.get_depth() <= SafeGuard.get_protect_depth():
            SafeGuard.warn(self.path, "rename")

        new_path = self.get_folder_path() + os.sep + new
        os.rename(self.path, new_path)

    def move(self, dst: str) -> None:
        """
        Moves the folder and its content to the given location

        :param dst: The destination path
        """

        if self.get_depth() <= SafeGuard.get_protect_depth():
            SafeGuard.warn(self.path, "move")

        dst = os.path.abspath(dst)
        shutil.move(self.path, dst)

    def show_in_explorer(self) -> None:
        """
        Opens the parent folder and highlights the folder in the file explorer
        """
        subprocess.Popen(f'explorer /select,"{self.path}"')

    def open_in_explorer(self) -> None:
        """
        Opens the folder itself in the file explorer
        """
        subprocess.Popen(f'explorer "{self.path}"')


class File:
    """
        FileLibrary File type to allow high level operations on files
    """

    def __init__(self, path=None):
        self.path: str = os.path.abspath(path)

    def get_depth(self) -> int:
        """
        Returns the depth (layers of folders) of the file
        """
        return len(PathHelper.split_path(self.get_folder_path()))

    def get_modified_time(self) -> float:
        """
        Returns the time of the last modification in seconds
        """
        return os.path.getmtime(self.path)

    def get_access_time(self) -> float:
        """
        Returns the time of the last access in seconds
        """
        return os.path.getatime(self.path)

    def get_creation_time(self) -> float:
        """
        Returns the time of the creation in seconds
        """
        return os.path.getctime(self.path)

    def get_name(self) -> str:
        """
        Returns the name of the file (no path)
        """
        return os.path.basename(self.path)

    def get_basename(self) -> str:
        """
        Returns the name of the file without the extension (no path)
        """
        return os.path.splitext(self.get_name())[0]

    def get_extension(self) -> str:
        """
        Returns the extension type of the file (with .)
        """
        return os.path.splitext(self.get_name())[1]

    def get_path(self) -> str:
        """
        Returns the path of the file
        """
        return self.path

    def get_folder_path(self) -> str:
        """
        Returns the path of the folder containing the file
        """
        return os.path.dirname(self.path)

    def get_folder(self) -> Folder:
        """
        Returns the folder object of the folder containing the file
        """
        return Folder(self.get_folder_path())

    def get_size(self) -> int:
        """
        Returns the size of the file in bytes
        """
        return os.path.getsize(self.path)

    def move(self, dst: str) -> None:
        """
        Moves the file to the given destination

        :param dst: The destination path
        """

        if self.get_depth() <= SafeGuard.get_protect_depth():
            SafeGuard.warn(self.path, "move")

        dst = os.path.abspath(dst)
        shutil.move(self.path, os.path.abspath(dst))

    def copy(self, dst: str) -> None:
        """
        Copies the file to the given destination

        :param dst: The destination path
        """
        dst = os.path.abspath(dst)
        shutil.copy2(self.path, dst)

    def rename(self, new: str, rename_func: bool = True) -> None:
        """
        Renames the file to the given new name

        :param new: New name of the file without the path
        :param rename_func: If true, special % commands will be run on the new name
        """

        if self.get_depth() <= SafeGuard.get_protect_depth():
            SafeGuard.warn(self.path, "rename")

        new_path = self.get_folder_path() + os.sep + RegexHelper.parse(new, self) if rename_func else new
        os.rename(self.path, new_path)

    def create(self, create_folder: bool = True) -> File:
        """
        Creates the file without data

        :param create_folder: non existing folders in path should be created
        """
        if create_folder:
            Folder(os.path.dirname(self.path)).create()
        with open(self.path, "w"): pass
        return self

    def delete(self) -> None:
        """
        Removes the file
        """

        if self.get_depth() <= SafeGuard.get_protect_depth():
            SafeGuard.warn(self.path, "delete")

        os.remove(self.path)

    def exists(self) -> bool:
        """
        Returns True if the file exists
        """

        return not os.path.isdir(self.path) and os.path.exists(self.path)

    def show_in_explorer(self) -> None:
        """
        Opens the folder containing the file and highlights it in the file explorer
        """
        subprocess.Popen(f'explorer /select,"{self.path}"')

    def __repr__(self):
        return f"File({self.path})"

    def __str__(self):
        return self.path


class PathHelper:
    @staticmethod
    def split_path(path: str) -> List[str]:
        return path.split(os.sep)


class RegexHelper:
    """
    Helper class to allow special rename functions

    Commands:
    %B - Basename
    %E - Extension name with .
    %C[...] - Collapsed folders joined with sequence between [ and ]

    %T - Time
       %TA... - Last access time
       %TM... - Last modification time
       %TC... - Creation time
       %TL... - The minimum time of %TA, %TM, %TC in case the file times are corrupt (TL -> Time least)
    """

    _BASENAME_PATTERN = re.compile(r"%B")
    _EXTENSION_PATTERN = re.compile(r"%E")
    _COLLAPSED_JOIN_PATTERN = re.compile(r"(?<=%C\[).*?(?=\])")
    _COLLAPSED_SUB_PATTERN = re.compile(r"%C\[(.*?)\]")

    _ACCESS_TIME_PATTERN = re.compile(r"(?<=%TA)-?.")
    _ACCESS_TIME_SUB_PATTERN = re.compile(r"%TA-?.")

    _MODIFIED_TIME_PATTERN = re.compile(r"(?<=%TM)-?.")
    _MODIFIED_TIME_SUB_PATTERN = re.compile(r"%TM-?.")

    _CREATION_TIME_PATTERN = re.compile(r"(?<=%TC)-?.")
    _CREATION_TIME_SUB_PATTERN = re.compile(r"%TC-?.")

    _LEAST_TIME_PATTERN = re.compile(r"(?<=%TL)-?.")
    _LEAST_TIME_SUB_PATTERN = re.compile(r"%TL-?.")

    @staticmethod
    def parse(name: str, t: Union[File, Folder], collapsed: List[str] = None) -> str:
        """
        Returns the new name of a folder / file after processing special commands such as %B
        :param name: The new name of the folder / file with the commands
        :param t: The file / folder object
        :param collapsed: The folders collapsed
        """

        if isinstance(t, File):
            name = RegexHelper.add_extension(name, t)
            name = RegexHelper.add_collapsed(name, collapsed)

        name = RegexHelper.add_basename(name, t)
        name = RegexHelper.add_access_time(name, t)
        name = RegexHelper.add_modified_time(name, t)
        name = RegexHelper.add_creation_time(name, t)
        name = RegexHelper.add_least_time(name, t)
        return name

    @staticmethod
    def add_basename(name: str, t: Union[File, Folder]) -> str:
        """
        Executes the basename command "%B"
        by adding the basename of the folder or file to the new name
        """
        basename = t.get_basename() if isinstance(t, File) else t.get_name()
        return RegexHelper._BASENAME_PATTERN.sub(basename, name)

    @staticmethod
    def add_extension(name: str, t: File) -> str:
        """
        Executes the extension command "%E"
        by adding the extension type of file to the new name (with .)
        """
        extension = t.get_extension()
        return RegexHelper._EXTENSION_PATTERN.sub(extension, name)

    @staticmethod
    def add_collapsed(name: str, collapsed: List[str]):
        """
        Executes the collapsed command "C%[...]"
        by adding the collapsed folder names joined by the given sequence to the new name
        """
        for match in RegexHelper._COLLAPSED_JOIN_PATTERN.finditer(name):
            join_seq = match.group()
            name = RegexHelper._COLLAPSED_SUB_PATTERN.sub(join_seq.join(collapsed), name, count=1)
        return name

    @staticmethod
    def add_access_time(name: str, t: Union[File, Folder]) -> str:
        """
        Executes the access time command "%TA"
        by adding the last access time with the given datetime strftime code to the name
        """
        for match in RegexHelper._ACCESS_TIME_PATTERN.finditer(name):
            dt_code = match.group()
            time = datetime.fromtimestamp(t.get_access_time()).strftime("%" + dt_code)
            name = RegexHelper._ACCESS_TIME_SUB_PATTERN.sub(time, name, count=1)

        return name

    @staticmethod
    def add_modified_time(name: str, t: Union[File, Folder]) -> str:
        """
        Executes the modified time command "%TM"
        by adding the last modified time with the given datetime strftime code to the name
        """
        for match in RegexHelper._MODIFIED_TIME_PATTERN.finditer(name):
            dt_code = match.group()
            time = datetime.fromtimestamp(t.get_modified_time()).strftime("%" + dt_code)
            name = RegexHelper._MODIFIED_TIME_SUB_PATTERN.sub(time, name, count=1)

        return name

    @staticmethod
    def add_creation_time(name: str, t: Union[File, Folder]) -> str:
        """
        Executes the creation time command "%TC"
        by adding the creation time with the given datetime strftime code to the name
        """
        for match in RegexHelper._CREATION_TIME_PATTERN.finditer(name):
            dt_code = match.group()
            time = datetime.fromtimestamp(t.get_creation_time()).strftime("%" + dt_code)
            name = RegexHelper._CREATION_TIME_SUB_PATTERN.sub(time, name, count=1)

        return name

    @staticmethod
    def add_least_time(name: str, t: Union[File, Folder]) -> str:
        """
        Executes the minimum time command "%TL"
        by adding the minimum time with the given datetime strftime code to the name
        """
        for match in RegexHelper._LEAST_TIME_PATTERN.finditer(name):
            dt_code = match.group()
            time = datetime.fromtimestamp(min(
                t.get_creation_time(),
                t.get_modified_time(),
                t.get_access_time())).strftime("%" + dt_code)
            name = RegexHelper._LEAST_TIME_SUB_PATTERN.sub(time, name, count=1)

        return name


class Example:
    @staticmethod
    def create_simple():
        """
        Creates the following folder structure in the working directory:

        example
        ├── a.txt
        ├── b.txt
        └── c.txt
        """

        File("./example/a.txt").create()
        File("./example/b.txt").create()
        File("./example/c.txt").create()

    @staticmethod
    def create_simple_nested():
        """
        Creates the following folder structure in the working directory:

        example
        ├── a.txt
        ├── test
        │   ├── b.txt
        │   ├── temp
        │   │   └── c.txt
        """

        File("./example/a.txt").create()
        File("./example/test/b.txt").create()
        File("./example/test/temp/c.txt").create()

    @staticmethod
    def create_nested_with_duplicates():
        """
        Creates the following folder structure in the working directory:

        example
        ├── a.txt
        ├── test
        │   ├── a.txt
        │   ├── b.txt
        │   ├── temp
        │   │   ├── a.txt
        │   │   ├── b.txt
        │   │   └── c.txt
        """

        File("./example/a.txt").create()
        File("./example/test/a.txt").create()
        File("./example/test/b.txt").create()
        File("./example/test/temp/a.txt").create()
        File("./example/test/temp/b.txt").create()
        File("./example/test/temp/c.txt").create()


"""
TODO:
[ ] - Get duplicates feature in Folder
[x] - Delete feature in File
[x] - Copy file to ... feature in File
[x] - Copy folder to ... feature in Folder
[x] - Rename folders feature in Folder
[x] - Deleteif feature in Folder
"""
