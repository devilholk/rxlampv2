#encoding=utf-8

import math

def gamma_correction_LUT(name, gamma, size, ceiling):
	return 'const uint16_t %s[%s] = {%s}' % (name, size, ','.join(['%i' % round((float(v)/float(size))**gamma * float(ceiling)) for v in range(size)]))

def full_sine_LUT(name, size, ceiling):
	return 'const uint16_t %s[%s] = {%s}' % (name, size, ','.join(['%i' % (round(math.sin(v*math.pi*2.0/size)*ceiling+ceiling) >> 1) for v in range(size)]))

def full_sine_sLUT(name, size, max):
	return 'const int16_t %s[%s] = {%s}' % (name, size, ','.join(['%i' % (round(math.sin(v*math.pi*2.0/size)*max)) for v in range(size)]))


class BANDWIDTH():
	BW50 = 'GPIO_MODE_OUTPUT_50_MHZ'
	BW2 = 'GPIO_MODE_OUTPUT_2_MHZ'
	MAX = BW50
	MIN = BW2



PIN_TABLE=set()

def Pin_Setup(pins, mode, bandwidth=BANDWIDTH.MAX):
	global PIN_TABLE
	if not hasattr(pins, '__iter__'):
		pins=(pins,)

	print ("pins: ", pins)

	for pin in pins:
		PIN_TABLE.add((pin, mode(pin, bandwidth)))


for port, pins in (
		('A', range(16)),
		('B', range(16)),
	):
	for pin in pins:
		globals()['P%s%s' % (port, pin)] = 'GPIO%s' % port, 'GPIO%i' % pin 


class MODE():
	AF_PP = lambda pin, bw: 'gpio_set_mode(%s, %s, GPIO_CNF_OUTPUT_ALTFN_PUSHPULL, %s);' %(pin[0], bw, pin[1])
	IN = lambda pin, bw: 'gpio_set_mode(%s, GPIO_MODE_INPUT, GPIO_CNF_INPUT_FLOAT, %s);' %(pin[0], pin[1])
	IN_PUPD = lambda pin, bw: 'gpio_set_mode(%s, GPIO_CNF_INPUT_PULL_UPDOWN, GPIO_CNF_INPUT_FLOAT, %s);' %(pin[0], pin[1])


def init_pins():
	global PIN_TABLE
	code=''
	for pin in sorted(sorted(PIN_TABLE, key=lambda i: i[0][0]), key=lambda i:i[0][1]):
		code+=pin[1]+'\n'
	return code


class OC1():
	ID=1
	CCMR = 1

class OC2():
	ID=2
	CCMR = 1

class OC3():
	ID=3
	CCMR = 2

class OC4():
	ID=4
	CCMR = 2


class TIMER_BASE():
	@classmethod
	def OC_Init(self, output_channels):
		code=''
		if not hasattr(output_channels, '__iter__'):
			output_channels=(output_channels,)
		for oc in output_channels:
			code +='''	/* Output compare %(oc)s mode and preload */
TIM%(id)s_CCMR%(ccmr)s |= TIM_CCMR%(ccmr)s_OC%(oc)sM_PWM1 | TIM_CCMR%(ccmr)s_OC%(oc)sPE;

/* Polarity and state */
//	TIM%(id)s_CCER |= TIM_CCER_CC%(oc)sP | TIM_CCER_CC%(oc)sE;		wrong polarity for stonerlights
TIM%(id)s_CCER |= TIM_CCER_CC%(oc)sE;''' % dict(
	id=self.ID,
	oc=oc.ID,
	ccmr=oc.CCMR)
		return code	


	@classmethod
	def PWM_Setup(self, period, output_channels):
		return '''
		TIM%(id)s_CR1 = TIM_CR1_CKD_CK_INT | TIM_CR1_CMS_EDGE;
		/* Period */
		TIM%(id)s_ARR = %(period)s;
		/* Prescaler */
		TIM%(id)s_PSC = 0;
		TIM%(id)s_EGR = TIM_EGR_UG;

		%(oc_init)s

		/* ARR reload enable */
		TIM%(id)s_CR1 |= TIM_CR1_ARPE;

		/* Counter enable */
		TIM%(id)s_CR1 |= TIM_CR1_CEN;''' % dict(
			id=self.ID,
			period=period,
			oc_init=self.OC_Init(output_channels))


class TIM1(TIMER_BASE):
	ID = 1
class TIM2(TIMER_BASE):
	ID = 2
class TIM3(TIMER_BASE):
	ID = 3
class TIM4(TIMER_BASE):
	ID = 4


def PWM_Setup(timer, period, output_channels):
	return timer.PWM_Setup(period, output_channels)

