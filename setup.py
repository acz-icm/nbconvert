#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

# the name of the package
name = 'nbconvert'

#-----------------------------------------------------------------------------
# Minimal Python version sanity check
#-----------------------------------------------------------------------------

import sys

v = sys.version_info
if v[:2] < (2,7) or (v[0] >= 3 and v[:2] < (3,3)):
    error = "ERROR: %s requires Python version 2.7 or 3.3 or above." % name
    print(error, file=sys.stderr)
    sys.exit(1)

PY3 = (sys.version_info[0] >= 3)

#-----------------------------------------------------------------------------
# get on with it
#-----------------------------------------------------------------------------

import os
from glob import glob
from io import BytesIO
try:
    from urllib.request import urlopen
except ImportError:
    from urllib import urlopen

from distutils.core import setup
from distutils.cmd import Command
from distutils.command.build import build
from distutils.command.sdist import sdist

pjoin = os.path.join
here = os.path.abspath(os.path.dirname(__file__))
pkg_root = pjoin(here, name)

packages = []
for d, _, _ in os.walk(pjoin(here, name)):
    if os.path.exists(pjoin(d, '__init__.py')):
        packages.append(d[len(here)+1:].replace(os.path.sep, '.'))

package_data = {
    'nbconvert.filters' : ['marked.js'],
    'nbconvert.resources' : ['style.min.css'],
    'nbconvert' : [
        'tests/files/*.*',
        'exporters/tests/files/*.*',
        'preprocessors/tests/files/*.*',
    ],
}


notebook_css_version = '4.0.0-dev'
css_url = "http://cdn.jupyter.org/notebook/%s/style/style.min.css" % notebook_css_version

class FetchCSS(Command):
    description = "Fetch Notebook CSS from Jupyter CDN"
    user_options = []
    def initialize_options(self):
        pass
    
    def finalize_options(self):
        pass
    
    def _download(self):
        try:
            return urlopen(css_url).read()
        except Exception as e:
            if 'ssl' in str(e).lower():
                try:
                    import pycurl
                except ImportError:
                    print("Failed, try again after installing PycURL with `pip install pycurl` to avoid outdated SSL.", file=sys.stderr)
                    raise e
                else:
                    print("Failed, trying again with PycURL to avoid outdated SSL.", file=sys.stderr)
                    return self._download_pycurl()
            raise e
    
    def _download_pycurl(self):
        """Download CSS with pycurl, in case of old SSL (e.g. Python < 2.7.9)."""
        import pycurl
        c = pycurl.Curl()
        c.setopt(c.URL, css_url)
        buf = BytesIO()
        c.setopt(c.WRITEDATA, buf)
        c.perform()
        return buf.getvalue()
    
    def run(self):
        dest = os.path.join('nbconvert', 'resources', 'style.min.css')
        if not os.path.exists('.git') and os.path.exists(dest):
            # not running from git, nothing to do
            return
        print("Downloading CSS: %s" % css_url)
        try:
            css = self._download()
        except Exception as e:
            msg = "Failed to download css from %s: %s" % (css_url, e)
            print(msg, file=sys.stderr)
            if os.path.exists(dest):
                print("Already have CSS: %s, moving on." % dest)
            else:
                raise OSError("Need Notebook CSS to proceed: %s" % dest)
            return
        
        with open(dest, 'wb') as f:
            f.write(css)
        print("Downloaded Notebook CSS to %s" % dest)

cmdclass = {'css': FetchCSS}

def css_first(command):
    class CSSFirst(command):
        def run(self):
            self.distribution.run_command('css')
            return command.run(self)
    return CSSFirst

cmdclass['build'] = css_first(build)
cmdclass['sdist'] = css_first(sdist)

for d, _, _ in os.walk(pjoin(pkg_root, 'templates')):
    g = pjoin(d[len(pkg_root)+1:], '*.*')
    package_data['nbconvert'].append(g)


version_ns = {}
with open(pjoin(here, name, '_version.py')) as f:
    exec(f.read(), {}, version_ns)


setup_args = dict(
    name            = name,
    description     = "Converting Jupyter Notebooks",
    version         = version_ns['__version__'],
    scripts         = glob(pjoin('scripts', '*')),
    packages        = packages,
    package_data    = package_data,
    cmdclass        = cmdclass,
    author          = 'Jupyter Development Team',
    author_email    = 'jupyter@googlegroups.com',
    url             = 'http://jupyter.org',
    license         = 'BSD',
    platforms       = "Linux, Mac OS X, Windows",
    keywords        = ['Interactive', 'Interpreter', 'Shell', 'Web'],
    classifiers     = [
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ],
)

if 'develop' in sys.argv or any(a.startswith('bdist') for a in sys.argv):
    import setuptools

setuptools_args = {}
install_requires = setuptools_args['install_requires'] = [
    'mistune!=0.6',
    'jinja2',
    'pygments',
    'traitlets',
    'jupyter_core',
    'nbformat',
]

extras_require = setuptools_args['extras_require'] = {
    'test': ['nose', 'ipykernel'],
    'serve': ['tornado'],
    'execute': ['jupyter_client'],
}

if 'setuptools' in sys.modules:
    from setuptools.command.develop import develop
    cmdclass['develop'] = css_first(develop)

    setup_args.update(setuptools_args)

if __name__ == '__main__':
    setup(**setup_args)
