#include <stdlib.h>
#include <string.h>
#include "pico/stdlib.h"
#include "pico/multicore.h" 
#include "pico/cyw43_arch.h"
#include "hardware/adc.h" 
#include "hardware/timer.h"
#include "hardware/irq.h"

#include "lwip/pbuf.h"
#include "lwip/tcp.h"
#include "picow_ap.h"

#define DEBUG_printf printf

// Use alarm 0
#define ALARM_NUM 0
#define ALARM_IRQ TIMER_IRQ_0

#define LED_PIN 14 
#define SAMPLING_INTERVAL_us 31 
#define ADC_CONVERSION_TIME_us 2
#define BUFF_SIZE 1024 

// Alarm interrupt handler
static volatile bool alarm_fired;
volatile int i = 0 ;
uint16_t tmp[BUFF_SIZE] ;
uint32_t time_interval = 30;  

static void alarm_irq(void) {
    alarm_fired = true;
    hw_clear_bits(&timer_hw->intr, 1u << ALARM_NUM);
    timer_hw->alarm[ALARM_NUM] = timer_hw->timerawl + SAMPLING_INTERVAL_us ;
}

static void alarm_in_us(uint32_t delay_us) {
    hw_set_bits(&timer_hw->inte, 1u << ALARM_NUM);
    irq_set_exclusive_handler(ALARM_IRQ, alarm_irq);
    irq_set_enabled(ALARM_IRQ, true);

    uint64_t target = timer_hw->timerawl + delay_us;
    timer_hw->alarm[ALARM_NUM] = (uint32_t) target;
}

void core1_main() {

  adc_init();
  adc_gpio_init(26);
  adc_select_input(0);

  alarm_in_us(time_interval);

  while(1) {
    alarm_fired = false;
    // printf("%u\n",time_interval);

    // wait for alarm to fire
    while (!alarm_fired);
    tmp[i++] = adc_read() ;
    if(i == BUFF_SIZE){
      i = 0 ;
      for(int i=0; i < BUFF_SIZE; i++){
        adc_16_bits[i] = tmp[i];
      }
        
    } 

  }
}

int main() {
    stdio_init_all();

    multicore_reset_core1();
    multicore_launch_core1(&core1_main);

    while(1) {
      printf("%u\n",time_interval);
      run_tcp_server_test();
    }

    return 0;
}

