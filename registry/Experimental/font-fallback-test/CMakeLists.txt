cmake_minimum_required(VERSION 3.16)
project(font-fallback-test LANGUAGES CXX RC)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_definitions(-DUNICODE -D_UNICODE)
add_definitions(-D_CRT_SECURE_NO_WARNINGS)

set(SOURCES
    main.cpp
    resource.rc
)

add_executable(font-fallback-test WIN32 ${SOURCES})

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

target_link_libraries(font-fallback-test
    user32
    gdi32
    comctl32
    advapi32
)

if (MSVC)
    target_compile_options(font-fallback-test PRIVATE
        /O2
        /W3
    )
    # 静态链接运行库
    # set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded")
endif()

if (MINGW)
    target_link_options(font-fallback-test PRIVATE
        -O3
    )
endif()

set_target_properties(font-fallback-test PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)

add_custom_command(
    TARGET font-fallback-test POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${CMAKE_SOURCE_DIR}/config.ini"
        "$<TARGET_FILE_DIR:font-fallback-test>/config.ini"
)
