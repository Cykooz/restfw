# encoding: utf-8
import os
import sys

from setuptools import find_packages, findall, setup


sys.path.append('.')
import version


HERE = os.path.abspath(os.path.dirname(__file__))


def cli_cmd(app_name, command_name, func_name=None):
    func_name = func_name or command_name
    tpl = '{cmd} = restfw.{app}.commands.{cmd}:{func}.cli'
    return tpl.format(cmd=command_name, app=app_name, func=func_name)


README = open(os.path.join(HERE, 'README.rst')).read()
CHANGES = open(os.path.join(HERE, 'CHANGES.rst')).read()


def find_package_data(include_paths=None):
    include_paths = set(include_paths or [])
    ignore_ext = {'.py', '.pyc', '.pyo'}
    base_package = 'restfw'
    package_data = {}
    root = os.path.join(HERE, base_package)
    for path in findall(root):
        if path.endswith('~'):
            continue
        rel_path = path[len(HERE) :]
        is_strict_path = False
        ext = os.path.splitext(path)[1]

        if rel_path in include_paths:
            is_strict_path = True
        else:
            if ext in ignore_ext:
                continue

        # Find package name
        package_path = os.path.dirname(path)
        while package_path != root:
            if os.path.isfile(os.path.join(package_path, '__init__.py')):
                break
            package_path = os.path.dirname(package_path)
        package_name = package_path[len(HERE) + 1 :].replace(os.path.sep, '.')

        globs = package_data.setdefault(package_name, set())
        data_path = path[len(package_path) + 1 :]
        data_glob = (
            data_path
            if is_strict_path
            else os.path.join(os.path.dirname(data_path), '*' + ext)
        )
        globs.add(data_glob)
    for key, value in package_data.items():
        package_data[key] = list(value)
    return package_data


setup(
    name='restfw',
    version=version.get_version(),
    description='REST framework for Pyramid',
    long_description=README + '\n\n' + CHANGES,
    long_description_content_type='text/x-rst',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Framework :: Pyramid',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'License :: OSI Approved :: MIT License',
    ],
    keywords='',
    author='Kirill Kuzminykh',
    author_email='cykooz@gmail.com',
    url='https://github.com/Cykooz/restfw',
    package_dir={'': '.'},
    packages=find_packages(),
    package_data=find_package_data(),
    include_package_data=True,
    zip_safe=False,
    extras_require={
        'test': [
            'pytest',
            'mock',
            'asset',
            'WebTest',
            'cykooz.testing',
            'requests',
            'pendulum',
        ],
        'docs': [
            'WebTest',
            'sphinx>=4.0',
            'jinja2',
            'requests',
            'cykooz.testing',
        ],
    },
    install_requires=[
        'setuptools',
        'colander',
        'pyramid>=2.0',
        'WebOb>=1.8.1',
        'zope.interface',
        'lru-dict',
        'venusian',
        'WebOb',
    ],
    entry_points={
        'console_scripts': [
            'restfw_test = restfw.runtests:runtests [test]',
        ],
    },
)
