import tarfile
import zipfile

from sio3pack.files.file import File


def is_archive(file: str|File):
    if isinstance(file, File):
        file_path = file.path
    else:
        file_path = file

    try:
        if zipfile.is_zipfile(file_path):
            return True

        if tarfile.is_tarfile(file_path):
            return True
    except:
        pass
    
    return False

def has_dir(file: str|File, dir_name: str):
    if isinstance(file, File):
        file_path = file.path
    else:
        file_path = file

    try:
        if zipfile.is_zipfile(file_path):
            archive = zipfile.ZipFile(file_path)
            return dir_name in map(lambda f: f.filename, archive.infolist())

        if tarfile.is_tarfile(file_path):
            archive = tarfile.TarFile(file_path)
            return dir_name in map(lambda f: f.name, archive.getmembers())
    except:
        pass
    
    return False
