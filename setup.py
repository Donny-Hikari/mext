from setuptools import setup, find_packages

setup(
  name='mext',
  version='0.1.0',
  author='donny',
  author_email='donny.hikari@gmail.com',
  description='Mext is an prompt template extension for LLM (large language model).',
  packages=['mext'],
  package_data={
    'mext': ['libs/*'],
  },
  install_requires=[],
  entry_points={},
)
