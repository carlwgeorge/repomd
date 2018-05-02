from unittest import mock

import pytest
from lxml import etree

import repomd


def load_repodata(path):
    with open(f'{path}/repomd.xml', 'rb') as f:
        repomd_xml = f.read()
    with open(f'{path}/primary.xml.gz', 'rb') as f:
        primary_xml = f.read()
    return (repomd_xml, primary_xml)


@pytest.fixture
@mock.patch('repomd.urlopen')
def repo(mock_urlopen):
    mock_urlopen.return_value.__enter__.return_value.read.side_effect = load_repodata('tests/data/repo/repodata')
    return repomd.Repo('https://example.com')


@pytest.fixture
def lazy_repo():
    return repomd.Repo('https://example.com', lazy=True)


@pytest.fixture
@mock.patch('repomd.urlopen')
def empty_repo(mock_urlopen):
    mock_urlopen.return_value.__enter__.return_value.read.side_effect = load_repodata('tests/data/empty_repo/repodata')
    return repomd.Repo('https://example.com')


def test_repo(repo):
    assert repo.baseurl == 'https://example.com'
    assert isinstance(repo._metadata, etree._Element)


def test_lazy_repo(lazy_repo):
    assert lazy_repo.baseurl == 'https://example.com'
    assert lazy_repo._metadata is None
    with mock.patch('repomd.urlopen') as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value.read.side_effect = load_repodata('tests/data/repo/repodata')
        lazy_repo.load()
    assert isinstance(lazy_repo._metadata, etree._Element)


def test_repo_repr(repo):
    assert repr(repo) == '<Repo: "https://example.com">'


def test_repo_str(repo):
    assert str(repo) == 'https://example.com'


def test_repo_len(repo, empty_repo):
    assert len(repo) == 5
    assert len(empty_repo) == 0
