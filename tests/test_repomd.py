from unittest import mock

import pytest
import lxml

import repomd


@pytest.fixture
@mock.patch('repomd.urlopen')
def repo(mock_urlopen):
    repodata_path = 'tests/fixtures/repodata'
    with open(f'{repodata_path}/repomd.xml', 'rb') as f:
        repomd_xml = f.read()
    with open(f'{repodata_path}/primary.xml.gz', 'rb') as f:
        primary_xml = f.read()
    mock_urlopen.return_value.__enter__.return_value.read.side_effect = (repomd_xml, primary_xml)
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
