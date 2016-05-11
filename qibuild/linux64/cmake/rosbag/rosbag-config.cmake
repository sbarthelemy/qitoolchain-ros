set(_root "${CMAKE_CURRENT_LIST_DIR}/../../..")
get_filename_component(_root ${_root} ABSOLUTE)

set(ROSBAG_LIBRARIES
  ${_root}/lib/libcpp_common.so
  ${_root}/lib/librosbag_storage.so
  ${_root}/lib/libroscpp_serialization.so
  ${_root}/lib/libroslz4.so
  ${_root}/lib/librostime.so
  CACHE INTERNAL "" FORCE
)

set(ROSBAG_INCLUDE_DIRS
  ${_root}/include
  CACHE INTERNAL "" FORCE
)

qi_persistent_set(ROSBAG_DEPENDS "CONSOLE_BRIDGE;BZIP2;BOOST;BOOST_SYSTEM;LZ4")
export_lib(ROSBAG)
