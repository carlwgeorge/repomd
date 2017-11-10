import repomd


def test_repo_init():
    repo = repomd.Repo('https://example.com')
    assert repo.baseurl == 'https://example.com'
