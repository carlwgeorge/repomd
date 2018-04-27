from setuptools import setup


with open('README.md') as f:
    long_description = f.read()


setup(
    name='repomd',
    version='0.1.0',
    description='library for reading dnf/yum repositories',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/carlwgeorge/repomd',
    license='MIT',
    package_dir={'': 'source'},
    py_modules=['repomd'],
    python_requires='>=3.6',
    setup_requires=['setuptools>=38.6.0'],
    install_requires=['lxml'],
    extras_require={
        'tests': ['pytest'],
        'style': ['pytest-flake8'],
        'coverage': ['pytest-cov', 'codecov']
    }
)
