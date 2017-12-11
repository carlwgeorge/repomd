import pytest

import repomd


@pytest.fixture
def repodata():
    path = 'tests/fixtures/repodata'
    with open(f'{path}/repomd.xml', 'rb') as f:
        raw_index = f.read()
    with open(f'{path}/primary.xml.gz', 'rb') as f:
        raw_primary = f.read()
    return (raw_index, raw_primary)


def test_repo_init():
    repo = repomd.Repo('https://example.com')
    assert repo.baseurl == 'https://example.com'
