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
        primary_data = repomd_xml.find('./repo:data[@type="primary"]', namespaces=_ns)
        primary_location = primary_data.find('repo:location', namespaces=_ns).get('href')

        # download and parse *-primary.xml
        with urlopen(f'{self.baseurl}/{primary_location}') as response:
            with BytesIO(response.read()) as compressed:
                with GzipFile(fileobj=compressed) as uncompressed:
                    self._metadata = etree.fromstring(uncompressed.read())

    def __repr__(self):
        return f'<{self.__class__.__name__}: "{self.baseurl}">'

    def __str__(self):
        return f'{self.baseurl}'

    def __len__(self):
        return int(self._metadata.get('packages'))
