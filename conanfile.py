# -*- coding: utf-8 -*-
#
# Copyright 2012-2019 CNRS-UM LIRMM, CNRS-AIST JRL
#

from conans import ConanFile, CMake, tools
import os
import shutil

class SCHCoreConan(ConanFile):
    name = "sch-core"
    version = "1.0.3"
    description = "Efficient implementation of GJK algorithm for proximity queries (collision detection, distance computations, penetration depths and witness points) between convex shapes."
    topics = ("robotics", "collision", "proximity", "convex")
    url = "https://github.com/jrl-umi3218/sch-core"
    homepage = "https://github.com/jrl-umi3218/sch-core"
    author = "Pierre Gergondet <pierre.gergondet@gmail.com>"
    license = "BSD-2-Clause"
    exports = ["LICENSE"]
    exports_sources = ["CMakeLists.txt", "conan/CMakeLists.txt", "cmake/*", "CMakeModules/*", "doc/*", "examples/*", "include/*", "src/*", "README.md", "conan/FindBoost.cmake"]
    generators = ["cmake_find_package", "cmake_paths"]
    settings = "os", "arch", "compiler", "build_type"

    requires = (
        # We don't really care for a specific version of Boost and conan has >= 1.64
        "boost/1.73.0"
    )

    def source(self):
        # Wrap the original CMake file to call conan_basic_setup
        shutil.move("CMakeLists.txt", "CMakeListsOriginal.txt")
        shutil.move(os.path.join("conan", "CMakeLists.txt"), "CMakeLists.txt")
        # Make sure we find conan's Boost not system Boost
        pattern = 'include(CMakeFindDependencyMacro)'
        replacement = '''set(BOOST_ROOT "${{PACKAGE_PREFIX_DIR}}")
set(Boost_NO_SYSTEM_PATHS ON)
list(APPEND CMAKE_MODULE_PATH "${{CMAKE_CURRENT_LIST_DIR}}")
{}'''.format(pattern)
        tools.replace_in_file('cmake/Config.cmake.in', pattern, replacement)
        # Install the up-to-date FindBoost.cmake
        pattern = 'add_subdirectory(src)'
        replacement = '''{}
install(FILES conan/FindBoost.cmake DESTINATION lib/cmake/sch-core)'''.format(pattern)
        tools.replace_in_file('CMakeListsOriginal.txt', pattern, replacement)
        # Link with Boost::Boost if consumed by conan
        pattern = "Boost::serialization Boost::disable_autolinking"
        replacement = "$<BUILD_INTERFACE:Boost::Boost>$<INSTALL_INTERFACE:$<IF:$<BOOL:CONAN_BOOST_ROOT>,Boost::Boost,{}>>".format(pattern.replace(' ', '$<SEMICOLON>'))
        tools.replace_in_file('src/CMakeLists.txt', pattern, replacement)

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions['BUILD_TESTING'] = False
        cmake.definitions['SCH_BUILD_BSD'] = True
        cmake.configure()
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        cmake = self._configure_cmake()
        pattern = "BOOL:CONAN_BOOST_ROOT"
        replacement = "BOOL:${CONAN_BOOST_ROOT}"
        generated = os.path.join(self.build_folder, 'CMakeFiles', 'Export', 'lib', 'cmake', self.name, '{}Targets.cmake'.format(self.name))
        tools.replace_in_file(generated, pattern, replacement)
        cmake.install()

    def deploy(self):
        self.copy("*")
        self.copy_deps("*")

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        self.env_info.LD_LIBRARY_PATH.append(os.path.join(self.package_folder, 'lib'))
