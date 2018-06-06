from setuptools import setup
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='vmjuggler',
    version='0.1.0',
    description="vmjuggler provides the simple high level API to VMWare’s SDK.",
    long_description=long_description,
    # long_description_content_type='text/plain, text/x-rst',
    url='https://github.com/shurkam/vmjuggler',
    author='Alexandr Malygin',
    author_email='shurkam@gmail.com',

    # Classifiers help users find your project by categorizing it.
    #
    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[  # Optional
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='vmware pyvmomi vm vcenter API devops sdk',
    packages=['vmjuggler'],
    install_requires=['pyvmomi>=6.5', 'future-fstrings>=0.4.2'],

    # List additional URLs that are relevant to your project as a dict.
    #
    # This field corresponds to the "Project-URL" metadata fields:
    # https://packaging.python.org/specifications/core-metadata/#project-url-multiple-use
    #
    # Examples listed include a pattern for specifying where the package tracks
    # issues, where the source is hosted, where to say thanks to the package
    # maintainers, and where to support the project financially. The key is
    # what's used to render the link text on PyPI.
    project_urls={  # Optional
        # 'Documentation': 'https://vmjuggler.readthedocs.org/',  # TODO:
        'Bug Reports': 'https://github.com/shurkam/vmjuggler/issues',
        'Source': 'https://github.com/shurkam/vmjuggler/',

    },
)
