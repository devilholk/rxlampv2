#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>
#include <libopencm3/stm32/usart.h>
#include <libopencm3/stm32/timer.h>

#define SOPTUNNA
//#define RXLAMP



#define FIRE_START 1000
#define FIRE_END 3000
#define MAX_INTENSITY 5400
#define INTENSITY_VARIATION 250

//Here we import some python stuff for the python precompiler
#python from stonerlights import *

//Bind a few python functions
#pyfunc gamma_correction_LUT
#pyfunc full_sine_sLUT
#pyfunc Pin_Setup
#pyfunc init_pins
#pyfunc PWM_Setup



gamma_correction_LUT("LUT_gamma", math.e, 4096, 4095);	//Create a 12 bit by 12 bit LUT for gamma e (2.7)
full_sine_sLUT("LUT_sine", 4096, 4096);


Pin_Setup( (PA3,) , MODE.IN_PUPD);


#ifdef RXLAMP

	#define TIMS_ELD

	// 22:07 <&sterna> den är väldigt röd
	// 22:07 <&sterna> peta in lite mer grönt där

	const uint32_t R_comp = 4096;
	const uint32_t G_comp = 4096;
	const uint32_t B_comp = 4096;


	// 21:57 <&sterna> #define SET_BLUE()I(GPIOA->BSRR = GPIO_Pin_1)
	// 21:57 <&sterna> #define SET_GREEN() (GPIOA->BSRR = GPIO_Pin_2)
	// 21:57 <&sterna> #define SET_RED()I(GPIOB->BSRR = GPIO_Pin_0)

	Pin_Setup( (PA1, PA2, PB0), MODE.AF_PP, BANDWIDTH.MAX ); //Setup pins for alternate function push-pull output


	#define LED_R	TIM3_CCR3
	#define LED_G	TIM2_CCR3
	#define LED_B	TIM2_CCR2

#endif

#ifdef SOPTUNNA

	const uint32_t R_comp = 4096;
	const uint32_t G_comp = 2949;
	const uint32_t B_comp = 3072;

	Pin_Setup( (PA0, PB8, PB9), MODE.AF_PP, BANDWIDTH.MAX ); //Setup pins for alternate function push-pull output

	#define LED_R	TIM4_CCR3
	#define LED_G	TIM2_CCR1
	#define LED_B	TIM4_CCR4

#endif

#ifndef LED_R
	#error "Varken RXLAMP eller SOPTUNNA är definierad, jag vet fan inte vad du tänkte köra denna koden på"
#endif




unsigned long xorshf96(void) {          //period 2^96-1

    static uint32_t x=123456789, y=362436069, z=521288629;

    unsigned long t;
        x ^= x << 16;
        x ^= x >> 5;
        x ^= x << 1;

       t = x;
       x = y;
       y = z;
       z = t ^ x ^ y;

  return z;
}


static void clock_setup(void)
{
	rcc_clock_setup_in_hsi_out_24mhz();


	/* Enable clocks for GPIO port A (for GPIO_USART1_TX) and USART1. */
	rcc_periph_clock_enable(RCC_GPIOA);
	rcc_periph_clock_enable(RCC_GPIOB);
	rcc_periph_clock_enable(RCC_USART1);

	rcc_periph_clock_enable(RCC_TIM2);
	rcc_periph_clock_enable(RCC_TIM3);
	rcc_periph_clock_enable(RCC_TIM4);

//rx lamp has &TIM3->CCR3, &TIM2->CCR3, &TIM2->CCR2

	#ifdef RXLAMP
		PWM_Setup(TIM3, 4096, OC3);				//Initialize timers and PWM channels
		PWM_Setup(TIM2, 4096, (OC2, OC3));
	#endif

	#ifdef SOPTUNNA
		PWM_Setup(TIM2, 4096, OC1);				//Initialize timers and PWM channels
		PWM_Setup(TIM4, 4096, (OC3, OC4));
	#endif



}


