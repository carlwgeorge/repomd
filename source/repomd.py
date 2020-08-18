import collections
import datetime
import gzip
import io
import defusedxml.lxml
import pathlib
import urllib.request
import urllib.parse


_ns = {
    'common': 'http://linux.duke.edu/metadata/common',
    'repo':   'http://linux.duke.edu/metadata/repo',
    'rpm':    'http://linux.duke.edu/metadata/rpm'
}

_fsns = {
    'common': 'http://linux.duke.edu/metadata/filelists'
}

_cond_map = {
    "EQ": "=",
    "NE": "!=",
    "GT": ">",
    "LT": "<",
    "GE": ">=",
    "LE": "<="
}

Entry = collections.namedtuple('Entry', ['name', 'condition'])


def load(baseurl):
    # parse baseurl to allow manipulating the path
    base = urllib.parse.urlparse(baseurl)
    path = pathlib.PurePosixPath(base.path)

    # first we must get the repomd.xml file
    repomd_path = path / 'repodata' / 'repomd.xml'
    repomd_url = base._replace(path=str(repomd_path)).geturl()

    # download and parse repomd.xml
    with urllib.request.urlopen(repomd_url) as response:
        repomd_xml = defusedxml.lxml.fromstring(response.read())

    # determine the location of *primary.xml.gz
    primary_element = repomd_xml.find('repo:data[@type="primary"]/repo:location', namespaces=_ns)
    primary_path = path / primary_element.get('href')
    primary_url = base._replace(path=str(primary_path)).geturl()

    # determine the location of *filelists.xml.gz
    filelists_element = repomd_xml.find('repo:data[@type="filelists"]/repo:location', namespaces=_ns)
    filelists_path = path / filelists_element.get('href')
    filelists_url = base._replace(path=str(filelists_path)).geturl()

    # download and parse *-primary.xml
    with urllib.request.urlopen(primary_url) as response:
        with io.BytesIO(response.read()) as compressed:
            with gzip.GzipFile(fileobj=compressed) as uncompressed:
                metadata = defusedxml.lxml.fromstring(uncompressed.read())

    # download and parse *-filelists.xml
    with urllib.request.urlopen(filelists_url) as response:
        with io.BytesIO(response.read()) as compressed:
            with gzip.GzipFile(fileobj=compressed) as uncompressed:
                filelists = defusedxml.lxml.fromstring(uncompressed.read())

    return Repo(baseurl, metadata, filelists)


class Filelists:

    def __init__(self, metadata):
        self._metadata = metadata

    def get_files(self, pkgid):
        results = self._metadata.findall(
            f'common:package[@pkgid="{pkgid}"]/common:file', namespaces=_fsns)

        return [r.text for r in results]


class Repo:
    """A dnf/yum repository."""

    __slots__ = ['baseurl', '_metadata', '_filelists']

    def __init__(self, baseurl, metadata, filelists):
        self.baseurl = baseurl
        self._metadata = metadata
        self._filelists = Filelists(filelists)

    def __repr__(self):
        return f'<{self.__class__.__name__}: "{self.baseurl}">'

    def __str__(self):
        return self.baseurl

    def __len__(self):
        return int(self._metadata.get('packages'))

    def __iter__(self):
        for element in self._metadata:
            yield Package(element)

    def find(self, name):
        results = self._metadata.findall(f'common:package[common:name="{name}"]', namespaces=_ns)
        if results:
            result = results[-1]
            pkgid = result.findtext('common:checksum', namespaces=_ns)
            filelist = self._filelists.get_files(pkgid)
            return Package(results[-1], filelist)
        else:
            return None

    def findall(self, name):
        return [
            Package(element)
            for element in self._metadata.findall(f'common:package[common:name="{name}"]', namespaces=_ns)
        ]


class Package:
    """An RPM package from a repository."""

    __slots__ = ['_element', '_filelist']

    def __init__(self, element, filelist):
        self._element = element
        self._filelist = filelist

    @property
    def filelist(self):
        return self._filelist

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
    def buildhost(self):
        return self._element.findtext(
            'common:format/rpm:buildhost', namespaces=_ns)

    @property
    def group(self):
        return self._element.findtext(
            'common:format/rpm:group', namespaces=_ns)

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
    def epoch(self):
        return self._version_info.get('epoch')

    @property
    def version(self):
        return self._version_info.get('ver')

    @property
    def release(self):
        return self._version_info.get('rel')

    @property
    def provides(self):
        provides = self._element.findall(
            'common:format/rpm:provides/rpm:entry', namespaces=_ns)
        return self._entries(provides)

    @property
    def requires(self):
        requires = self._element.findall(
            'common:format/rpm:requires/rpm:entry', namespaces=_ns)
        return self._entries(requires)

    @property
    def conflicts(self):
        conflicts = self._element.findall(
            'common:format/rpm:conflicts/rpm:entry', namespaces=_ns)
        return self._entries(conflicts)

    @property
    def obsoletes(self):
        obsoletes = self._element.findall(
            'common:format/rpm:obsoletes/rpm:entry', namespaces=_ns)
        return self._entries(obsoletes)

    def _entries(self, entries):
        def condition(one):
            epoch = one.get('epoch')
            ver = one.get('ver')
            rel = one.get('rel')
            flags = one.get('flags')
            if one.get('ver'):
                epoch = f"{epoch}:" if int(epoch) else ""
                rel = f"-{rel}" if rel else ""

                return "{cond} {evr}".format(
                    evr=f"{epoch}{ver}{rel}",
                    cond=_cond_map[flags])

            return "-"

        return [Entry(one.get("name"), condition(one)) for one in entries]

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
