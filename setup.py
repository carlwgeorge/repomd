from setuptools import setup


setup(
    name='repomd',
    version='0.1.0',
    description='library for reading dnf/yum repositories',
    url='https://github.com/carlwgeorge/repomd',
    license='MIT',
    package_dir={'': 'source'},
    py_modules=['repomd'],
    extras_require={
        'tests': ['pytest'],
    }
)
