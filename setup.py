from setuptools import setup


setup(
    name='repomd',
    version='0.1.0',
    description='library for reading dnf/yum repositories',
    url='https://github.com/carlwgeorge/repomd',
    license='MIT',
    package_dir={'': 'source'},
    py_modules=['repomd'],
    python_requires='>=3.6',
    setup_requires=['setuptools>=24.2.0'],
    install_requires=['lxml'],
    extras_require={
        'tests': ['pytest'],
        'style': ['pytest-flake8'],
        'coverage': ['pytest-cov', 'codecov']
    }
)
