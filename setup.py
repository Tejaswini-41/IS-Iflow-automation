from setuptools import setup, find_packages

setup(
    name='sap-cpi-iflow-analyzer',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A tool for analyzing SAP CPI iFlow files and generating visualizations.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/sap-cpi-iflow-analyzer',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'lxml',
        'jsonschema',
        'beautifulsoup4',
        'pytest'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)