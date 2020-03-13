import copy
import datetime
import pathlib
import unittest.mock
import urllib
import xml.etree.ElementTree as ET

import pytest

import repomd


def load_test_repodata(base):
    base = pathlib.Path(base)
    with (base / 'repodata' / 'repomd.xml').open(mode='rb') as f:
        repomd_xml = f.read()
    with (base / 'repodata' / 'primary.xml.gz').open(mode='rb') as f:
        primary_xml = f.read()
    return (repomd_xml, primary_xml)


@pytest.fixture
@unittest.mock.patch('repomd.urllib.request.urlopen')
def repo(mock_urlopen):
    mock_urlopen.return_value.__enter__.return_value.read.side_effect = load_test_repodata('tests/data/repo')
    return repomd.load('https://example.com')


@pytest.fixture
@unittest.mock.patch('repomd.urllib.request.urlopen')
def empty_repo(mock_urlopen):
    mock_urlopen.return_value.__enter__.return_value.read.side_effect = load_test_repodata('tests/data/empty_repo')
    return repomd.load('https://example.com')


@pytest.fixture
def chicken(repo):
    return repo.find('chicken')


@pytest.fixture
def brisket(repo):
    return repo.find('brisket')


@pytest.fixture
def pork_ribs(repo):
    return repo.find('pork-ribs')


@unittest.mock.patch('repomd.urllib.request.urlopen')
def test_valid_load_mirrorlist(mock_urlopen):
    data = b'http://test1.mirror.com/CentOS/7\nhttp://test2.mirror.com/CentOS'  # noqa

    expected = [
        'http://test1.mirror.com/CentOS/7',
        'http://test2.mirror.com/CentOS'
    ]

    m = unittest.mock.MagicMock()
    m.read.return_value = data
    mock_urlopen.return_value.__enter__.return_value = m

    assert repomd._load_mirrorlist('http://mirrorlist.mirror.com') == expected


@unittest.mock.patch('repomd.urllib.request.urlopen')
def test_no_data_load_mirrorlist(mock_urlopen):
    m = unittest.mock.MagicMock()
    m.read.return_value = b''
    mock_urlopen.return_value.__enter__.return_value = m

    assert repomd._load_mirrorlist('http://mirrorlist.mirror.com') == []


@unittest.mock.patch('repomd.urllib.request.urlopen')
def test_invalid_url_load_mirrorlist(mock_urlopen):
    data = b'http://test1.mirror.com/CentOS\nsomestring\nhttp://\n://test\nhttp://test2.mirror.com/CentOS/7'  # noqa

    expected = [
        'http://test1.mirror.com/CentOS',
        'http://test2.mirror.com/CentOS/7'
    ]

    m = unittest.mock.MagicMock()
    m.read.return_value = data
    mock_urlopen.return_value.__enter__.return_value = m

    assert repomd._load_mirrorlist('http://mirrorlist.mirror.com') == expected


@unittest.mock.patch('repomd.urllib.request.urlopen')
def test_exception_load_mirrorlist(mock_urlopen):
    mock_urlopen.return_value.__enter__.side_effect = Exception
    assert repomd._load_mirrorlist('http://mirrorlist.mirror.com') == []


def test_parse_baseurl():
    base, path = repomd._parse_baseurl('http://test.url.com/some/path')

    assert base.geturl() == 'http://test.url.com/some/path'
    assert path == pathlib.PurePosixPath('/some/path')


@unittest.mock.patch('repomd.urllib.request.urlopen')
def test_load_repomd_not_found(mock_urlopen):
    mock_urlopen.return_value.__enter__.side_effect = urllib.error.HTTPError(
        url='', code=404, msg='', hdrs=None, fp=None)

    with pytest.raises(repomd.NotRepoException):
        base, path = repomd._parse_baseurl('http://example.com')
        repomd._load_repomd(base, path)


@unittest.mock.patch('repomd.urllib.request.urlopen')
def test_load_repomd_urllib_reraise_exception(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url='', code=500, msg='', hdrs=None, fp=None)

    with pytest.raises(urllib.error.HTTPError):
        base, path = repomd._parse_baseurl('http://example.com')
        repomd._load_repomd(base, path)


@unittest.mock.patch('repomd.urllib.request.urlopen')
def test_load_repomd_other_exception(mock_urlopen):
    mock_urlopen.side_effect = Exception
    with pytest.raises(Exception):
        base, path = repomd._parse_baseurl('http://example.com')
        repomd._load_repomd(base, path)


@unittest.mock.patch('repomd._load_mirrorlist')
@unittest.mock.patch('repomd._load_repomd')
def test_load_fail_mirrorlist(mock_one, mock_two):
    mock_one.side_effect = repomd.NotRepoException
    mock_two.return_value = []

    with pytest.raises((repomd.NotRepoException,
                        repomd.NotRepoException)):
        repomd.load('https://example.com')


@unittest.mock.patch('repomd.urllib.request.urlopen')
@unittest.mock.patch('repomd._load_mirrorlist')
@unittest.mock.patch('repomd._load_repomd')
def test_load_fallback_mirrorlist(mock_one, mock_two, mock_three):
    repo, primary = load_test_repodata('tests/data/repo')
    f1 = Exception
    f2 = ET.fromstring(repo)

    mock_one.side_effect = (repomd.NotRepoException, f1, f2)

    mock_two.return_value = [
        'http://test1.mirror.com/CentOS/7',
        'http://test2.mirror.com/CentOS',
    ]

    mock_three.return_value.__enter__.return_value.read.return_value = primary
    repomd.load('https://example.com')


