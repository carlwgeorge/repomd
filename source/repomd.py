from copy import deepcopy
from datetime import datetime
from gzip import GzipFile
from io import BytesIO
from urllib.request import urlopen
from lxml import etree


_ns = {
    'common': 'http://linux.duke.edu/metadata/common',
    'repo':   'http://linux.duke.edu/metadata/repo',
    'rpm':    'http://linux.duke.edu/metadata/rpm'
}


def load(baseurl):
    # download and parse repomd.xml
    with urlopen(f'{baseurl}/repodata/repomd.xml') as response:
        repomd_xml = etree.fromstring(response.read())

    # determine the location of *primary.xml.gz
    location = repomd_xml.find('repo:data[@type="primary"]/repo:location', namespaces=_ns).get('href')

    # download and parse *-primary.xml
    with urlopen(f'{baseurl}/{location}') as response:
        with BytesIO(response.read()) as compressed:
            with GzipFile(fileobj=compressed) as uncompressed:
                metadata = etree.fromstring(uncompressed.read())

    return Repo(baseurl, metadata)


class Repo:
    """A dnf/yum repository."""

    __slots__ = ['baseurl', '_metadata']

    def __init__(self, baseurl, metadata):
        self.baseurl = baseurl
        self._metadata = metadata

    def __repr__(self):
        return f'<{self.__class__.__name__}: "{self.baseurl}">'

    def __str__(self):
        return f'{self.baseurl}'

    def __len__(self):
        return int(self._metadata.get('packages'))

    def __iter__(self):
        for element in self._metadata:
            yield Package(element)

    def find(self, name):
        results = self._metadata.findall(f'common:package[common:name="{name}"]', namespaces=_ns)
        if results:
            return Package(results[-1])
        else:
            return None

    def findall(self, name):
        return [
            Package(element)
            for element in self._metadata.findall(f'common:package[common:name="{name}"]', namespaces=_ns)
        ]


class Package:
    """An RPM package from a repository."""

    __slots__ = ['_element']

    def __init__(self, element):
        self._element = deepcopy(element)

    @property
    def name(self):
        return self._element.findtext(f'common:name', namespaces=_ns)

    @property
    def arch(self):
        return self._element.findtext(f'common:arch', namespaces=_ns)

    @property
    def summary(self):
        return self._element.findtext(f'common:summary', namespaces=_ns)

    @property
    def description(self):
        return self._element.findtext(f'common:description', namespaces=_ns)

    @property
    def packager(self):
        return self._element.findtext(f'common:packager', namespaces=_ns)

    @property
    def url(self):
        return self._element.findtext(f'common:url', namespaces=_ns)

    @property
    def license(self):
        return self._element.findtext(f'common:format/rpm:license', namespaces=_ns)

    @property
    def vendor(self):
        return self._element.findtext(f'common:format/rpm:vendor', namespaces=_ns)

    @property
    def sourcerpm(self):
        return self._element.findtext(f'common:format/rpm:sourcerpm', namespaces=_ns)

    @property
    def build_time(self):
        build_time = self._element.find('common:time', namespaces=_ns).get('build')
        return datetime.fromtimestamp(int(build_time))

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
