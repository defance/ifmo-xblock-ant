import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='ifmo-xblock-academicnt',
    version='9.0',
    install_requires=[
        'django',
        'path.py',
        'celery',
        'requests',
        'XBlock',
        'ifmo-edx-celery-grader==4.0',
    ],
    packages=[
        'xblock_ant',
    ],
    include_package_data=True,
    license='BSD License',
    description='Package provides celery grader.',
    long_description=README,
    url='https://www.de.ifmo.ru/',
    author='Dmitrii Ivaniushin',
    author_email='defance@gmail.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License', 
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
    ],
    entry_points={
        'xblock.v1': [
            'ifmo_xblock_ant = xblock_ant:AntXBlock',
        ]
    },
)