def test_repo(repo):
    assert repo.baseurl == 'https://example.com'
    assert isinstance(repo._metadata, ET.Element)


def test_repo_repr(repo):
    assert repr(repo) == '<Repo: "https://example.com">'


def test_repo_str(repo):
    assert str(repo) == 'https://example.com'


def test_repo_len(repo, empty_repo):
    assert len(repo) == 5
    assert len(empty_repo) == 0


def test_find(repo):
    package = repo.find('non-existent')
    assert package is None
    package = repo.find('chicken')
    assert isinstance(package, repomd.Package)


def test_findall(repo):
    packages = repo.findall('non-existent')
    assert packages == []
    packages = repo.findall('chicken')
    assert any(packages)
    for package in packages:
        assert isinstance(package, repomd.Package)


def test_iter(repo):
    for package in repo:
        assert isinstance(package, repomd.Package)


def test_package(chicken):
    assert repr(chicken) == '<Package: "chicken-2.2.10-1.fc27.noarch">'
    assert chicken.name == 'chicken'
    assert chicken.arch == 'noarch'
    assert chicken.summary == 'Chicken'
    assert chicken.description == 'Chicken.'
    assert chicken.packager == 'Carl'
    assert chicken.url == 'https://example.com/chicken'
    assert chicken.license == 'BBQ'
    assert chicken.vendor == "Carl's BBQ"
    assert chicken.sourcerpm == 'chicken-2.2.10-1.fc27.src.rpm'
    assert chicken.build_time == datetime.datetime.fromtimestamp(1525208602)
    assert chicken.location == 'chicken-2.2.10-1.fc27.noarch.rpm'
    assert chicken.epoch == '0'
    assert chicken.version == '2.2.10'
    assert chicken.release == '1.fc27'
    assert chicken.vr == '2.2.10-1.fc27'
    assert chicken.nvr == 'chicken-2.2.10-1.fc27'
    assert chicken.evr == '2.2.10-1.fc27'
    assert chicken.nevr == 'chicken-2.2.10-1.fc27'
    assert chicken.nevra == 'chicken-2.2.10-1.fc27.noarch'


def test_package_with_epoch(brisket):
    assert repr(brisket) == '<Package: "brisket-1:5.1.1-1.fc27.noarch">'
    assert brisket.name == 'brisket'
    assert brisket.arch == 'noarch'
    assert brisket.summary == 'Brisket'
    assert brisket.description == 'Brisket.'
    assert brisket.packager == 'Carl'
    assert brisket.url == 'https://example.com/brisket'
    assert brisket.license == 'BBQ'
    assert brisket.vendor == "Carl's BBQ"
    assert brisket.sourcerpm == 'brisket-5.1.1-1.fc27.src.rpm'
    assert brisket.build_time == datetime.datetime.fromtimestamp(1525208602)
    assert brisket.location == 'brisket-5.1.1-1.fc27.noarch.rpm'
    assert brisket.epoch == '1'
    assert brisket.version == '5.1.1'
    assert brisket.release == '1.fc27'
    assert brisket.vr == '5.1.1-1.fc27'
    assert brisket.nvr == 'brisket-5.1.1-1.fc27'
    assert brisket.evr == '1:5.1.1-1.fc27'
    assert brisket.nevr == 'brisket-1:5.1.1-1.fc27'
    assert brisket.nevra == 'brisket-1:5.1.1-1.fc27.noarch'


def test_subpackage(pork_ribs):
    assert repr(pork_ribs) == '<Package: "pork-ribs-3.2.0-1.fc27.noarch">'
    assert pork_ribs.name == 'pork-ribs'
    assert pork_ribs.arch == 'noarch'
    assert pork_ribs.summary == 'Pork ribs'
    assert pork_ribs.description == 'Pork ribs.'
    assert pork_ribs.packager == 'Carl'
    assert pork_ribs.url == 'https://example.com/ribs'
    assert pork_ribs.license == 'BBQ'
    assert pork_ribs.vendor == "Carl's BBQ"
    assert pork_ribs.sourcerpm == 'ribs-3.2.0-1.fc27.src.rpm'
    assert pork_ribs.build_time == datetime.datetime.fromtimestamp(1525208603)
    assert pork_ribs.location == 'pork-ribs-3.2.0-1.fc27.noarch.rpm'
    assert pork_ribs.epoch == '0'
    assert pork_ribs.version == '3.2.0'
    assert pork_ribs.release == '1.fc27'
    assert pork_ribs.vr == '3.2.0-1.fc27'
    assert pork_ribs.nvr == 'pork-ribs-3.2.0-1.fc27'
    assert pork_ribs.evr == '3.2.0-1.fc27'
    assert pork_ribs.nevr == 'pork-ribs-3.2.0-1.fc27'
    assert pork_ribs.nevra == 'pork-ribs-3.2.0-1.fc27.noarch'


def test_package_equals_its_copy(chicken):
    copied_chicken = copy.copy(chicken)
    assert chicken is chicken
    assert chicken == chicken
    assert chicken is not copied_chicken
    assert chicken == copied_chicken


def test_packages_can_be_used_as_dict_keys(chicken, brisket):
    d = {chicken: 'chicken', brisket: 'brisket'}
    copied_chicken = copy.copy(chicken)
    assert d[copied_chicken] == 'chicken'


def test_equal_packages_work_in_set(chicken, brisket):
    copied_chicken = copy.copy(chicken)
    copied_brisket = copy.copy(brisket)
    assert len({chicken, brisket, copied_chicken, copied_brisket}) == 2
