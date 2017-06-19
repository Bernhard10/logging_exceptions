from setuptools import setup
import os.path

# Get the long description from the README file
with open('README.rst') as f:
    long_description = f.read()


setup(name='logging_exceptions',
      version='0.1.4',
      py_modules=['logging_exceptions'],
      author="Bernhard C. Thiel",
      author_email="thiel@tbi.univie.ac.at",
      description="Self-logging exceptions: Attach log messages to exceptions and output them conditionally.",
      long_description=long_description,
      url='https://github.com/Bernhard10/logging_exceptions',
      license='MIT',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.5'
      ],
      keywords='logging exceptions'

      )
