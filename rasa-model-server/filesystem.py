from datetime import datetime
from os import scandir, listdir
from os.path import isfile, isdir, relpath, join, getsize

from config import models_dir


class Scaner:
    def __init__(self, path):
        self.entries = [Entry(entry) for entry in scandir(path.encode())]
        self.latest_entry = next(iter(sorted(self.entries, key=lambda e: e.modified_time, reverse=True)), None)


class Entry:
    def __init__(self, entry):
        self.name = entry.name.decode()
        self.path = entry.path.decode()
        self.rel_path = relpath(self.path, models_dir)
        self.is_dir = entry.is_dir()
        self.created_time = datetime.fromtimestamp(entry.stat().st_ctime)
        self.modified_time = datetime.fromtimestamp(entry.stat().st_mtime)
        self.size = self._human_readable_size(self._get_size(entry.path))

    def _get_size(self, path):
        total_size = getsize(path)
        if isdir(path):
            for item in listdir(path):
                item_path = join(path, item)
                if isfile(item_path):
                    total_size += getsize(item_path)
                elif isdir(item_path):
                    total_size += self._get_size(item_path)
        return total_size

    def _human_readable_size(self, size):
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        human_fmt = '{0:.2f} {1}'
        human_radix = 1024.

        for unit in units[:-1]:
            if size < human_radix: 
                return human_fmt.format(size, unit)
            size /= human_radix

        return human_fmt.format(size, units[-1])

# flake8: noqa: E501
