import copy
import datetime
import pathlib
import unittest.mock

import glob
import pytest

import repomd


def get_buildtimes(filename):
    with open('tests/data/buildtimes') as fh:
        for line in fh:
            line_filename, buildtime = line.split(' ', 2)
            if line_filename == filename:
                return int(buildtime)


def load_test_repodata(base):
    base = pathlib.Path(base)
    with (base / 'repodata' / 'repomd.xml').open(mode='rb') as f:
        repomd_xml = f.read()
    repo_glob = '{}/repodata/*-primary.sqlite.bz2'.format(base)
    primary_path = glob.glob(repo_glob)[0]
    with open(primary_path, mode='rb') as f:
        primary_sqlite = f.read()
    return (repomd_xml, primary_sqlite)


@pytest.fixture
@unittest.mock.patch('repomd.urllib.request.urlopen')
def repo(mock_urlopen):
    mock_urlopen.return_value.__enter__.return_value.read.side_effect = load_test_repodata('tests/data/sqlite_repo')
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


def test_repo(repo):
    assert repo.baseurl == 'https://example.com'


def test_repo_repr(repo):
    assert repr(repo) == '<SQLiteRepo: "https://example.com">'


def test_repo_str(repo):
    assert str(repo) == 'https://example.com'


def test_repo_len(repo):
    assert len(repo) == 5


def test_find(repo):
    package = repo.find('non-existent')
    assert package is None
    package = repo.find('chicken')
    assert isinstance(package, repomd.BasePackage)


def test_findall(repo):
    packages = repo.findall('non-existent')
    assert packages == []
    packages = repo.findall('chicken')
    assert any(packages)
    for package in packages:
        assert isinstance(package, repomd.BasePackage)


def test_iter(repo):
    for package in repo:
        assert isinstance(package, repomd.BasePackage)


def test_package(chicken):
    buildtime = get_buildtimes('chicken-2.2.10-1.fc27.noarch.rpm')
    assert repr(chicken) == '<SQLitePackage: "chicken-2.2.10-1.fc27.noarch">'
    assert chicken.name == 'chicken'
    assert chicken.arch == 'noarch'
    assert chicken.summary == 'Chicken'
    assert chicken.description == 'Chicken.'
    assert chicken.packager == 'Carl'
    assert chicken.url == 'https://example.com/chicken'
    assert chicken.license == 'BBQ'
    assert chicken.vendor == "Carl's BBQ"
    assert chicken.sourcerpm == 'chicken-2.2.10-1.fc27.src.rpm'
    assert chicken.build_time == datetime.datetime.fromtimestamp(buildtime)
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
    buildtime = get_buildtimes('brisket-5.1.1-1.fc27.noarch.rpm')
    assert repr(brisket) == '<SQLitePackage: "brisket-1:5.1.1-1.fc27.noarch">'
    assert brisket.name == 'brisket'
    assert brisket.arch == 'noarch'
    assert brisket.summary == 'Brisket'
    assert brisket.description == 'Brisket.'
    assert brisket.packager == 'Carl'
    assert brisket.url == 'https://example.com/brisket'
    assert brisket.license == 'BBQ'
    assert brisket.vendor == "Carl's BBQ"
    assert brisket.sourcerpm == 'brisket-5.1.1-1.fc27.src.rpm'
    assert brisket.build_time == datetime.datetime.fromtimestamp(buildtime)
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
    buildtime = get_buildtimes('pork-ribs-3.2.0-1.fc27.noarch.rpm')
    assert repr(pork_ribs) == '<SQLitePackage: "pork-ribs-3.2.0-1.fc27.noarch">'
    assert pork_ribs.name == 'pork-ribs'
    assert pork_ribs.arch == 'noarch'
    assert pork_ribs.summary == 'Pork ribs'
    assert pork_ribs.description == 'Pork ribs.'
    assert pork_ribs.packager == 'Carl'
    assert pork_ribs.url == 'https://example.com/ribs'
    assert pork_ribs.license == 'BBQ'
    assert pork_ribs.vendor == "Carl's BBQ"
    assert pork_ribs.sourcerpm == 'ribs-3.2.0-1.fc27.src.rpm'
    assert pork_ribs.build_time == datetime.datetime.fromtimestamp(buildtime)
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
