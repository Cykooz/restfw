import os

from setuptools import find_packages, setup


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.rst')) as f:
    CHANGES = f.read()

requires = [
    'plaster_pastedeploy',
    'pyramid',
    'restfw',
    'pyramid_debugtoolbar',
    'waitress',
]

tests_require = [
    'WebTest >= 1.3.1',  # py3 compat
    'pytest >= 3.7.4',
    'restfw[test]',
]

setup(
    name='storage',
    version='0.0',
    description='storage',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],

    author='',
    author_email='',
    url='',
    keywords='web pyramid restfw',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    extras_require={
        'test': tests_require,
    },
    install_requires=requires,
    entry_points={
        'console_scripts':
        [
            'storage_test = storage.runtests:runtests [test]',
        ],
        'paste.app_factory': [
            'main = storage.main:main',
        ],
    },
)
