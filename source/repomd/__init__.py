import gzip
import io
import defusedxml.lxml
import pathlib
import urllib.request
import urllib.parse
from repomd import _xml, _sqlite


def load(baseurl):
    # parse baseurl to allow manipulating the path
    base = urllib.parse.urlparse(baseurl)
    path = pathlib.PurePosixPath(base.path)

    # first we must get the repomd.xml file
    repomd_path = path / 'repodata' / 'repomd.xml'
    repomd_url = base._replace(path=str(repomd_path)).geturl()

    # download and parse repomd.xml
    with urllib.request.urlopen(repomd_url) as response:
        repomd_str = response.read().decode('utf-8')
        repomd_xml = defusedxml.lxml.fromstring(repomd_str)

    # determine the location of *primary.xml.gz / *primary.sqlite.gz

    primary_element = repomd_xml.find('repo:data[@type="primary"]/repo:location', namespaces=_xml._ns)
    metadata_type = 'xml'

    if primary_element is None:
        primary_element = repomd_xml.find('repo:data[@type="primary_db"]/repo:location', namespaces=_xml._ns)
        metadata_type = 'db'

    if primary_element is None:
        raise LookupError('Missing primary and primary_db in repomd.xml')

    primary_path = path / primary_element.get('href')
    primary_url = base._replace(path=str(primary_path)).geturl()

    # download and parse *-primary.xml / primary.sqlite
    with urllib.request.urlopen(primary_url) as response:
        with io.BytesIO(response.read()) as compressed:
            with gzip.GzipFile(fileobj=compressed) as uncompressed:
                raw_metadata = uncompressed.read()

    if metadata_type == 'xml':
        return _xml.Repo(baseurl, defusedxml.lxml.fromstring(raw_metadata))
    elif metadata_type == 'db':
        return _sqlite.Repo(baseurl, raw_metadata)