inline void colorHexagon(int hue, int *R, int *G, int *B) {
	int frac = hue >> 12;
	int ci = hue & 0xFFF;
	int cd = 4095 - ci;
	int cs = 4095;
	switch (frac) {
		case 0:	*R = cs;	*G = ci;	*B = 0; break;		//R1	G+	B0
		case 1:	*R = cd;	*G = cs;	*B = 0; break;		//R-	G1	B0
		case 2:	*R = 0;	*G = cs;	*B = ci; break;	//R0	G1	B+
		case 3:	*R = 0;	*G = cd;	*B = cs; break;	//R0	G-	B1
		case 4:	*R = ci;	*G = 0;	*B = cs; break;	//R+	G0	B1
		case 5:	*R = cs;	*G = 0;	*B = cd; break;	//R1	G0	B-
	}
}

int main(void)
{
	int counter=0;
	int i, j = 0, c = 0;

	clock_setup();
	init_pins();
	gpio_set(GPIOA, GPIO3);	//Pull up

	while (1) {


		#ifdef TIMS_ELD
			if (gpio_get(GPIOA, GPIO3)) {
				LED_R=0,
				LED_G=0;
				LED_B=0;
				while(gpio_get(GPIOA, GPIO3));
			}
		#endif 

		counter++;


		int R=0, G=0, B=0;



		int hue = LUT_sine[(counter*15) & 0xFFF];
		hue = (hue * LUT_sine[(counter*17 + 100) & 0xFFF]) / 4096;
		hue = (hue * LUT_sine[(counter*19 + 5222) & 0xFFF]) / 4096;
		hue = (hue * LUT_sine[(counter*23 + 124) & 0xFFF]) / 4096;

		int intensity_deviance = LUT_sine[(counter*23) & 0xFFF];
		intensity_deviance = (intensity_deviance * LUT_sine[(counter*19 + 5623) & 0xFFF]) / 4096;
		intensity_deviance = (intensity_deviance * LUT_sine[(counter*21 + 3052) & 0xFFF]) / 4096;
		intensity_deviance = (intensity_deviance * LUT_sine[(counter*27 + 256) & 0xFFF]) / 4096;


		hue = (unsigned int)(hue+4096) >> 1;

		int intensity = hue + intensity_deviance * INTENSITY_VARIATION / 4096;
		if (intensity < -4096) {
			intensity = -4096;
		}

		if (intensity > 4095) {
			intensity = 4095;
		}

		intensity = (unsigned int)(intensity+4096);		//This ones goes to 8191 but that is too white for fire



		intensity= (intensity*MAX_INTENSITY)>>13;


		colorHexagon ( ((hue * (FIRE_END - FIRE_START)) >> 12) + FIRE_START, &R, &G, &B);

		//Om intensiteten är över 4096 så börjar vi gå mot vitt istället
		if (intensity < 4096) {
			LED_R = LUT_gamma[((((uint32_t)R * R_comp) >> 12) * intensity) >> 12];
			LED_G = LUT_gamma[((((uint32_t)G * G_comp) >> 12) * intensity) >> 12];
			LED_B = LUT_gamma[((((uint32_t)B * B_comp) >> 12) * intensity) >> 12];
		} else {
			intensity-=4096;
			int inv = 4095-intensity;			

			LED_R = LUT_gamma[(((((uint32_t)R * R_comp) >> 12) * inv) >> 12) + intensity];
			LED_G = LUT_gamma[(((((uint32_t)G * G_comp) >> 12) * inv) >> 12) + intensity];
			LED_B = LUT_gamma[(((((uint32_t)B * B_comp) >> 12) * inv) >> 12) + intensity];


			// LED_R = ((LUT_gamma[((uint32_t)R * R_comp) >> 12] * inv) >> 12) + intensity;
			// LED_G = ((LUT_gamma[((uint32_t)G * G_comp) >> 12] * inv) >> 12) + intensity; 
			// LED_B = ((LUT_gamma[((uint32_t)B * B_comp) >> 12] * inv) >> 12) + intensity; 
		}

		for (volatile int i=0;i!=10000;i++);

	}


	return 0;
}
