# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
add_executable(tkur_timer_unit timer_unit.cpp)
target_include_directories(tkur_timer_unit PRIVATE ../src)
target_compile_options(tkur_timer_unit PRIVATE -UNDEBUG)
add_test(NAME timer_unit COMMAND tkur_timer_unit)
add_executable(tkur_runtime_fixture runtime_fixture.cpp)
target_link_libraries(tkur_runtime_fixture PRIVATE tkur_fuzzer)
add_executable(tkur_c_smoke flat.c)
target_compile_options(tkur_c_smoke PRIVATE -fsanitize=fuzzer-no-link)
set_target_properties(tkur_c_smoke PROPERTIES LINKER_LANGUAGE CXX)
target_link_libraries(tkur_c_smoke PRIVATE tkur_fuzzer)
add_test(NAME c_direct_new_stall COMMAND tkur_c_smoke --new-stall 1)
add_test(NAME c_direct_cov_stall COMMAND tkur_c_smoke --cov-stall=1)
set_tests_properties(c_direct_new_stall c_direct_cov_stall PROPERTIES
  PASS_REGULAR_EXPRESSION "TKUR: stopping after" TIMEOUT 10)
# This optional regression runner uses CMake only, not Python.
add_test(NAME runtime_regressions COMMAND ${CMAKE_COMMAND}
  -DFIXTURE=$<TARGET_FILE:tkur_runtime_fixture>
  -DWORK=${CMAKE_CURRENT_BINARY_DIR}/regressions
  -P ${CMAKE_CURRENT_SOURCE_DIR}/regressions.cmake)
set_tests_properties(runtime_regressions PROPERTIES TIMEOUT 90)
