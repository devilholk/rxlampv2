#encoding=utf-8

import time


#TODO - Iterera mera. Alltså, läs includes men outputta inget från dem!

#Notis: Exekreveringsvärlden kommer innehålla _internals som är kryptisk och lurig
#Den är bara till för fulhack, hjälpfunktioner kommer finnas för att enklare göra luriga saker



crange = lambda a:''.join([chr(v) for v in range(ord(a[0]), ord(a[1])+1)])

symbol = crange('az') + crange('az').upper() + '_'
number = crange('09')
ws = '\n\t '
nonsymbol = '*+^%&!~,=;|><:'
leftexpr='([{'
rightexpr=')]}'


global LAST_GUID
def GUID():
	LAST_GUID+=1
	return LAST_GUID




class token_scanner():
	def __init__(self, data):
		self.iter = iter(data)
		self.peekbuf=[]
		self.pos=0

	def _drain(self):
		try:
			val= self.iter.__next__()
			self.pos+=1
			return val
		except StopIteration:
			return None

	def peek(self, count=1):
		if len(self.peekbuf) >= count:
			return list(self.peekbuf[:count])
		else:
			for p in range(count - len(self.peekbuf)):		#More internal drain to fill up peekbuf
				self.peekbuf.append(self._drain())
			return list(self.peekbuf)

	def drain(self, count=1):

		if len(self.peekbuf) >= count:		#We have everything peeked, return it and remove from peekbuf
			val = list(self.peekbuf[:count])
			self.peekbuf=self.peekbuf[count:]
			return val
		else:								#We have some or nothing peeked, return that and append interal drain
			val = list(self.peekbuf)
			self.peekbuf=[]
			for p in range(count - len(val)):		#Drain remaining
				val.append(self._drain())
			return val

	def flush(self):
		self.peekbuf=[]


class scanner():
	def __init__(self, data):
		self.iter = iter(data)
		self.peekbuf=''
		self.row=0
		self.col=0

	def _drain(self):
		try:
			val= self.iter.__next__()
			if val == '\n':
				self.col=0
				self.row+=1
			else:
				self.col+=1

			return val
		except StopIteration:
			return ''

	def peek(self, count=1):
		if len(self.peekbuf) >= count:
			return self.peekbuf[:count]
		else:
			for p in range(count - len(self.peekbuf)):		#More internal drain to fill up peekbuf
				self.peekbuf+=self._drain()
			return self.peekbuf

	def drain(self, count=1):

		if len(self.peekbuf) >= count:		#We have everything peeked, return it and remove from peekbuf
			val = self.peekbuf[:count]
			self.peekbuf=self.peekbuf[count:]
			return val
		else:								#We have some or nothing peeked, return that and append interal drain
			val = self.peekbuf
			self.peekbuf=''
			for p in range(count - len(val)):		#Drain remaining
				val+=self._drain()

			return val

	def flush(self):
		self.peekbuf=''

class Token():
	class Symbol():
		pass
	class NonSymbol():
		pass
	class Whitespace():
		pass
	class String():
		pass
	class Char():
		pass
	class LeftExpr():
		pass
	class RightExpr():
		pass
	class Number():
		pass
	class Directive():
		pass
	class CommentML():
		pass
	class CommentSL():
		pass
	class Processed():
		pass


def get_line(scanner, keep_continuation_breaks=False):
	res = ''
	while True:
		byte = scanner.peek()
		if byte == '':
			return res

		if byte == '\n':			
			return res

		elif byte == '\\':				#Translate line continuation
			if scanner.peek(2) == '\\\n':
				if keep_continuation_breaks:
					res+='\n'
				scanner.flush()
			else:
				res+=scanner.drain()
		else:
			res+=scanner.drain()

def get_string(scanner):
	qoute = scanner.drain()	 #Remove initial qoutation mark
	res = qoute
	while True:
		byte = scanner.peek()
		if byte == '':
			return res

		if byte == qoute:			
			res+=scanner.drain()
			return res

		elif byte == '\\':				#Translate line continuation
			if scanner.peek(2) == '\\\n':
				scanner.flush()
			else:
				res+=scanner.drain()
		else:
			res+=scanner.drain()

