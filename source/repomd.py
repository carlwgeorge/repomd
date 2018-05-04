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


class Repo:
    """A dnf/yum repository."""

    __slots__ = ['baseurl', '_metadata']

    def __init__(self, baseurl, lazy=False):
        self.baseurl = baseurl
        self._metadata = None
        if not lazy:
            self.load()

    def load(self):
        # download and parse repomd.xml
        with urlopen(f'{self.baseurl}/repodata/repomd.xml') as response:
            repomd_xml = etree.fromstring(response.read())

        # determine the location of *primary.xml.gz
        location = repomd_xml.find('repo:data[@type="primary"]/repo:location', namespaces=_ns).get('href')

        # download and parse *-primary.xml
        with urlopen(f'{self.baseurl}/{location}') as response:
            with BytesIO(response.read()) as compressed:
                with GzipFile(fileobj=compressed) as uncompressed:
                    self._metadata = etree.fromstring(uncompressed.read())

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
    def epoch(self):
        return self._element.find('common:version', namespaces=_ns).get('epoch')

    @property
    def version(self):
        return self._element.find('common:version', namespaces=_ns).get('ver')

    @property
    def release(self):
        return self._element.find('common:version', namespaces=_ns).get('rel')

    @property
    def build_time(self):
        build_time = self._element.find('common:time', namespaces=_ns).get('build')
        return datetime.fromtimestamp(int(build_time))

    @property
    def location(self):
        return self._element.find('common:location', namespaces=_ns).get('href')

    @property
    def nevra(self):
        return f'{self.nevr}.{self.arch}'

    @property
    def nevra_tuple(self):
        return self.name, self.epoch, self.version, self.release, self.arch

    @property
    def nevr(self):
        if int(self.epoch):
            return f'{self.name}-{self.epoch}:{self.version}-{self.release}'
        else:
            return f'{self.name}-{self.version}-{self.release}'

    @property
    def nvr(self):
        return f'{self.name}-{self.version}-{self.release}'

    @property
    def vr(self):
        return f'{self.version}-{self.release}'

    def __repr__(self):
        return f'<{self.__class__.__name__}: "{self.nevra}">'

    def __eq__(self, other):
        return self.nevra_tuple == other.nevra_tuple

    def __hash__(self):
        return hash(self.nevra_tuple)
