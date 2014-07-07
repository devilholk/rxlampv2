#encoding=utf-8


LAST_GUID=0
def GUID():
	global LAST_GUID
	LAST_GUID+=1
	return LAST_GUID




class GPIO():
	class Pin():
		def __init__(self, port, name, bit,cname):
			self.port = port
			self.name = name
			self.bit = bit
			self.cname=cname


	class Mode():
		def __init__(self, mode):
			self.mode=mode
			self.speed='GPIO_Speed_50MHz'

class MODE():
	AF_OPEN_DRAIN = GPIO.Mode(mode='GPIO_Mode_AF_OD')
	OPEN_DRAIN = GPIO.Mode(mode='GPIO_Mode_Out_OD')
	IN_FLOATING = GPIO.Mode(mode='GPIO_Mode_IN_FLOATING')
	OUT_AF_PP = GPIO.Mode(mode='GPIO_Mode_AF_PP')
	OUT_PP = GPIO.Mode(mode='GPIO_Mode_Out_PP')
	ANALOG_IN = GPIO.Mode(mode='GPIO_Mode_AIN')


class PIN():
	pass


VirtualPins={}
Remaps=set([])

def SetupRemap(remap):
	Remaps.add(remap)
	return ''

class VPin():
	def __init__(self, name, pin, mode, value=None, inverted=False):
		self.name = name
		self.pin = pin
		self.mode = mode
		self.value = value
		self.inverted = inverted

	def electrical(self, override_value=None):
		if override_value != None:			
			return self.inverted != override_value
		else:
			return self.inverted != self.value

#Setup ports and pins
for port in 'ABC':
	for pin in range(16):
		setattr(PIN, 'P%s%i'%(port,pin), GPIO.Pin(port='GPIO%s'%port, name='P%s%i'%(port,pin), cname='GPIO_Pin_%i' % pin, bit=pin))

for port in 'D':
	for pin in range(2):
		setattr(PIN, 'P%s%i'%(port,pin), GPIO.Pin(port='GPIO%s'%port, name='P%s%i'%(port,pin), cname='GPIO_Pin_%i' % pin, bit=pin))


def SetPins(*pins):
	ports={}
	for p in pins:
		pin = VirtualPins[p]
		key=pin.pin.port
		port = ports.get(key)
		if port:
			port.add(pin)
		else:
			ports[key] = set([pin])

	res=''
	for port, pin in ports.items():
		set_pins = u'|'.join([v.pin.cname for v in pin if v.electrical(True)])
		clear_pins = u'|'.join([v.pin.cname for v in pin if not v.electrical(True)])
		res+='%s->BSRR=%s;\n' % (port, '|'.join(['(%s)%s'%(p, bs) for p, bs in ((set_pins, ''), (clear_pins, '<<16')) if p]))


	return res

def ClearPins(*pins):
	ports={}
	for p in pins:
		pin = VirtualPins[p]
		key=pin.pin.port
		port = ports.get(key)
		if port:
			port.add(pin)
		else:
			ports[key] = set([pin])

	res=''
	for port, pin in ports.items():

		set_pins = u'|'.join([v.pin.cname for v in pin if v.electrical(False)])
		clear_pins = u'|'.join([v.pin.cname for v in pin if not v.electrical(False)])

		res+='%s->BSRR=%s;\n' % (port, '|'.join(['(%s)%s'%(p, bs) for p, bs in ((set_pins, ''), (clear_pins, '<<16')) if p]))


	return res



def SetupPin(name, pin, mode, value=None, inverted=False, interrupt=None):
	VirtualPins[name] = VPin(name, pin, mode, value, inverted)
	return '//SetupPin called with data: %s' % repr((name, pin, mode, value, inverted))



