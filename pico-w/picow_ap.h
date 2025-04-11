#include <string.h>
#include <stdlib.h>

#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"
#include "lwip/pbuf.h"
#include "lwip/tcp.h"
#include "dhcpserver.h"
  
#define ADC_BUFF_SIZE 1024 

extern uint16_t adc_16_bits[ADC_BUFF_SIZE] ;
extern uint32_t time_interval ;

static err_t tcp_server_close(void *arg) ;

static err_t tcp_server_result(void *arg, int status) ;

static err_t tcp_server_sent(void *arg, struct tcp_pcb *tpcb, u16_t len) ;

err_t tcp_server_send_data(void *arg, struct tcp_pcb *tpcb) ;

err_t tcp_server_recv(void *arg, struct tcp_pcb *tpcb, struct pbuf *p, err_t err) ;

static err_t tcp_server_poll(void *arg, struct tcp_pcb *tpcb) ;

static void tcp_server_err(void *arg, err_t err) ;

static err_t tcp_server_accept(void *arg, struct tcp_pcb *client_pcb, err_t err) ;

static bool tcp_server_open(void *arg, const char *ap_name) ;

int run_tcp_server_test(void) ;

