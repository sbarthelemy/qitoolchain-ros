set(_root "${CMAKE_CURRENT_LIST_DIR}/../../..")
get_filename_component(_root ${_root} ABSOLUTE)

set(TF2_LIBRARIES

  ${_root}/lib/libtf2.so
  CACHE INTERNAL "" FORCE
)

set(TF2_INCLUDE_DIRS
  ${_root}/include
  CACHE INTERNAL "" FORCE
)

qi_persistent_set(TF2_DEPENDS "CONSOLE_BRIDGE;ROSTIME")
export_lib(TF2)
