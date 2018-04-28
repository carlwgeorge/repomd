from unittest import mock

import pytest
import lxml

import repomd


@pytest.fixture
@mock.patch('repomd.urlopen')
def repo(mock_urlopen):
    path = 'tests/fixtures/repodata'
    with open(f'{path}/repomd.xml', 'rb') as f:
        raw_index = f.read()
    with open(f'{path}/primary.xml.gz', 'rb') as f:
        raw_primary = f.read()
    mock_urlopen.return_value.__enter__.return_value.read.side_effect = (raw_index, raw_primary)
    return repomd.Repo('https://example.com')


@pytest.fixture
def lazy_repo():
    return repomd.Repo('https://example.com', lazy=True)


def test_repo_init(repo):
    assert repo.baseurl == 'https://example.com'
    assert repr(repo) == '<Repo: "https://example.com">'
    assert str(repo) == 'https://example.com'
    assert isinstance(repo._metadata, lxml.etree._Element)


def test_repo_init_lazy(lazy_repo):
    assert lazy_repo.baseurl == 'https://example.com'
    assert lazy_repo._metadata is None
