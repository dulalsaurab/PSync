# -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-

from waflib import Context, Logs, Utils
import os, subprocess

VERSION = '0.1.0'
APPNAME = 'PSync'
GIT_TAG_PREFIX = ''

def options(opt):
    opt.load(['compiler_c', 'compiler_cxx', 'gnu_dirs'])
    opt.load(['default-compiler-flags', 'coverage', 'sanitizers',
              'boost', 'doxygen', 'sphinx_build'],
             tooldir=['.waf-tools'])

    optgrp = opt.add_option_group('PSync Options')
    optgrp.add_option('--with-examples', action='store_true', default=False,
                      help='Build examples')
    optgrp.add_option('--with-tests', action='store_true', default=False,
                      help='Build unit tests')
    optgrp.add_option('--lite', action='store_true', default=False,
                      help='Compile full consumer only')

def configure(conf):
    conf.load(['compiler_c', 'compiler_cxx', 'gnu_dirs',
               'default-compiler-flags', 'boost',
               'doxygen', 'sphinx_build'])

    conf.env.WITH_EXAMPLES = conf.options.with_examples
    conf.env.WITH_TESTS = conf.options.with_tests
    conf.env.LITE = conf.options.lite

    if conf.options.lite:
        conf.define('LITE', 1)

    if 'PKG_CONFIG_PATH' not in os.environ:
        os.environ['PKG_CONFIG_PATH'] = Utils.subst_vars('${LIBDIR}/pkgconfig', conf.env)
    conf.check_cfg(package='libndn-cxx', args=['--cflags', '--libs'], uselib_store='NDN_CXX')

    boost_libs = ['system', 'iostreams']
    if conf.env.WITH_TESTS:
        boost_libs.append('unit_test_framework')

    conf.check_boost(lib=boost_libs, mt=True)

    conf.check_compiler_flags()

    # Loading "late" to prevent tests from being compiled with profiling flags
    conf.load('coverage')
    conf.load('sanitizers')

    # If there happens to be a static library, waf will put the corresponding -L flags
    # before dynamic library flags.  This can result in compilation failure when the
    # system has a different version of the PSync library installed.
    conf.env.prepend_value('STLIBPATH', ['.'])

    conf.define_cond('WITH_TESTS', conf.env.WITH_TESTS)
    conf.define_cond('LITE', conf.env.LITE)
    # The config header will contain all defines that were added using conf.define()
    # or conf.define_cond().  Everything that was added directly to conf.env.DEFINES
    # will not appear in the config header, but will instead be passed directly to the
    # compiler on the command line.
    conf.write_config_header('PSync/detail/config.hpp', define_prefix='PSYNC_')

def build(bld):
    bld.shlib(
        target='PSync',
        vnum=VERSION,
        cnum=VERSION,
        source=bld.path.ant_glob('PSync/**/*.cpp'),
        use='BOOST NDN_CXX',
        includes='.',
        export_includes='.')

    if bld.env.WITH_TESTS:
        bld.recurse('tests')

    if bld.env.WITH_EXAMPLES:
        bld.recurse('examples')

    headers = bld.path.ant_glob('PSync/**/*.hpp')
    bld.install_files(bld.env['INCLUDEDIR'], headers, relative_trick=True)

    bld.install_files('${INCLUDEDIR}/PSync/detail',
                      bld.path.find_resource('PSync/detail/config.hpp'))

    bld(features='subst',
        source='PSync.pc.in',
        target='PSync.pc',
        install_path = '${LIBDIR}/pkgconfig',
        PREFIX       = bld.env['PREFIX'],
        INCLUDEDIR   = bld.env['INCLUDEDIR'],
        VERSION      = VERSION)

def docs(bld):
    from waflib import Options
    Options.commands = ['doxygen', 'sphinx'] + Options.commands

def doxygen(bld):
    version(bld)

    if not bld.env.DOXYGEN:
        bld.fatal('Cannot build documentation ("doxygen" not found in PATH)')

    bld(features='subst',
        name='doxygen.conf',
        source=['docs/doxygen.conf.in',
                'docs/named_data_theme/named_data_footer-with-analytics.html.in'],
        target=['docs/doxygen.conf',
                'docs/named_data_theme/named_data_footer-with-analytics.html'],
        VERSION=VERSION,
        HTML_FOOTER='../build/docs/named_data_theme/named_data_footer-with-analytics.html' \
                        if os.getenv('GOOGLE_ANALYTICS', None) \
                        else '../docs/named_data_theme/named_data_footer.html',
        GOOGLE_ANALYTICS=os.getenv('GOOGLE_ANALYTICS', ''))

    bld(features='doxygen',
        doxyfile='docs/doxygen.conf',
        use='doxygen.conf')

def sphinx(bld):
    version(bld)

    if not bld.env.SPHINX_BUILD:
        bld.fatal('Cannot build documentation ("sphinx-build" not found in PATH)')

    bld(features='sphinx',
        config='docs/conf.py',
        outdir='docs',
        source=bld.path.ant_glob('docs/**/*.rst'),
        VERSION=VERSION)

def version(ctx):
    # don't execute more than once
    if getattr(Context.g_module, 'VERSION_BASE', None):
        return

    Context.g_module.VERSION_BASE = Context.g_module.VERSION
    Context.g_module.VERSION_SPLIT = VERSION_BASE.split('.')

    # first, try to get a version string from git
    gotVersionFromGit = False
    try:
        cmd = ['git', 'describe', '--always', '--match', '%s*' % GIT_TAG_PREFIX]
        out = subprocess.check_output(cmd, universal_newlines=True).strip()
        if out:
            gotVersionFromGit = True
            if out.startswith(GIT_TAG_PREFIX):
                Context.g_module.VERSION = out.lstrip(GIT_TAG_PREFIX)
            else:
                # no tags matched
                Context.g_module.VERSION = '%s-commit-%s' % (VERSION_BASE, out)
    except (OSError, subprocess.CalledProcessError):
        pass

    versionFile = ctx.path.find_node('VERSION')
    if not gotVersionFromGit and versionFile is not None:
        try:
            Context.g_module.VERSION = versionFile.read()
            return
        except EnvironmentError:
            pass

    # version was obtained from git, update VERSION file if necessary
    if versionFile is not None:
        try:
            if versionFile.read() == Context.g_module.VERSION:
                # already up-to-date
                return
        except EnvironmentError as e:
            Logs.warn('%s exists but is not readable (%s)' % (versionFile, e.strerror))
    else:
        versionFile = ctx.path.make_node('VERSION')

    try:
        versionFile.write(Context.g_module.VERSION)
    except EnvironmentError as e:
        Logs.warn('%s is not writable (%s)' % (versionFile, e.strerror))

def dist(ctx):
    version(ctx)

def distcheck(ctx):
    version(ctx)
