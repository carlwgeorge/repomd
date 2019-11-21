import datetime
import tempfile
import sqlite3
import os


class Repo:
    """A dnf/yum repository."""

    __slots__ = ['baseurl', '_metadata']

    def __init__(self, baseurl, metadata):
        self.baseurl = baseurl
        self._metadata = sqlite3.connect(':memory:')
        self._metadata.row_factory = sqlite3.Row
        with tempfile.TemporaryDirectory() as temp_dir:
            db_file = os.path.join(temp_dir, 'temp.db')
            with open(db_file, 'wb') as fp:
                fp.write(metadata)
            temp_con = sqlite3.connect(db_file)
            temp_con.backup(self._metadata)
            temp_con.close()

    def _execute(self, query):
        cur = self._metadata.cursor()
        return cur.execute(query)

    def __repr__(self):
        return f'<{self.__class__.__name__}: "{self.baseurl}">'

    def __str__(self):
        return self.baseurl

    def __len__(self):
        return self._execute('SELECT count(*) FROM packages').fetchone()[0]

    def __iter__(self):
        for row in self._execute('SELECT * FROM packages'):
            yield Package(row)

    def find(self, name):
        rows = self._execute(f'SELECT * FROM packages WHERE name = "{name}"').fetchall()
        if rows:
            return Package(rows[-1])  # Maybe this should return the latest
        else:
            return None

    def findall(self, name):
        return [
            Package(row)
            for row in self._execute(f'SELECT * FROM packages WHERE name = "{name}"').fetchall()
        ]


class Package:
    """An RPM package from a repository."""

    __slots__ = ['_row']

    def __init__(self, row):
        self._row = row

    @property
    def name(self):
        return self._row['name']

    @property
    def arch(self):
        return self._row['arch']

    @property
    def summary(self):
        return self._row['summary']

    @property
    def description(self):
        return self._row['description']

    @property
    def packager(self):
        return self._row['packager']

    @property
    def url(self):
        return self._row['arch']

    @property
    def license(self):
        return self._row['rpm_license']

    @property
    def vendor(self):
        return self._row['rpm_vendor']

    @property
    def sourcerpm(self):
        return self._row['rpm_sourcerpm']

    @property
    def build_time(self):
        build_time = self._row['time_build']
        return datetime.datetime.fromtimestamp(int(build_time))

    @property
    def location(self):
        return self._row['location_href']

    @property
    def epoch(self):
        return self._row['epoch']

    @property
    def version(self):
        return self._row['version']

    @property
    def release(self):
        return self._row['release']

    @property
    def vr(self):
        return f'{self.version}-{self.release}'

    @property
    def nvr(self):
        return f'{self.name}-{self.vr}'

    @property
    def evr(self):
        if int(self.epoch):
            return f'{self.epoch}:{self.version}-{self.release}'
        else:
            return f'{self.version}-{self.release}'

    @property
    def nevr(self):
        return f'{self.name}-{self.evr}'

    @property
    def nevra(self):
        return f'{self.nevr}.{self.arch}'

    @property
    def _nevra_tuple(self):
        return self.name, self.epoch, self.version, self.release, self.arch

    def __eq__(self, other):
        return self._nevra_tuple == other._nevra_tuple

    def __hash__(self):
        return hash(self._nevra_tuple)

    def __repr__(self):
        return f'<{self.__class__.__name__}: "{self.nevra}">'
