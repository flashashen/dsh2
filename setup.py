# https://packaging.python.org/tutorials/distributing-packages/

from setuptools import setup

readme = open('README.md', 'r')
README_TEXT = readme.read()
readme.close()

setup(
    name='dsh2',
    version='2.0.1',
    author='flashashen',
    author_email='flashashen@gmail.com',
    description='Autoload configuration from multiple sources. Autotranslate config into usable objects',
    license = "MIT",
    url="https://github.com/flashashen/dsh2",
    classifiers= [
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development',
        'Environment :: Console',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
        'Development Status :: 3 - Alpha',

    ],
    platforms='osx,linux',
    keywords = "shell console configuration yaml object registry",
    long_description=README_TEXT,
    packages=['dsh'],
    package_data={'dsh': ['data/*']},
    tests_require = ['nose','jsonschema'],
    test_suite="nose.collector",
    install_requires=[
        'flange',
        'PyYAML',
        'prompt_toolkit',
        'anyconfig',
        'jsonschema',
        'six',

    ],
    entry_points='''
        [console_scripts]
        dsh2=dsh.main:main
    ''',
)