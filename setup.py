# https://packaging.python.org/tutorials/distributing-packages/

from setuptools import setup

readme = open('README.md', 'r')
README_TEXT = readme.read()
readme.close()

setup(
    name='dsh',
    version='2.2.0',
    author='flashashen',
    author_email='flashashen@gmail.com',
    description='console application to organize commands and environments',
    license = "MIT",
    url="https://github.com/flashashen/dsh2",
    classifiers= [
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3'   ,
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development',
        'Environment :: Console',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
        'Development Status :: 3 - Alpha',

    ],
    platforms='osx,linux',
    keywords="shell console yaml",
    long_description=README_TEXT,
    long_description_content_type='text/markdown',
    packages=['dsh'],
    package_data={'dsh': ['data/*']},
    tests_require=['nose', 'jsonschema'],
    test_suite="tests",
    install_requires=[
        'flange>=1.0.0',
        'prompt_toolkit>3.0',
        'pygments',
        'Click'
    ],
    entry_points='''
        [console_scripts]
        dsh=dsh.main:cli
    ''',
)