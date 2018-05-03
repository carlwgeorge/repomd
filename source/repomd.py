from datetime import datetime
from functools import partial
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
    __slots__ = [
        'name',
        'arch',
        'summary',
        'description',
        'packager',
        'url',
        'license',
        'vendor',
        'sourcerpm',
        'epoch',
        'version',
        'release',
        'build_time',
        'location',
    ]

    def __init__(self, element):
        find = partial(element.find, namespaces=_ns)
        findtext = partial(element.findtext, namespaces=_ns)

        self.name = findtext('common:name')
        self.arch = findtext('common:arch')
        self.summary = findtext('common:summary')
        self.description = findtext('common:description')
        self.packager = findtext('common:packager')
        self.url = findtext('common:url')
        self.license = findtext('common:format/rpm:license')
        self.vendor = findtext('common:format/rpm:vendor')
        self.sourcerpm = findtext('common:format/rpm:sourcerpm')

        self.epoch = find('common:version').get('epoch')
        self.version = find('common:version').get('ver')
        self.release = find('common:version').get('rel')

        build_time = find('common:time').get('build')
        self.build_time = datetime.fromtimestamp(int(build_time))

        self.location = find('common:location').get('href')

    @property
    def nevra(self):
        if int(self.epoch):
            return f'{self.name}-{self.epoch}:{self.version}-{self.release}.{self.arch}'
        else:
            return f'{self.name}-{self.version}-{self.release}.{self.arch}'

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