def InitPins():
	#This can be lots improved but it works now
	ports={}
	for pin in VirtualPins.values():
		key=pin.pin.port, pin.mode.mode, pin.mode.speed
		port = ports.get(key)
		if port:
			port.add(pin)
		else:
			ports[key] = set([pin])


	deinits='\n\t'.join(['GPIO_DeInit(%s);'%p for p in set([pin.pin.port for pin in VirtualPins.values()])]) 
	remaps='\n\t'.join(['GPIO_PinRemapConfig(%s, ENABLE);'%r for r in Remaps])

	res='''GPIO_InitTypeDef GPIO_InitStructure;\n
	%s\n
	%s\n''' % (deinits, remaps)
	




	port_c='''	GPIO_InitStructure.GPIO_Pin = %(pinmask)s;
	GPIO_InitStructure.GPIO_Mode = %(mode)s;
	GPIO_InitStructure.GPIO_Speed = %(speed)s;
	GPIO_Init(%(portname)s, &GPIO_InitStructure);'''



	for (port, mode, speed), pin in ports.items():
		
		
		pinmask=u'|'.join([v.pin.cname for v in pin])
		set_pins = u'|'.join([v.pin.cname for v in pin if v.electrical()])
		clear_pins = u'|'.join([v.pin.cname for v in pin if not v.electrical()])

		if set_pins or clear_pins:
			res += '	%s->BSRR=%s;\n' % (port, '|'.join(['(%s)%s'%(p, bs) for p, bs in ((set_pins, ''), (clear_pins, '<<16')) if p]))

		res += port_c % dict(speed=speed, mode=mode, portname=port, pinmask=pinmask)


	
	return res


class EXTI():
	RISING = 'EXTI_Trigger_Rising'
	FALLING = 'EXTI_Trigger_Falling'

	@classmethod
	def Interrupt_from_pin(self, pin):
		if VirtualPins[pin].pin.bit > 15:
			raise Exception("Interruptet finns inte")
		elif VirtualPins[pin].pin.bit >= 10:
			return 'EXTI15_10_IRQHandler' 
		elif VirtualPins[pin].pin.bit >= 5:
			return 'EXTI9_5_IRQHandler' 
		else:
			return 'EXTI%i_IRQHandler' % VirtualPins[pin].pin.bit


	@classmethod
	def Interrupt_id_from_pin(self, pin):
		if VirtualPins[pin].pin.bit > 15:
			raise Exception("Interruptet finns inte")
		elif VirtualPins[pin].pin.bit >= 10:
			return 'EXTI15_10_IRQn' 
		elif VirtualPins[pin].pin.bit >= 5:
			return 'EXTI9_5_IRQn' 
		else:
			return 'EXTI%i_IRQn' % VirtualPins[pin].pin.bit


def ClearInterrupt(pin):
	return "EXTI_ClearFlag(EXTI_Line%(pin)s);" % dict(pin=VirtualPins[pin].pin.bit)

def EnableInterrupt(pin, trigger=EXTI.RISING,var=None):
#	print ("EnableInterrupt",pin, trigger, VirtualPins[pin].pin.bit)

	code = '''
			%(var)s.EXTI_Line = EXTI_Line%(pin_number)s;
			%(var)s.EXTI_Mode = EXTI_Mode_Interrupt;
			%(var)s.EXTI_Trigger = %(trigger)s;
			%(var)s.EXTI_LineCmd = ENABLE;
			EXTI_ClearFlag(%(var)s.EXTI_Line);
			EXTI_Init(&%(var)s);
			GPIO_EXTILineConfig(GPIO_PortSource%(port)s, %(pin_number)s);	//Pinne noll
			NVIC_EnableIRQ(%(interrupt)s);
	''' % dict(
		pin_number = VirtualPins[pin].pin.bit,
		port = VirtualPins[pin].pin.port,
		trigger = trigger,
		var=var or 'tmp%i' % GUID(),
		interrupt=EXTI.Interrupt_id_from_pin(pin),
	)
	return(code)


def DisableInterrupt(pin, clear=False):
	code = '''
	NVIC_DisableIRQ(%(interrupt)s);
	%(clear)s
	''' % dict(
		interrupt = EXTI.Interrupt_id_from_pin(pin),
		clear = ClearInterrupt(pin) if clear else ''
	)
	return(code)

def HookInterrupts(pins, code):

	res=''	
	for interrupt in set([EXTI.Interrupt_from_pin(pin) for pin in pins]):
		res+='''

void %(interrupt)s (void) {
	%(code)s
}''' % dict(
		code= code,
		interrupt = interrupt,
	)

	return res