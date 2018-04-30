cmake_minimum_required(VERSION 3.4.1)


add_library( vshare-lib

             SHARED

             src/main/cpp/native-lib.cpp
             src/main/cpp/vshare-jni.c
             src/main/cpp/suinput.c
             )


find_library(log-lib
              log )

target_link_libraries( vshare-lib
                       ${log-lib} )