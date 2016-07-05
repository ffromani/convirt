from __future__ import absolute_import
import os.path
from distutils.core import setup


def version():
    # MUST fail if cannot open the source file
    with open('PKG-INFO', 'rt') as info:
        for line in info:
            if line.startswith('Version'):
                name, value = line.strip().split(':')
                return value.strip()


def description():
    try:
        with open(os.path.join('docs', 'convirt-intro.rst'), 'rt') as desc:
            return desc.read()
    except IOError:
        return """
TODO
"""

setup(name='convirt',
      version=version(),
      description='Run containers with the libvirt API',
      long_description=description(),
      platforms = ['posix'],
      license = 'MIT',
      author = 'Francesco Romani',
      author_email = 'fromani@redhat.com',
      url='TODO',
      download_url='TODO',
      scripts=[
        'tools/convirt-setup-net',
        'tools/convirt-ls-runtimes',
      ],
      packages=['convirt', 'convirt.config',
                'convirt.metrics', 'convirt.runtimes'],
      install_requires=[
        "libvirt-python",
        "six",
      ],
      classifiers = [
        'Classifier: Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Classifier: Operating System :: POSIX',
        'License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Classifier: Topic :: Software Development :: Libraries',
        'Classifier: Topic :: Software Development :: Libraries :: Python Modules',
      ])
