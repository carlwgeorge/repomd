.. image:: https://img.shields.io/travis/carlwgeorge/repomd.svg
   :alt: travis-ci.org
   :target: https://travis-ci.org/carlwgeorge/repomd

.. image:: https://img.shields.io/codecov/c/github/carlwgeorge/repomd.svg
   :alt: codecov.io
   :target: https://codecov.io/gh/carlwgeorge/repomd

repomd
======

This library provides an object-oriented interface to get information out of dnf/yum repositories.

Usage
-----

Create a repo instance from the baseurl of the repo.

.. code-block:: python

   >>> repo = Repo('http://mirror.centos.org/centos/7/os/x86_64')
