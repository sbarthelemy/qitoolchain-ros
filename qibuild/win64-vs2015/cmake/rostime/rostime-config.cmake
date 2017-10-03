set(_root "${CMAKE_CURRENT_LIST_DIR}/../../..")
get_filename_component(_root ${_root} ABSOLUTE)

set(ROSTIME_LIBRARIES
  optimized;${_root}/lib/rostime.lib;
  debug;${_root}/lib/rostime_d.lib;
  CACHE INTERNAL "" FORCE
)

set(ROSTIME_INCLUDE_DIRS
  ${_root}/include
  CACHE INTERNAL "" FORCE
)

qi_persistent_set(ROSTIME_DEPENDS "BOOST_DATE_TIME;BOOST_SYSTEM;BOOST_THREAD")

qi_persistent_set(ROSTIME_DEFINITIONS
   "ROS_BUILD_SHARED_LIBS"
)
export_lib(ROSTIME)
