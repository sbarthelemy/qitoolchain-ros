import argparse
import multiprocessing
import os
import subprocess
import sys

from qisys import ui
import qisys.script
import qisys.envsetter
import qisys.sh
import qibuild.config
import qitoolchain


THIS_DIR = os.path.dirname(os.path.realpath(__file__))

KNOWN_PLATFORMS = [
    ("linux", "linux"),
    ("mac", "mac"),
    ("win", "windows"),
]

KNOWN_TARGETS = [
    "linux32",
    "linux64",
    "mac64",
    "win32-vs2013",
    "win64-vs2015",
]

def get_platform(build_config):
    for short_name, long_name in KNOWN_PLATFORMS:
        if short_name in build_config.name:
            return long_name
    else:
        sys.exit("Could not guess platform from %s" % build_config.name)

def get_target(build_config):
    for target in KNOWN_TARGETS:
        if target in build_config.name:
            return target
    else:
        sys.exit("Could not guess target from %s" % build_config.name)


def get_build_env(build_config):
    """ Read env settings from ~/.config/qi/qibuild.xml """
    # This is required to find CMake at the correct location,
    # and to source vcvarsall.bat on Windows

    qibuild_cfg = qibuild.config.QiBuildConfig()
    qibuild_cfg.read()
    qibuild_cfg.set_active_config(build_config.name)
    envsetter = qisys.envsetter.EnvSetter()
    envsetter.read_config(qibuild_cfg)
    return envsetter.get_build_env()

def parse_repos(build_config):
    platform = get_platform(build_config)
    repos = []
    with open(os.path.join(THIS_DIR, 'src-%s.yml' % platform)) as fd:
        repos = []
        repo = {}
        for line in fd:
            line = line.strip()
            if not line:
                continue
            if line == '- git:':
                assert(not repo)
            else:
                key, value = line.split(':', 1)
                repo[key.strip()] = value.strip()
                if len(repo) == 3:
                    repos.append(repo)
                    repo = {}
        return repos

def prepare_sources(workspace, build_config):
    src_dir = os.path.join(workspace, "src")
    qisys.sh.mkdir(src_dir, recursive=True)
    repos = parse_repos(build_config)
    for r in repos:
        local_name = r['local-name']
        dest = os.path.join(src_dir, local_name)
        if os.path.exists(dest):
            print "Skipping", dest
        else:
            qisys.command.call(['git', 'clone', '--branch', r['version'], r['uri'], dest])
            apply_patches(workspace, build_config, local_name)

def apply_patches(workspace, build_config, local_name):
    platform = get_platform(build_config)
    patches_dir = os.path.join(THIS_DIR, "patches", platform, local_name)
    src = os.path.join(workspace, "src", local_name)
    if not os.path.exists(patches_dir):
        return
    ui.info(":: Patching", local_name)
    patches = [os.path.join(patches_dir, x) for x in os.listdir(patches_dir)
            if x.endswith(".patch")]
    for patch_path in patches:
        patch_cmd = ["patch",
                        "--batch",
                        "--ignore-whitespace",
                        "--strip=1",
                        "--input", patch_path]
        ui.info("Applying patch", patch_path)
        qisys.command.call(patch_cmd, cwd=src)

def init_workspace(workspace):
    workspace = os.path.join(THIS_DIR, "workspace")
    src_dir = os.path.join(workspace, "src")
    top_cmake = os.path.join(src_dir, "CMakeLists.txt")
    if os.path.exists(top_cmake):
        ui.info("catkin workspace already initialized")
        return
    catkin_script = os.path.join(src_dir, "catkin", "bin", "catkin_init_workspace")
    cmd = [sys.executable, catkin_script, "."]
    qisys.command.call(cmd, cwd=src_dir)

def configure(workspace, build_config, build_type="Release"):
    build_dir = os.path.join(workspace, "build-%s" % build_type)
    qisys.sh.mkdir(build_dir, recursive=True)
    platform = get_platform(build_config)
    toolchain = qitoolchain.get_toolchain(build_config.toolchain)
    toolchain.update()
    ui.info(str(toolchain))
    toolchain_path = toolchain.db.db_path
    cmake_args = list()

    cmake_args.append("-Wno-dev")
    cmake_args.append("-DCMAKE_BUILD_TYPE=%s" % build_type)

    # Find Boost in toolchain
    boost_path = toolchain.get_package("boost", raises=True).path
    boost_root = qisys.sh.to_posix_path(boost_path)
    cmake_args.append("-DBOOST_ROOT=%s" % boost_root)
    # our boost package assumes boost libs are shared:
    cmake_args.append("-DBoost_USE_STATIC_LIBS=OFF")

    # Find Eigen3 in toolchain
    eigen_path = toolchain.get_package("eigen3", raises=True).path
    eigen_root = qisys.sh.to_posix_path(eigen_path)
    cmake_args.append("-DEIGEN_ROOT=%s" % eigen_root)

    # Find console_bridge in toolchain
    console_bridge_path = toolchain.get_package("console_bridge", raises=True).path
    console_bridge_dir = os.path.join(console_bridge_path,
                                      "share", "cmake", "console_bridge")
    console_bridge_dir = qisys.sh.to_posix_path(console_bridge_dir)
    cmake_args.append("-Dconsole_bridge_DIR=%s" % console_bridge_dir)

    # Need an absolute, non-empty path for CMAKE_INSTALL_PREFIX
    cmake_args.append("-DCMAKE_INSTALL_PREFIX=/prefix")

    # Don't bother building tests:
    cmake_args.append("-DCATKIN_ENABLE_TESTING=OFF")


    if platform == "linux":
        cmake_include_path = list()
        cmake_lib_path = list()
        # Need to find lz4 and bz2 (deps of rosbag) in toolchain:
        for dep in ["bzip2", "lz4"]:
            package_path = toolchain.get_package(dep, raises=True).path
            include_path = os.path.join(package_path, "include")
            lib_path = os.path.join(package_path, "lib")
            cmake_include_path.append(include_path)
            cmake_lib_path.append(lib_path)
        cmake_args.append("-DCMAKE_INCLUDE_PATH=%s" % ";".join(cmake_include_path))
        cmake_args.append("-DCMAKE_LIBRARY_PATH=%s" % ";".join(cmake_lib_path))

    cmake_args.append("-DCMAKE_CXX_FLAGS=-std=gnu++11")

    if platform == "windows":
        cmake_args.append("-DCMAKE_DEBUG_POSTFIX=_d")
        cmake_flags = (
            # our boost package assumes boost libs are shared:
            ("BOOST_ALL_DYN_LINK", "1"),
            # ros/time.h uses #ifdef WIN32 instead of #ifdef _WIN32 ...
            ("WIN32", "1"),
        )

        cmake_flags_arg = "-DCMAKE_CXX_FLAGS="
        for key, value in cmake_flags:
            cmake_flags_arg += "/D%s=%s " % (key, value)

        # re-add some flags
        # (they get removed when we set CMAKE_CXX_FLAGS
        # for some reason)
        # /EHsc is required for exceptions, and
        # /MD for linking with the 'dynamic' runtime
        cmake_flags_arg += "/EHsc /MD"
        cmake_args.append(cmake_flags_arg)

    if platform != "linux":
        # Ninja may not work on linux ...
        cmake_args.append("-GNinja")


    cmake_args.append("../src")

    build_env = get_build_env(build_config)
    qisys.command.call(["cmake"] + cmake_args, env=build_env, cwd=build_dir)

