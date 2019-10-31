import datetime
import bz2
import gzip
import io
import defusedxml.lxml
import pathlib
import urllib.request
import urllib.parse
import sqlite3
import tempfile


import pprint

_ns = {
    'common': 'http://linux.duke.edu/metadata/common',
    'repo':   'http://linux.duke.edu/metadata/repo',
    'rpm':    'http://linux.duke.edu/metadata/rpm'
}


def get_primary_contents(base, path, repomd_xml, data_type):
    """Get the repometadata for the type in question.

    Parameters:
        base - output of urllib.parse.urlparse on a repomd.xml file
        repomd_xml - defusedxml.lxml.fromstring output of the repomd.xml path
        data_type - The XML Node to look for, usually 'primary' or 'primary_db'

    Returns:
        (bytes) - An uncompressed bytes object from the URL referenced 
                  in the found xml node.

    Common Exceptions:
        Will raise AttributeError when the DataType is not found
    """
    find_query = 'repo:data[@type="{}"]/repo:location'.format(data_type)

    primary_element = repomd_xml.find(find_query, namespaces=_ns)
    primary_path = path / primary_element.get('href')
    primary_url = base._replace(path=str(primary_path)).geturl()

    with urllib.request.urlopen(primary_url) as response:
        with io.BytesIO(response.read()) as compressed:
            if primary_url.endswith('.gz'):
                with gzip.GzipFile(fileobj=compressed) as uncompressed:
                    return uncompressed.read()
            if primary_url.endswith('.bz2'):
                with bz2.BZ2File(compressed) as uncompressed:
                    return uncompressed.read()

def load(baseurl):
    # parse baseurl to allow manipulating the path
    base = urllib.parse.urlparse(baseurl)
    path = pathlib.PurePosixPath(base.path)

    # first we must get the repomd.xml file
    repomd_path = path / 'repodata' / 'repomd.xml'
    repomd_url = base._replace(path=str(repomd_path)).geturl()

    repo_obj = None
    # download and parse repomd.xml
    with urllib.request.urlopen(repomd_url) as response:
        repomd_xml = defusedxml.lxml.fromstring(response.read())
    try:
        primary_contents = get_primary_contents(base, path, repomd_xml, 'primary_db')
        repo_obj = SQLiteRepo(baseurl, primary_contents)
    except AttributeError as e:
        # silencing this error so that we can pass to the next exception
        pass
    if not repo_obj:
        primary_contents = get_primary_contents(base, path, repomd_xml, 'primary')
        repo_obj = XmlRepo(baseurl, primary_contents)
    return repo_obj

class BasePackage:

    @property
    def vr(self):
        version_info = self._version_info
        v = version_info.get('ver')
        r = version_info.get('rel')
        return f'{v}-{r}'

    @property
    def nvr(self):
        return f'{self.name}-{self.vr}'

    @property
    def evr(self):
        version_info = self._version_info
        e = version_info.get('epoch')
        v = version_info.get('ver')
        r = version_info.get('rel')
        if int(e):
            return f'{e}:{v}-{r}'
        else:
            return f'{v}-{r}'

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

class SQLitePackage(BasePackage):
    """A Class for inspecting packages in an SQLite-based repo.
    
    Most properties are generated based on primary.packages column headers and dynamically
    generated from the pkg_row constructor parameter.

    The properties that are auto generated from a CentOS 7-built primary sqlite DB are:

        pkgId TEXT
        name TEXT
        arch TEXT
        version TEXT
        epoch TEXT
        release TEXT
        summary TEXT
        description TEXT
        url TEXT
        time_file INTEGER
        time_build INTEGER
        license TEXT
        vendor TEXT
        group TEXT
        buildhost TEXT
        sourcerpm TEXT
        header_start INTEGER
        header_end INTEGER
        packager TEXT
        size_package INTEGER
        size_installed INTEGER
        size_archive INTEGER
        location_href TEXT
        location_base TEXT
        checksum_type TEXT

    These could vary between different yum repo versions but should be consistent with most major 
    red hat-derived distros in 2019.

    There are some other properties as well that are not dynamically generated.

    Properties:
        location (str) - alias to location_href
        ver (str) - alias to version
        rel (str) - alias to release
        shasum (str) - alias to pkgId
        build_time (datetime) - datetime object from the time_build column

    Parameters:
        pkg_row - an sqlite3.Row object representing the sqlite table.
    
    """
    def __init__(self, pkg_row):
        self.pkg_row = pkg_row
        # copy all of keys from the pkg_row into attributes
        # this will result in the common rpm headers having attributes available.
        # any key that starts with rpm_ in the sqlite file will have it stripped off
        for k in pkg_row.keys():
            attr_name = k
            if k.startswith('rpm_'):
                attr_name = attr_name.replace('rpm_', '')
            setattr(self, attr_name, pkg_row[k])

        self.location = self.location_href
        self.ver = self.version
        self.rel = self.release
        self.shasum = self.pkgId
        self._version_info = {
            'epoch': self.epoch,
            'ver': self.ver,
            'rel': self.rel
        }

    @property
    def build_time(self):
        return datetime.datetime.fromtimestamp(int(self.time_build))


