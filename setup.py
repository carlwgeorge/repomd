from setuptools import setup


with open('README.md') as f:
    long_description = f.read()


setup(
    name='repomd',
    version='0.1.0',
    author='Carl George',
    author_email='carl@george.computer',
    description='Library for reading dnf/yum repositories',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/carlwgeorge/repomd',
    license='MIT',
    package_dir={'': 'source'},
    py_modules=['repomd'],
    python_requires='>=3.6',
    setup_requires=['setuptools>=38.6.0'],
    tests_require=['pytest'],
    install_requires=['lxml'],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ],
)
