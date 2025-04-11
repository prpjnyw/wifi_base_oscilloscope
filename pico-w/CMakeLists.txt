cmake_minimum_required(VERSION 3.13)

include(pico_sdk_import.cmake)

project(test_project C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()

add_executable(test
main.c
dhcpserver/dhcpserver.c
dnsserver/dnsserver.c
)

target_sources(test PRIVATE main.c picow_ap.c )
pico_enable_stdio_usb(test 1)

pico_enable_stdio_uart(test 1)

pico_add_extra_outputs(test)
    
target_include_directories(test PRIVATE 
${CMAKE_CURRENT_LIST_DIR} 
${CMAKE_CURRENT_LIST_DIR}/.. # for our common lwipopts
${CMAKE_CURRENT_LIST_DIR}/dhcpserver
${CMAKE_CURRENT_LIST_DIR}/dnsserver

)
target_link_libraries(test pico_cyw43_arch_lwip_threadsafe_background 
hardware_adc 
hardware_timer 
hardware_irq  
pico_multicore
pico_stdlib)
