# encoding: utf-8
import os
import sys
from setuptools import setup, find_packages, findall
sys.path.append('.')
import version


HERE = os.path.abspath(os.path.dirname(__file__))


def find_package_data():
    ignore_ext = {'.py', '.pyc', '.pyo'}
    base_package = 'restfw'
    package_data = {}
    root = os.path.join(HERE, base_package)
    for path in findall(root):
        if path.endswith('~'):
            continue
        ext = os.path.splitext(path)[1]
        if ext in ignore_ext:
            continue

        # Find package name
        package_path = os.path.dirname(path)
        while package_path != root:
            if os.path.isfile(os.path.join(package_path, '__init__.py')):
                break
            package_path = os.path.dirname(package_path)
        package_name = package_path[len(HERE) + 1:].replace(os.path.sep, '.')

        globs = package_data.setdefault(package_name, set())
        data_path = path[len(package_path) + 1:]
        data_glob = os.path.join(os.path.dirname(data_path), '*' + ext)
        globs.add(data_glob)
    for key, value in package_data.items():
        package_data[key] = list(value)
    return package_data


def cli_cmd(app_name, command_name, func_name=None):
    func_name = func_name or command_name
    tpl = '{cmd} = restfw.{app}.commands.{cmd}:{func}.cli'
    return tpl.format(cmd=command_name, app=app_name, func=func_name)


README = open(os.path.join(HERE, 'README.txt')).read()
CHANGES = open(os.path.join(HERE, 'CHANGES.txt')).read()


setup(
    name='restfw',
    version=version.get_version(),
    description='REST framework for Pyramid',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Framework :: Pyramid',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'License :: OSI Approved :: MIT License',
    ],
    keywords='',
    author='ASD Technologies',
    author_email='team@asdtech.co',
    url='',
    package_dir={'': '.'},
    packages=find_packages(),
    package_data=find_package_data(),
    zip_safe=False,
    extras_require={
        'test': [
            'pytest',
            'webob',
            'mock',
            'asset',
            'docker-py',
            'WebTest',
        ],
        'docs': [
            'WebTest',
            'sphinx_rtd_theme',
            'sphinxcontrib-blockdiag',
        ]
    },
    install_requires=[
        'setuptools',
        'six',
        'colander',
        'pyramid>=1.8.3',
        'pyramid_jinja2',
        'pyramid_zodbconn',
        'zope.interface',
        'ZODB',
        'ZEO',
        'pyramid_tm',
        'pyramid_retry',
        'transaction',
        'persistent',
        'mountbit.utils',
    ],
    entry_points={
        'console_scripts':
        [
            'restfw_test = restfw.runtests:runtests [test]',
        ],
    },
)
