#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UAV Edge SDK - Setup Script

用于安装 Python 包和构建 C++ 模块
"""

import os
import sys
import subprocess
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext


class CMakeExtension(Extension):
    """CMake 扩展模块"""

    def __init__(self, name: str, sourcedir: str = '') -> None:
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    """CMake 构建命令"""

    def build_extension(self, ext: CMakeExtension) -> None:
        ext_fullpath = os.path.abspath(
            os.path.join(self.build_lib, *ext.name.split('.'))
        )
        extdir = os.path.dirname(ext_fullpath)

        cmake_args = [
            f'-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={extdir}',
            f'-DPYTHON_EXECUTABLE={sys.executable}',
            '-DCMAKE_BUILD_TYPE=Release',
        ]

        build_args = ['--config', 'Release']

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)

        subprocess.run(
            ['cmake', ext.sourcedir, '-DCMAKE_BUILD_TYPE=Release'] + cmake_args,
            cwd=self.build_temp,
            check=True,
        )

        subprocess.run(
            ['cmake', '--build', '.', '--config', 'Release'] + build_args,
            cwd=self.build_temp,
            check=True,
        )


setup(
    name='uav-edge-sdk',
    version='1.0.0',
    author='Dithiothreitol',
    description='UAV Edge SDK with C++/Python hybrid implementation',
    long_description='High-performance UAV edge computing SDK with offline path planning and weather risk assessment',
    url='https://github.com/yourusername/uav-edge-sdk',
    license='Apache 2.0',
    packages=['edge_sdk'],
    ext_modules=[CMakeExtension('edge_sdk.edge_sdk_cpp')],
    cmdclass={'build_ext': CMakeBuild},
    zip_safe=False,
    python_requires='>=3.8',
)
