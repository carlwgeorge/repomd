from unittest import mock

import pytest
import lxml

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
    mock_urlopen.return_value.__enter__.return_value.read.side_effect = load_repodata('tests/fixtures/repodata')
    return repomd.Repo('https://example.com')


@pytest.fixture
def lazy_repo():
    return repomd.Repo('https://example.com', lazy=True)


@pytest.fixture
@mock.patch('repomd.urlopen')
def empty_repo(mock_urlopen):
    mock_urlopen.return_value.__enter__.return_value.read.side_effect = load_repodata('tests/fixtures/empty_repodata')
    return repomd.Repo('https://example.com')


def test_repo_init(repo):
    assert repo.baseurl == 'https://example.com'
    assert repr(repo) == '<Repo: "https://example.com">'
    assert str(repo) == 'https://example.com'
    assert isinstance(repo._metadata, lxml.etree._Element)


def test_repo_init_lazy(lazy_repo):
    assert lazy_repo.baseurl == 'https://example.com'
    assert lazy_repo._metadata is None


def test_len(repo, empty_repo):
    assert len(repo) == 7
    assert len(empty_repo) == 0
