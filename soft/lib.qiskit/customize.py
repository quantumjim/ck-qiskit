#
# Collective Knowledge (individual environment - setup)
#
# See CK LICENSE.txt for licensing details
# See CK COPYRIGHT.txt for copyright details
#
# Author(s):
# - Grigori Fursin, cTuning foundation/dividiti
# - Flavio Vella, dividiti
# - Anton Lokhmotov, dividiti
#

import os


def version_cmd(i):
    path_with_init_py       = i['full_path']                            # the full_path that ends with PACKAGE_NAME/__init__.py
    path_without_init_py    = os.path.dirname( path_with_init_py )
    version_file_path       = os.path.join( path_without_init_py, 'VERSION.txt' )

    if os.path.isfile( version_file_path ):
        with open(version_file_path, 'r') as version_file:
            version_string = version_file.read().strip()
    else:
        version_string  = ''

    return {'return':0, 'cmd':'', 'version':version_string}


def setup(i):
    """
    Input:  {
              cfg              - meta of this soft entry
              self_cfg         - meta of module soft
              ck_kernel        - import CK kernel module (to reuse functions)

              host_os_uoa      - host OS UOA
              host_os_uid      - host OS UID
              host_os_dict     - host OS meta

              target_os_uoa    - target OS UOA
              target_os_uid    - target OS UID
              target_os_dict   - target OS meta

              target_device_id - target device ID (if via ADB)

              tags             - list of tags used to search this entry

              env              - updated environment vars from meta
              customize        - updated customize vars from meta

              deps             - resolved dependencies for this soft

              interactive      - if 'yes', can ask questions, otherwise quiet
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              bat          - prepared string for bat file
            }

    """

    import os

    # Get variables
    ck=i['ck_kernel']

    hosd    = i['host_os_dict']
    tosd    = i['target_os_dict']
    winh    = hosd.get('windows_base','')
    macos   = hosd.get('macos','')

    cus             = i.get('customize',{})
    ienv            = cus.get('install_env',{})

    fp              = cus.get('full_path','')
    p1              = os.path.dirname(fp)
    path_lib        = os.path.dirname(p1)
    path_install    = os.path.dirname(path_lib)

    env                     = i['env']
    env_prefix              = cus['env_prefix']
    env[env_prefix]         = path_install
    env[env_prefix+'_LIB']  = path_lib

    # Using a generic script to prepend the library search path
    # with the value expected to be set in $CK_ENV_COMPILER_GCC_LIB .
    #
    # GCC's dynamic library is an implicit dependency of Python's scipy package.
    # If this library is not found, dlopen() call buried deep in scipy library
    # fails to import ___addtf3 symbol.
    #
    # See this discussion:
    #   https://github.com/citwild/laugh-finder/issues/11#issuecomment-377997186
    #
    lib_path_adict = { 'action': 'lib_path_export_script',
                       'module_uoa': 'os',
                       'host_os_dict': hosd,
                       'lib_path': [ '$CK_ENV_COMPILER_GCC_LIB' ],
    }

    if not winh:
        pil_extra_dynamic_path = os.path.join(path_lib, 'PIL', '.dylibs' if macos else '.libs')
        lib_path_adict['lib_path'].insert(0, pil_extra_dynamic_path)

    r = ck.access( lib_path_adict )
    if r['return']>0: return r
    shell_setup_script_contents = r['script']

    # FIXME: Fix for Windows.
    # FIXME: Should have no explicit exports.
    if winh=='yes':
        shell_setup_script_contents += '\nset PYTHONPATH='+path_lib+';%PYTHONPATH%\n'
    else:
        shell_setup_script_contents += '\nexport PYTHONPATH='+path_lib+':${PYTHONPATH}\n'
        spath=os.path.join(path_lib, 'out', 'qiskit_simulator')
        shell_setup_script_contents += '\nexport CK_ENV_LIB_QISKIT_SIM='+spath+'\n'

    for k in ienv:
        if k.startswith('QISKIT_') or k=='CK_PYTHON_IPYTHON_BIN_FULL' or k=='CK_ENV_COMPILER_PYTHON_FILE':
           env[k]=ienv[k]
   
    return {'return':0, 'bat':shell_setup_script_contents}
