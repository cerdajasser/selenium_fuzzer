from setuptools import setup, find_packages

setup(
    name='selenium_fuzzer',
    version='0.0.1',
    author='Jasser Cerda',
    author_email='cerdajasser@gmail.com',
    description='A Selenium-based fuzzer for input fields in Angular Material applications.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/cerdajasser/selenium_fuzzer',
    packages=find_packages(),
    install_requires=[
        'selenium>=3.141.0',
        # Add other dependencies here
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
)
