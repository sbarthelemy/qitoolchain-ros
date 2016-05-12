set(_root "${CMAKE_CURRENT_LIST_DIR}/../../..")
get_filename_component(_root ${_root} ABSOLUTE)

set(TF2_LIBRARIES
  optimized;${_root}/lib/cpp_common.lib;
  debug;${_root}/lib/cpp_common_d.lib;
  optimized;${_root}/lib/rostime.lib;
  debug;${_root}/lib/rostime_d.lib;
  optimized;${_root}/lib/tf2.lib;
  debug;${_root}/lib/tf2_d.lib;
  CACHE INTERNAL "" FORCE
)

set(TF2_INCLUDE_DIRS
  ${_root}/include
  CACHE INTERNAL "" FORCE
)

qi_persistent_set(TF2_DEPENDS
  "BOOST_CHRONO;BOOST_DATE_TIME;BOOST_SIGNALS;BOOST_SYSTEM;BOOST_THREAD;CONSOLE_BRIDGE"
)
qi_persistent_set(TF2_DEFINITIONS
   "ROS_BUILD_SHARED_LIBS"
)
export_lib(TF2)
