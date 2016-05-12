set(_root "${CMAKE_CURRENT_LIST_DIR}/../../..")
get_filename_component(_root ${_root} ABSOLUTE)

set(ROSTIME_LIBRARIES
  ${_root}/lib/librostime.so
  CACHE INTERNAL "" FORCE
)

set(ROSTIME_INCLUDE_DIRS
  ${_root}/include
  CACHE INTERNAL "" FORCE
)

qi_persistent_set(ROSTIME_DEPENDS "BOOST_DATE_TIME;BOOST_SYSTEM;BOOST_THREAD")
export_lib(ROSTIME)
