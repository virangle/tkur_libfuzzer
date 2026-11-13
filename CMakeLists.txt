# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
cmake_minimum_required(VERSION 3.22)
project(tkur_libfuzzer VERSION 0.2.0 LANGUAGES C CXX)
if(NOT CMAKE_SYSTEM_NAME STREQUAL "Linux")
  message(FATAL_ERROR "This release supports Linux only")
endif()
if(NOT CMAKE_CXX_COMPILER_ID STREQUAL "Clang" OR
   CMAKE_CXX_COMPILER_VERSION VERSION_LESS 18 OR
   NOT CMAKE_CXX_COMPILER_VERSION VERSION_LESS 19)
  message(FATAL_ERROR "Use clang++-18 (-DCMAKE_CXX_COMPILER=clang++-18)")
endif()
include(cmake/VerifySources.cmake)
include(GNUInstallDirs)
find_package(Threads REQUIRED)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
file(GLOB TKUR_SOURCES CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/src/Fuzzer*.cpp")
list(REMOVE_ITEM TKUR_SOURCES
  "${CMAKE_CURRENT_SOURCE_DIR}/src/FuzzerMain.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/src/FuzzerInterceptors.cpp")
add_library(tkur_fuzzer_objects OBJECT ${TKUR_SOURCES})
target_link_libraries(tkur_fuzzer_objects PRIVATE Threads::Threads)
target_compile_options(tkur_fuzzer_objects PRIVATE -O2 -g -pthread -fno-omit-frame-pointer
  -fno-sanitize=all
  -fno-sanitize-coverage=trace-pc-guard,trace-cmp,inline-8bit-counters,pc-table
  "-ffile-prefix-map=${CMAKE_CURRENT_SOURCE_DIR}=tkur_libfuzzer"
  "-ffile-prefix-map=${CMAKE_CURRENT_BINARY_DIR}=tkur_libfuzzer-build")
add_library(tkur_fuzzer_no_main STATIC $<TARGET_OBJECTS:tkur_fuzzer_objects>)
set_target_properties(tkur_fuzzer_no_main PROPERTIES OUTPUT_NAME clang_rt.fuzzer_no_main)
add_library(tkur_fuzzer STATIC $<TARGET_OBJECTS:tkur_fuzzer_objects> src/FuzzerMain.cpp)
set_target_properties(tkur_fuzzer PROPERTIES OUTPUT_NAME clang_rt.fuzzer)
foreach(target tkur_fuzzer tkur_fuzzer_no_main)
  target_link_libraries(${target} PUBLIC Threads::Threads ${CMAKE_DL_LIBS})
endforeach()
configure_file(cmake/BUILD-INFO.txt.in BUILD-INFO.txt @ONLY)
install(TARGETS tkur_fuzzer tkur_fuzzer_no_main
  ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR} COMPONENT Runtime)
install(FILES LICENSE.LLVM.txt
  DESTINATION ${CMAKE_INSTALL_DATADIR}/tkur_libfuzzer COMPONENT Runtime)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/BUILD-INFO.txt"
  DESTINATION ${CMAKE_INSTALL_DATADIR}/tkur_libfuzzer COMPONENT Development)
install(FILES src/FuzzerInterface.h include/tkur_libfuzzer.h
  DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/tkur_libfuzzer COMPONENT Development)

option(TKUR_BUILD_TESTS "Build optional C/C++ tests; never installed or released" OFF)
if(TKUR_BUILD_TESTS)
  enable_testing()
  add_subdirectory(tests)
endif()

# Binary release contains only compiled archives and licensing/build metadata.
# No CMake, source, headers, executables, shell wrappers or Python scripts.
set(CPACK_GENERATOR TGZ)
set(CPACK_PACKAGE_NAME tkur_libfuzzer)
set(CPACK_PACKAGE_VERSION ${PROJECT_VERSION})
set(CPACK_PACKAGE_VENDOR TKUR)
set(CPACK_ARCHIVE_COMPONENT_INSTALL ON)
set(CPACK_COMPONENTS_ALL Runtime)
set(CPACK_ARCHIVE_RUNTIME_FILE_NAME "tkur_libfuzzer-${PROJECT_VERSION}-linux-${CMAKE_SYSTEM_PROCESSOR}")
set(CPACK_INCLUDE_TOPLEVEL_DIRECTORY OFF)
include(CPack)
