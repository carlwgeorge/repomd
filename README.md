[![travis-ci.org](https://img.shields.io/travis/carlwgeorge/repomd.svg)](https://travis-ci.org/carlwgeorge/repomd)
[![codecov.io](https://img.shields.io/codecov/c/github/carlwgeorge/repomd.svg)](https://codecov.io/gh/carlwgeorge/repomd)

# repomd

This library provides an object-oriented interface to get information out of dnf/yum repositories.

## Usage

Import the Repo class from the module.

```python
>>> from repomd import Repo
```

Create a repo instance from the baseurl of the repo.

```python
>>> repo = Repo('http://mirror.centos.org/centos/7/os/x86_64')
```

Optionally, you can delay loading of the repo metadata.

```python
>>> repo = Repo('http://mirror.centos.org/centos/7/os/x86_64', lazy=True)
>>> repo.load()
```