def build(workspace, build_config, build_type):
    platform = get_platform(build_config)
    build_dir = os.path.join(workspace, "build-%s" % build_type)
    build_env = get_build_env(build_config)
    build_args = ["--build", build_dir]
    if platform == "linux":
        build_args += ["--", "-j", str(multiprocessing.cpu_count())]
    qisys.command.call(["cmake"] + build_args, env=build_env)

def install(workspace, build_config, build_type="Release"):
    install_dir = os.path.join(THIS_DIR, "install", "ros-%s" % build_config.name)
    build_dir = os.path.join(workspace, "build-%s" % build_type)
    build_env = get_build_env(build_config)
    build_env["DESTDIR"]=qisys.sh.to_posix_path(install_dir)
    qisys.command.call(["cmake", "-P", "cmake_install.cmake"],
                       env=build_env,
                       cwd=build_dir)
    return install_dir

def configure_build_install(workspace, build_config):
    platform = get_platform(build_config)
    if platform == "windows":
        configure(workspace, build_config, build_type="Debug")
        build(workspace, build_config, build_type="Debug")
        install(workspace, build_config, build_type="Debug")
    configure(workspace, build_config, build_type="Release")
    build(workspace, build_config, build_type="Release")
    install_dir = install(workspace, build_config, build_type="Release")
    return install_dir

def make_package(install_dir, build_config, tmpdir):
    platform = get_platform(build_config)
    prefix = os.path.join(install_dir, "prefix")
    # Only keep useful stuff:
    subdirs = ["include", "lib"]
    for subdir in subdirs:
        src = os.path.join(prefix, subdir)
        dest = os.path.join(tmpdir, subdir)
        qisys.sh.install(src, dest)
    # On Windows, only keep dlls in bin:
    if platform == "windows":
        bin_dest = os.path.join(tmpdir, "bin")
        bin_src = os.path.join(prefix, "bin")
        qisys.sh.mkdir(bin_dest, recursive=True)
        dlls = [x for x in os.listdir(bin_src) if x.endswith(".dll")]
        for dll in dlls:
            src = os.path.join(bin_src, dll)
            qisys.sh.install(src, bin_dest)

    # Remove pkgconfig
    qisys.sh.rm(os.path.join(tmpdir, "lib", "pkgconfig"))

    # Remove Python stuff
    if platform == "windows":
        site_packages = "lib/site-packages"
    else:
        site_packages = "lib/python2.7/site-packages"
    qisys.sh.rm(os.path.join(tmpdir, site_packages))

    # Add qibuild/cmake stuff:
    target = get_target(build_config)
    src = os.path.join(THIS_DIR, "qibuild", target, "cmake")
    dest = os.path.join(tmpdir, "share", "cmake")
    qisys.sh.install(src, dest)

    # Add package.xml
    src = os.path.join(THIS_DIR, "qibuild", target, "package.xml")
    qisys.sh.install(src, tmpdir)

    res = qisys.script.run_action("qitoolchain.actions.make_package",
                                  args=[tmpdir, "--output", os.getcwd()])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", required=True, dest="build_config_name",
                        help="Name of a build config matching a toolchain")
    args = parser.parse_args()
    build_config_name = args.build_config_name
    qibuild_cfg = qibuild.config.QiBuildConfig()
    qibuild_cfg.read()
    build_config = qibuild_cfg.configs.get(build_config_name)
    if not build_config:
        sys.exit("No such build config: %s" % build_config_name)
    toolchain_name = build_config.toolchain
    if not toolchain_name:
        sys.exit("No toolchain configured for build config: %s" % build_config)

    workspace = os.path.join(THIS_DIR, "workspace")
    prepare_sources(workspace, build_config)
    init_workspace(workspace)
    install_dir = configure_build_install(workspace, build_config)
    with qisys.sh.TempDir() as tmp:
        make_package(install_dir, build_config, tmp)

if __name__ == "__main__":
    main()
