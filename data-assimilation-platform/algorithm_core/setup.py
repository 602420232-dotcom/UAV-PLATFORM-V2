from setuptools import setup, find_packages
import os
import importlib.util

here = os.path.abspath(os.path.dirname(__file__))


spec = importlib.util.spec_from_file_location(
    '__version__', os.path.join(here, 'src/bayesian_assimilation/__version__.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
__version__ = getattr(mod, '__version__', '1.0.0')


with open(os.path.join(here, 'README.md'), 'r', encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='bayesian_assimilation',
    version=__version__,
    description='贝叶斯数据同化核心算法库',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Data Assimilation Team',
    author_email='H13396600636@163.com',
    url='https://github.com/602420232-dotcom/weather.git',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    python_requires='>=3.8',
    install_requires=[
        'numpy>=1.24.0',
        'scipy>=1.11.0',
        'netCDF4>=1.6.0',
        'h5py>=3.9.0',
        'pandas>=2.0.0',
        'scikit-learn>=1.3.0',
        'matplotlib>=3.7.0',
        'seaborn>=0.12.0',
    ],
    extras_require={
        'api': [
            'fastapi>=0.100.0',
            'uvicorn>=0.23.0',
            'pydantic>=2.0.0',
            'flask>=3.0.0',
            'flask-cors>=4.0.0',
        ],
        'parallel': [
            'ray>=2.0.0',
            'dask>=2023.1.0',
            'distributed>=2023.1.0',
            'mpi4py>=3.1.0',
        ],
        'gpu': [
            'cupy>=12.0.0',
            'jax>=0.4.0',
            'jaxlib>=0.4.0',
            'torch>=2.0.0',
        ],
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'pre-commit>=3.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
            'sphinx>=7.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'assimilate=bayesian_assimilation.api.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: Atmospheric Science',
        'Topic :: Scientific/Engineering :: Mathematics',
    ],
    keywords='data assimilation bayesian meteorology weather',
    license='MIT',
    license_expression='MIT',
)
