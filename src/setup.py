# encoding: utf-8
import os
import sys
from setuptools import setup, find_packages
sys.path.append('.')
import version


HERE = os.path.abspath(os.path.dirname(__file__))


def cli_cmd(app_name, command_name, func_name=None):
    func_name = func_name or command_name
    tpl = '{cmd} = restfw.{app}.commands.{cmd}:{func}.cli'
    return tpl.format(cmd=command_name, app=app_name, func=func_name)


README = open(os.path.join(HERE, 'README.rst')).read()
CHANGES = open(os.path.join(HERE, 'CHANGES.rst')).read()


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
    url='https://bitbucket.org/asdtech/restfw',
    package_dir={'': '.'},
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    extras_require={
        'test': [
            'pytest',
            'mock',
            'asset',
            'WebTest',
            'cykooz.testing',
        ],
        'docs': [
            'WebTest',
            'sphinx',
            'jinja2',
            'pathlib2;python_version<"3.4"',
        ]
    },
    install_requires=[
        'setuptools',
        'six',
        'colander',
        'pyramid>=1.8.3',
        'WebOb>=1.8.1',
        'zope.interface',
        'requests',
        'lru-dict',
        'venusian',
    ],
    entry_points={
        'console_scripts':
        [
            'restfw_test = restfw.runtests:runtests [test]',
        ],
    },
)
