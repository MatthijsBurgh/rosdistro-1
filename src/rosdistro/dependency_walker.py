# Software License Agreement (BSD License)
#
# Copyright (c) 2013, Open Source Robotics Foundation, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Open Source Robotics Foundation, Inc. nor
#    the names of its contributors may be used to endorse or promote
#    products derived from this software without specific prior
#    written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from catkin_pkg.package import InvalidPackage, parse_package_string


class DependencyWalker(object):

    def __init__(self, release_instance):
        self._release_instance = release_instance
        self._packages = {}

    def _get_package(self, pkg_name):
        if pkg_name not in self._packages:
            repo = self._release_instance.repositories[self._release_instance.packages[pkg_name].repository_name]
            assert repo.version is not None, "Package '%s' in repository '%s' has no version set" % (pkg_name, repo.name)
            assert 'release' in repo.tags, "Package '%s' in repository '%s' has no 'release' tag set" % (pkg_name, repo.name)
            pkg_xml = self._release_instance.get_package_xml(pkg_name)
            try:
                pkg = parse_package_string(pkg_xml)
            except InvalidPackage as e:
                raise InvalidPackage(pkg_name + ': %s' % str(e))
            self._packages[pkg_name] = pkg
        return self._packages[pkg_name]

    def get_depends(self, pkg_name, depend_type, ros_packages_only=False):
        '''Return a set of package names which the package depends on.'''
        deps = self._get_dependencies(pkg_name, depend_type)
        if ros_packages_only:
            deps = deps & set(self._release_instance.packages.keys())
        return deps

    def get_recursive_depends(self, pkg_name, depend_types, ros_packages_only=False, ignore_pkgs=None):
        '''Return a set of package names which the package (transitively) depends on.'''
        if ignore_pkgs is None:
            ignore_pkgs = []
        depends = set([])
        pkgs_to_check = set([pkg_name])
        while pkgs_to_check:
            next_pkg_to_check = pkgs_to_check.pop()
            if next_pkg_to_check in ignore_pkgs:
                continue
            for depend_type in depend_types:
                deps = self.get_depends(next_pkg_to_check, depend_type)
                if ros_packages_only:
                    deps = deps & set(self._release_instance.packages.keys())
                new_deps = deps - depends
                pkgs_to_check |= new_deps
                depends |= new_deps
        return depends

    def get_depends_on(self, pkg_name, depend_type):
        '''Return a set of package names which depend on the package.'''
        depends_on = set([])
        for name in self._release_instance.packages.keys():
            pkg = self._release_instance.packages[name]
            repo = self._release_instance.repositories[pkg.repository_name]
            if repo.version is None:
                continue
            deps = self._get_dependencies(name, depend_type)
            if pkg_name in deps:
                depends_on.add(name)
        return depends_on

    def get_recursive_depends_on(self, pkg_name, depend_types, ignore_pkgs=None):
        '''Return a set of package names which (transitively) depend on the package.'''
        if ignore_pkgs is None:
            ignore_pkgs = []
        depends_on = set([])
        pkgs_to_check = set([pkg_name])
        while pkgs_to_check:
            next_pkg_to_check = pkgs_to_check.pop()
            if next_pkg_to_check in ignore_pkgs:
                continue
            for depend_type in depend_types:
                deps = self.get_depends_on(next_pkg_to_check, depend_type)
                new_deps = deps - depends_on
                pkgs_to_check |= new_deps
                depends_on |= new_deps
        return depends_on

    def _get_dependencies(self, pkg_name, dep_type):
        pkg = self._get_package(pkg_name)
        deps = {
            'buildtool': pkg.buildtool_depends,
            'build': pkg.build_depends,
            'run': pkg.run_depends,
            'test': pkg.test_depends
        }
        return set([d.name for d in deps[dep_type]])
