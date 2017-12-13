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
        if not lazy:
            self.load()

    def load(self):
        # download and parse repomd.xml
        with urlopen(f'{self.baseurl}/repodata/repomd.xml') as response:
            index = etree.fromstring(response.read())

        # determine the location of *primary.xml.gz
        data = index.find('./repo:data[@type="primary"]', namespaces=_ns)
        location = data.find('repo:location', namespaces=_ns).get('href')

        # download and parse *-primary.xml
        with urlopen(f'{self.baseurl}/{location}') as response:
            with BytesIO(response.read()) as compressed:
                with GzipFile(fileobj=compressed) as uncompressed:
                    self._metadata = etree.fromstring(uncompressed.read())