class XmlPackage(BasePackage):
    """An RPM package from a repository."""

    __slots__ = ['_element']

    def __init__(self, element):
        self._element = element

    @property
    def name(self):
        return self._element.findtext('common:name', namespaces=_ns)

    @property
    def arch(self):
        return self._element.findtext('common:arch', namespaces=_ns)

    @property
    def summary(self):
        return self._element.findtext('common:summary', namespaces=_ns)

    @property
    def description(self):
        return self._element.findtext('common:description', namespaces=_ns)

    @property
    def packager(self):
        return self._element.findtext('common:packager', namespaces=_ns)

    @property
    def url(self):
        return self._element.findtext('common:url', namespaces=_ns)

    @property
    def license(self):
        return self._element.findtext('common:format/rpm:license', namespaces=_ns)

    @property
    def vendor(self):
        return self._element.findtext('common:format/rpm:vendor', namespaces=_ns)

    @property
    def sourcerpm(self):
        return self._element.findtext('common:format/rpm:sourcerpm', namespaces=_ns)

    @property
    def build_time(self):
        build_time = self._element.find('common:time', namespaces=_ns).get('build')
        return datetime.datetime.fromtimestamp(int(build_time))

    @property
    def location(self):
        return self._element.find('common:location', namespaces=_ns).get('href')

    @property
    def _version_info(self):
        return self._element.find('common:version', namespaces=_ns)

    @property
    def version(self):
        return self._version_info.get('ver')

    @property
    def release(self):
        return self._version_info.get('rel')

    @property
    def epoch(self):
        return self._version_info.get('epoch')


class BaseRepo():
    pass


class XmlRepo(BaseRepo):
    """A dnf/yum repository backed by XML."""

    __slots__ = ['baseurl', '_metadata']

    def __init__(self, baseurl, metadata):
        self.baseurl = baseurl
        self._metadata = defusedxml.lxml.fromstring(metadata)

    def __repr__(self):
        return f'<{self.__class__.__name__}: "{self.baseurl}">'

    def __str__(self):
        return self.baseurl

    def __len__(self):
        return int(self._metadata.get('packages'))

    def __iter__(self):
        for element in self._metadata:
            yield XmlPackage(element)

    def find(self, name):
        results = self._metadata.findall(f'common:package[common:name="{name}"]', namespaces=_ns)
        if results:
            return XmlPackage(results[-1])
        else:
            return None

    def findall(self, name):
        return [
            XmlPackage(element)
            for element in self._metadata.findall(f'common:package[common:name="{name}"]', namespaces=_ns)
        ]


class SQLiteRepo(BaseRepo):
    """A yum/dnf repoistory backed by SQLite."""

    def __init__(self, baseurl, metadata):
        self.baseurl = baseurl
        self.db_file = tempfile.NamedTemporaryFile()
        self.db_file.write(metadata) 
        self.conn = sqlite3.connect(self.db_file.name)
        self.conn.row_factory = sqlite3.Row

    def __repr__(self):
        return f'<{self.__class__.__name__}: "{self.baseurl}">'

    def __str__(self):
        return self.baseurl

    def __len__(self):
        c = self.conn.cursor()
        row = c.execute('SELECT COUNT(ALL) FROM packages')
        return row.fetchone()[0]

    def __iter__(self):
        c = self.conn.cursor()
        c.execute('SELECT * FROM packages')
        for pkgrow in c:
            yield SQLitePackage(pkgrow)

    def findall(self, pkgname):
        c = self.conn.cursor()
        c.execute("SELECT * FROM packages WHERE name = ?", [pkgname])
        return [SQLitePackage(p) for p in c.fetchall()]

    def find(self, pkgname):
        c = self.conn.cursor()
        c.execute("SELECT * FROM packages WHERE name = ? ORDER BY time_build LIMIT 1", [pkgname])
        res = c.fetchone()
        if res:
            return SQLitePackage(res)
        return None