def get_multiline_comment(scanner):
	res = ''
	while True:
		byte = scanner.peek()
		if byte == '':
			return res

		if byte == '*':
			if scanner.peek(2) == '*/':
				res+=scanner.drain(2)
				return res
			else:
				res+=scanner.drain()

		elif byte == '\\':				#Translate line continuation
			if scanner.peek(2) == '\\\n':
				scanner.flush()
				res+='\\\n'		#We keep these in comments
			else:
				res+=scanner.drain()

		else:
			res+=scanner.drain()

def get_contiguous_match(scanner, match):
	res=''	
	while True:
		byte = scanner.peek()
		if byte == '':
			return res

		if byte in match:
			res+=scanner.drain()
		elif byte == '\\':				#Translate line continuation
			if scanner.peek(2) == '\\\n':
				scanner.flush()
			elif byte in match:
				res+=scanner.drain()
			else:
				return res

		else:
			return res


def get_main_scope(scanner):
	tokens=[]
	while True:
		byte = scanner.peek()

		if byte == '':
			break
		elif byte in ws:
			tokens.append((scanner.row, scanner.col, Token.Whitespace, get_contiguous_match(scanner, ws)))

		elif byte in symbol:
			tokens.append((scanner.row, scanner.col, Token.Symbol, get_contiguous_match(scanner, symbol + number)))

		elif byte in nonsymbol:
			tokens.append((scanner.row, scanner.col, Token.NonSymbol, get_contiguous_match(scanner, nonsymbol)))

		elif byte == '"':
			tokens.append((scanner.row, scanner.col, Token.String, get_string(scanner)))

		elif byte == "'":
			tokens.append((scanner.row, scanner.col, Token.Char, get_string(scanner)))

		elif byte in leftexpr:
			tokens.append((scanner.row, scanner.col, Token.LeftExpr, scanner.drain()))

		elif byte in rightexpr:
			tokens.append((scanner.row, scanner.col, Token.RightExpr, scanner.drain()))

		elif byte in number:			
			tokens.append((scanner.row, scanner.col, Token.Number, get_contiguous_match(scanner, number+'.xbLeEfU')))

		elif byte in '.+-':
			#This may be a namespace separator or operator but it may also be the start of a number
			if scanner.peek(2)[1] in number:
				tokens.append((scanner.row, scanner.col, Token.Number, get_contiguous_match(scanner, number+'+-.xbLeEfU')))
			else:
				tokens.append((scanner.row, scanner.col, Token.NonSymbol, scanner.drain() + get_contiguous_match(scanner, nonsymbol)))


		elif byte=='#':			
			tokens.append((scanner.row, scanner.col, Token.Directive, get_line(scanner, keep_continuation_breaks=True)))

		elif byte=='/':
			if scanner.peek(2) == '//':
				tokens.append((scanner.row, scanner.col, Token.CommentSL, get_line(scanner)))
			elif scanner.peek(2) == '/*':
				tokens.append((scanner.row, scanner.col, Token.CommentML, get_multiline_comment(scanner)))
			else:				
				tokens.append((scanner.row, scanner.col, Token.NonSymbol, scanner.drain() + get_contiguous_match(scanner, nonsymbol)))


		else:
			print ("Current tokens:", tokens)
			raise Exception("Okänt: %s" % repr(byte))
			
	# for row, col, token, data in tokens:
	# 	print ("%10s %15s\t%s" % ('%i:%i' %(row,col),token.__name__,repr(data)))
	return tokens
import sys
with open(sys.argv[1], 'r', encoding='utf-8', errors='replace') as f:
	tokens = get_main_scope(scanner(f.read()))



funcs = {}
symbs=set()

world = {
	'_internals': (funcs, symbs),
}


