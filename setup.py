import os
from setuptools import find_packages, setup
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

version = __import__('simons_spark_genbank').__version__

setup(
    name='GenBank',
    version=version,
    author='Dan Dodson',
    author_email='daniel@dndodson.com',
    description='Tools for interacting with GenBank data.',
    package_dir={'': 'src'},
    packages=find_packages(where="./src"),
    include_package_data=True,
    scripts=['src/genbank-query.py'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
)