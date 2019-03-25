import pathlib

import setuptools


with pathlib.Path('README.md').open() as f:
    long_description = f.read()


setuptools.setup(
    name='repomd',
    version='0.2.1',
    author='Carl George',
    author_email='carl@george.computer',
    description='Library for reading dnf/yum repositories',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/carlwgeorge/repomd',
    license='MIT',
    package_dir={'': 'source'},
    py_modules=['repomd'],
    # f-strings
    python_requires='>=3.6',
    # markdown content type
    setup_requires=['setuptools>=38.6.0'],
    install_requires=[
        'defusedxml',
        'lxml',
    ],
    extras_require={
        'test': [
            'pytest',
            'pytest-cov',
            'pytest-flake8',
        ],
    },
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
    ],
)