#Senare skall vi outputta vilken rad det blir fel på, ge flaggor för att tillåta eller gnälla på dubbla funktioner etc

def encounters(scanner, match_tokens=[], ignore_tokens=[], match_data=None, match_all=False):
	searchpos=0
	while True:
		searchpos+=1
		data = scanner.peek(searchpos)[searchpos-1]
		if data == None:
			#print ("ingen träff2")
			return None
		row, col, token, data = data

		#Here we match against stuff
		if token in match_tokens:
			return searchpos-1

		if (match_data != None) and data == match_data:
			return searchpos-1

		if not token in ignore_tokens:
			if match_all:
				#print ("Matched ", data)
				return searchpos-1
			else:
				#print ("ingen träff")
				return None






scanner = token_scanner(tokens)
outdata=[]
read=None
while True:
	last=read 						#Keep track of last so we know if a symbol has a . in front of it (then it's a member symbol)
	data = scanner.drain()[0]
	read=data
	if data == None:
		break

#	time.sleep(.1)
#	print ("Hanterar token: ",data)
	row, col, token, data = data


	if token == Token.Directive:	#This code could be better, we may lose tabs and spaces now in constant string literals! BUG
		items = data[1:].split(' ',1)
		if len(items) == 2:
			directive, subdata = items
		else:
			directive, subdata = items[0], ''
		if directive == 'python':
			exec(subdata, world)
			data='//Python Executed: %s' % subdata.replace('\n', '\n//')
		elif directive == 'pyfunc':
			items = [v for v in subdata.replace('\t',' ').replace('\n', ' ').split(' ') if v]
			if len(items) == 1:
				func, expr = items * 2
			else:
				func = items[0]
				expr = ' '.join(items[1:])
			if func in funcs:
				raise Exception('Funktionen redan definierad!')
			
			funcs[func] = expr								
			data='//Python defined function: %s → %s' % (func.replace('\n', '\n//'), expr.replace('\n', '\n//'))

		elif directive == 'pysymb':
			items = [v for v in subdata.replace('\t',' ').replace('\n', ' ').split(' ') if v]
			if len(items) == 1:
				symb, expr = items * 2
			else:
				symb = items[0]
				expr = ' '.join(items[1:])
			if symb in symbs:
				raise Exception('Symbolen redan definierad!')
			
			symbs.add(symb)
			world[symb] = eval(expr, world)
			data='//Python defined symbol: %s → %s' % (func.replace('\n', '\n//'), expr.replace('\n', '\n//'))
		

		elif directive == 'pyexec':
			with open(subdata, 'rb') as f:
				exec(f.read(), world)
			data='//Python executed code in: %s' % subdata.replace('\n', '\n//')

		else:
			data= data.replace('\n','\\\n')	#Put back line continuation


	if token == Token.Symbol:
		match = encounters(scanner, ignore_tokens=[Token.Whitespace], match_all=True)
		if match != None:
			matchrow, matchcol, matchtoken, matchdata = scanner.peek(match+1)[match]
			if matchtoken == Token.LeftExpr and matchdata == '(':
				func = funcs.get(data)
				if func:
					scanner.drain(match+1)		#Drain out whitespaces and (

					args=''
					bal=1
					while True:
						item_row, item_col, item_token, item_data = scanner.drain()[0]

						if item_token==Token.RightExpr and item_data==')':
							bal-=1
							if bal:
								args+=')'
							else:
								break
						
						elif item_token==Token.LeftExpr and item_data=='(':
							args+='('
							bal+=1

						else:
							args+=item_data

					try:
						code="%s(%s)"% (func, args)
						data=str(eval(code, world) or '')
						token=Token.Processed

					except:
						print ("Code: %s"%code)
						raise

	if token == Token.Symbol:
		if last and last[3] != '.':
			if data in symbs:
				data = str('' if world[data] == None else world[data])
				token=Token.Processed

	outdata.append(data)

with open(sys.argv[2], 'w', encoding='utf-8') as out:
	out.write(''.join(outdata))

