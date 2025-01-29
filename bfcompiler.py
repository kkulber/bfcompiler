class bf_compiler:
	def __init__(self):
		self.code = ""
		self.pointer = 0
		self.vars = {}
		self.used_mem = 0
		self.used_temp = 0

	def result(self, filename, trimmed=True):
		if trimmed:
			self.trim()
		print("Program compiled successfully!\n" + 
			f"Generated brainf*ck program has a length of {len(self.code)} instructions.")
		file = open(f"generated/{filename}.bf", "w")
		file.write(self.code)
		file.close()
		print(f"Saved to generated/{filename}.bf")
		return self.code

	def trim(self):
		# Remove leading pointer moves
		i = 0
		while i < len(self.code):
			if self.code[i] not in "<>":
				self.code = self.code[i:]
				break
			i += 1

		# Remove redundant code after last input/ouput
		find = max(self.code.rfind("."), self.code.rfind(","))
		if find == -1:
			self.code = ""
			return

		i = 0
		depth = 0
		while i < len(self.code):
			if i >= find and depth == 0:
				self.code = self.code[:i+1]
				break
			if self.code[i] == "[":
				depth += 1
			elif self.code[i] == "]":
				depth -= 1
			i += 1

		# Remove unenterable brackets
		while self.code.find("][") != -1:
			i = self.code.find("][") + 2
			depth = 1
			while depth != 0:
				if self.code[i] == "[":
					depth += 1
				elif self.code[i] == "]":
					depth -= 1
				i += 1
			self.code = self.code[:self.code.find("][")+1] + self.code[i:]

		# Remove Operations that undo themselves
			for seq in "+-", "-+", "<>", "><":
				while self.code.find(seq) != -1:
					self.code = self.code.replace(seq, "") 


	def algorithm(self, filename):
		file = open(f"algorithms/{filename}.bf", "r")
		self.code += file.readlines()[0].strip()
		file.close()


	# Variable Access

	def get(self, var):
		if type(var) != str:
			return var
		if var not in self.vars:
			return None
		return self.vars[var]
	
	def get_name(self, var):
		try:
			return list(self.vars.keys())[list(self.vars.values()).index(var)]
		except:
			return None

	def index(self, arr, index):
		if type(arr) != str:
			return arr[index]
		return self.vars[arr][index]

	def length(self, arr):
		if type(arr) != str:
			return len(arr)
		return len(self.vars[arr])


	# Memory Allocation

	def def_(self, name, value=0):
		if type(value) == bool:
			value = int(value)
		if type(value) == str:
		    	value = ord(value)
		free = self.used_mem
		self.vars[name] = free
		self.used_mem += 1
		if value != 0:
		    self.set(free, value, reset=False)
		return free

	def defVar(self, name, cell):
		free = self.used_mem
		self.vars[name] = free
		self.used_mem += 1
		self.setVar(free, cell, reset=False)
		return free

	def defArr(self, name, values):
		if type(values) == str:
		      values = list(values)
		if type(values) == int:
			values = values*(0,)
		free = tuple(range(self.used_mem, self.used_mem + len(values)))
		self.used_mem += len(values)
		self.vars[name] = free
		for i in range(len(values)):
			if values[i] != 0:
		     		self.set(free[i], values[i], reset=False)
		return free

	def defArrVar(self, name, arr):
		free = tuple(range(self.used_mem, self.used_mem + self.length(arr)))
		self.used_mem += self.length(arr)
		self.vars[name] = free
		self.copyArr(arr, free, reset=False)
		return free

	def malloc(self, len_=None):
		if len_ == None:
			free = -(self.used_temp + 1)
			len_ = 1
		else:
			free = tuple(range(-(self.used_temp + 1), -(self.used_temp + 1 + len_), -1))
		self.used_temp += len_
		return free

	def free(self, num=1, reset=False):
		if reset:
			for cell in range(-self.used_temp, -self.used_temp + num):
				self.reset(cell)
		self.used_temp -= num

	def clean(self, preserve=0):
		for cell in range(-self.used_temp, -preserve):
			self.reset(cell)
		self.used_temp = 0

	def saveMemState(self):
		return self.used_temp

	def loadMemState(self, memState):
		self.free(self.used_temp - memState, reset=True)


	# Cell Management

	def goto(self, cell):
		if type(cell) == str:
			cell = self.vars[cell]
		diff = cell - self.pointer
		self.pointer = cell
		if diff > 0:
			self.code += abs(diff) * ">"
		else:
			self.code += abs(diff) * "<"
		return cell

	def reset(self, cell):
		self.goto(cell)
		self.code += "[-]"
		return cell

	def set(self, cell, value, reset=True):
		if type(value) == str:
			value = ord(value)
		self.goto(cell)
		if reset:
			self.reset(cell)
		if value < 128:
			self.code += value * "+"
		else:
			self.code += (256 - value) * "-"
		return cell

	def move(self, from_, to, reset=True):
		if reset:
			self.reset(to)
		self.goto(from_)
		self.code += "[-"
		self.inc(to)
		self.goto(from_)
		self.code += "]"
		return to

	def setVar(self, to, from_, reset=True):
		if reset:
			self.reset(to)
		temp = self.malloc()
		self.goto(from_)
		self.code += "[-"
		self.inc(to)
		self.inc(temp)
		self.goto(from_)
		self.code += "]"
		self.move(temp, from_, reset=False)
		self.free()
		return to

	def inc(self, cell, value=1):
		self.goto(cell)
		self.code += value * "+"
		return cell

	def dec(self, cell, value=1):
		self.goto(cell)
		self.code += value * "-"
		return cell

	def change(self, cell, value):
		self.goto(cell)
		if value > 0:
			self.inc(cell, value)
		else:
			self.dec(cell, -value)
		return cell


	# Arithmetic
	def add(self, cell, value):
		result = self.malloc()
		self.setVar(result, cell, reset=False)
		if value > 0:
			self.inc(result, value)
		else:
			self.dec(result, -value)
		return result

	def addVar(self, cell1, cell2):
		result = self.malloc()
		self.setVar(result, cell1, reset=False)
		self.setVar(result, cell2, reset=False)
		return result

	def sub(self, cell, value):
		result = self.malloc()
		self.setVar(result, cell, reset=False)
		if value > 0:
			self.dec(result, value)
		else:
			self.inc(result, -value)
		return result

	def subVar(self, cell1, cell2):
		result, temp = self.malloc(2)
		self.setVar(result, cell1, reset=False)
		self.setVar(temp, cell2, reset=False)
		self.goto(temp)
		self.algorithm("subVar")
		self.free()
		return result

	def mul(self, cell, value):
		result, temp = self.malloc(2)
		self.set(temp, value, reset=False)
		self.move(self.mulVar(cell, temp), result)
		self.free(2, reset=True)
		return result

	def mulVar(self, cell1, cell2):
		result, temp1, temp2 = self.malloc(3)
		self.setVar(temp1, cell1, reset=False)
		self.setVar(temp2, cell2, reset=False)
		self.goto(temp1)
		self.algorithm("mulVar")
		self.pointer = temp2
		self.free(2)
		return result

	def divMod(self, cell, value):
		div, mod = self.malloc(2)
		self.setVar(mod, cell, reset=False)
		self.while_(lambda: self.or_(self.gt(mod, value), self.eq(mod, value)),
			lambda: (self.dec(mod, value), self.inc(div, 1)))
		return div, mod

	def divModVar(self, cell1, cell2):
		div, mod, temp = self.malloc(3)
		self.setVar(mod, cell1, reset=False)
		self.setVar(temp, cell2, reset=False)
		self.while_(lambda: self.or_(self.gtVar(mod, temp), self.eqVar(mod, temp)),
			lambda: (self.setVar(mod, self.subVar(mod, temp)), self.inc(div)))
		self.free(reset=True)
		return div, mod
	

	# Logic

	def not_(self, cell):
		result, temp = self.malloc(2)
		self.setVar(result, cell, reset=False)
		self.goto(temp)
		self.algorithm("not")
		self.free()
		return result

	def and_(self, cell1, cell2):
		result, temp1, temp2 = self.malloc(3)
		self.setVar(temp1, cell1)
		self.setVar(temp2, cell2)
		self.goto(temp1)
		self.algorithm("and")
		self.pointer = temp2
		self.free(2)
		return result

	def or_(self, cell1, cell2):
		result, temp1, temp2 = self.malloc(3)
		self.setVar(temp1, cell1)
		self.setVar(temp2, cell2)
		self.goto(temp1)
		self.algorithm("or")
		self.pointer = temp2
		self.free(2)
		return result


	# Comparison

	def neq(self, cell, value):
		if type(value) == str:
			value = ord(value)
		result, temp = self.malloc(2)
		self.setVar(temp, cell, reset=False)
		self.dec(temp, value)
		self.goto(temp)
		self.algorithm("neq")
		self.free()
		return result

	def neqVar(self, cell1, cell2):
		result, temp1, temp2 = self.malloc(3)
		self.setVar(temp1, cell1, reset=False)
		self.setVar(temp2, cell2, reset=False)
		self.goto(temp1)
		self.algorithm("neqVar")
		self.pointer = temp2
		self.free(2)
		return result

	def eq(self, cell, value):
		if type(value) == str:
			value = ord(value)
		result, temp = self.malloc(2)
		self.setVar(temp, cell, reset=False)
		self.dec(temp, value)
		self.goto(temp)
		self.algorithm("eq")
		self.free()
		return result

	def eqVar(self, cell1, cell2):
		result, temp = self.malloc(2)
		self.setVar(result, cell1)
		self.setVar(temp, cell2)
		self.goto(result)
		self.algorithm("eqVar")
		self.pointer = temp
		self.free()
		return result

	def gt(self, cell, value):
		if type(value) == str:
			value = ord(value)
		result, temp = self.malloc(2)
		self.set(temp, value, reset=False)
		self.move(self.gtVar(cell, temp), result)
		self.free()
		self.free(reset=True)
		return result

	def gtVar(self, cell1, cell2):
		result, temp1, temp2, temp3, temp4 = self.malloc(5)
		self.setVar(temp1, cell1, reset=False)
		self.setVar(temp2, cell2, reset=False)
		self.goto(temp1)
		self.algorithm("gt")
		self.pointer = temp2 
		self.free(4)
		return result

	def gtEq(self, cell, value):
		pass

	def gtEqVar(self, cell1, cell2):
		result = self.malloc()
		def edge():
			self.set(result, 1)
		def default():
			self.move(self.gtVar(self.add(cell1, 1), cell2), result)
			self.free()
			self.free(reset=True)
		self.ifelse(self.and_(self.eq(cell1, 255), self.eq(cell2, 255)), edge, default)
		return result		
	
	def lt(self, cell, value):
		pass
				
	def ltVar(self, cell1, cell2):
		pass
	
	def ltEq(self, cell, value):
		pass
						
	def ltEq(self, cell1, cell2):
		pass

# Control Flow

	def if_(self, cell, do):
		temp = self.malloc()
		self.setVar(temp, cell, reset=False)
		self.goto(temp)
		self.code += "["
		memState = self.saveMemState()
		do()
		self.loadMemState(memState)
		self.reset(temp)
		self.code += "]"
		self.free()

	def ifelse(self, cell, ifDo, elseDo):
		temp1, temp2 = self.malloc(2)
		self.setVar(temp1, cell, reset=False)
		self.inc(temp2)
		self.goto(temp1)
		self.code += "["
		memState = self.saveMemState()
		ifDo()
		self.loadMemState(memState)
		self.dec(temp2)
		self.reset(temp1)
		self.code += "]"
		self.goto(temp2)
		self.code += "["
		memState = self.saveMemState()
		elseDo()
		self.loadMemState(memState)
		self.reset(temp2)
		self.code += "]"
		self.free(2)
	
	def while_(self, cond, do):
		temp = self.malloc()
		memState = self.saveMemState()
		self.setVar(temp, cond())
		self.loadMemState(memState)
		self.goto(temp)
		self.code += "["
		do()
		self.loadMemState(memState)
		self.setVar(temp, cond())
		self.loadMemState(memState)
		self.goto(temp)
		self.code += "]"
		self.free()

	def for_(self, start, cond, step, do):
		cell, temp = self.malloc(2)
		start(param=cell)
		memState = self.saveMemState()
		self.setVar(temp, cond(param=cell))
		self.loadMemState(memState)
		self.goto(temp)
		self.code += "["
		do(param=cell)
		step(param=cell)
		self.loadMemState(memState)
		self.setVar(temp, cond(param=cell))
		self.loadMemState(memState)
		self.goto(temp)
		self.code += "]"
		self.free()
		self.free(reset=True)

	def forever(self, do):
		temp = self.malloc()
		self.set(temp, True, reset=False)
		self.goto(temp)
		self.code += "["
		memState = self.saveMemState()
		do()
		self.loadMemState(memState)
		self.goto(temp)
		self.code += "]"
		self.free()

	def foreach(self, arr, do):
		memState = self.saveMemState()
		for cell in self.get(arr):
			do(param=cell)
			self.loadMemState(memState)

	# IO

	def print(self, cell):
		self.goto(cell)
		self.code += "."
		return cell

	def printStr(self, string):
		temp = self.malloc()
		lastchar = 0
		for char in string:
			diff = ord(char) - lastchar
			lastchar = ord(char)
			self.change(temp, diff)
			self.print(temp)
		self.free(reset=True)

	def printArr(self, arr):
		for cell in self.get(arr):
			self.goto(cell)
			self.print(cell)
		return arr

	def input(self, single=True):
		result, newline = self.malloc(2)
		self.goto(result)
		self.code += ","
		self.goto(newline)
		self.code += ","
		self.free(reset=True)
		return result

	def inputArr(self, len_=3):
		result = self.malloc(len_)
		temp, newline = self.malloc(2)
		self.set(temp, 1)
		def do(param):
			def take_input():
				self.goto(param)
				self.code += ","
			self.if_(temp, take_input)
			self.if_(self.eq(param, "\n"), lambda: (self.reset(temp),
				  self.reset(param)))
		self.foreach(result, do)
		def catch_newline():
			self.goto(newline)
			self.code += ","
		self.if_(temp, catch_newline)
		self.free(2, reset=True)
		return result
	
	# Arrays

	def resetArr(self, arr):
		for cell in self.get(arr):
			self.reset(cell)
		return arr

	def setArr(self, arr, values):
		for i, value in enumerate(values):
			self.set(self.index(arr, i), value)
		return arr

	def moveArr(self, arr1, arr2, reset=True):
		for i in range(self.length(arr2)):
			self.move(self.index(arr1, i), self.index(arr2, i), reset=reset)
		return arr2

	def copyArr(self, arr1, arr2, reset=True):
		for i in range(self.length(arr2)):
			self.setVar(self.index(arr2, i), self.index(arr1, i), reset=reset)
		return arr2

	def getIndex(self, arr, index):
		result, temp0, temp1, temp2 = self.malloc(4)
		tempArr = self.malloc(self.length(arr))
		self.setVar(temp0, index, reset=False)
		self.setVar(temp1, temp0, reset=False)
		self.copyArr(arr, tempArr, reset=False)
		self.goto(temp0)
		self.algorithm("indexGet")
		self.pointer = temp2
		self.resetArr(tempArr)
		self.free(self.length(arr) + 3)
		return result

	def setIndex(self, arr, index, value):
		temp = self.malloc()
		self.set(temp, value)
		self.setIndexVar(arr, index, temp)
		self.free(reset=True)
		return arr 

	def setIndexVar(self, arr, index, data):
		temp0, temp1, temp2, temp3 = self.malloc(4)
		tempArr = self.malloc(self.length(arr))
		self.setVar(temp1, index)
		self.setVar(temp2, temp1)
		self.setVar(temp3, data)
		self.moveArr(arr, tempArr)
		self.goto(temp1)
		self.algorithm("indexSet")
		self.pointer = temp2
		self.moveArr(tempArr, arr)
		self.free(self.length(arr) + 4)
		return arr

	def concat(self, arr1, arr2):
		result = self.malloc(self.length(arr1) + self.length(arr2))
		self.copyArr(arr1, result[:self.length(arr1)], reset=False)
		self.copyArr(arr2, result[self.length(arr1):], reset=False)
		return result

	def concatStr(self, arr, string):
		pass

	# Datatype Conversion

	def toBool(self, cell):
		result, temp = self.malloc(2)
		self.setVar(temp, cell, reset=False)
		self.goto(temp)
		self.algorithm("toBool")
		self.free()
		return result

	def toInt(self, arr):
		temp = self.malloc(3)
		result = self.index(temp, 2)
		self.copyArr(arr, temp)
		self.dec(self.index(temp, 0), ord("0"))
		def one_digit_parsing():
			self.move(self.index(temp, 0), result)
		def two_digit_parsing():
			self.move(self.index(temp, 1), result, reset=False)
			self.move(self.mul(self.index(temp, 0), 10), result, reset=False)
			self.free()
		def three_digit_parsing():
			self.dec(self.index(temp, 2), ord("0"))
			self.move(self.mul(self.index(temp, 1), 10), result, reset=False)
			self.move(self.mul(self.index(temp, 0), 100), result, reset=False)
			self.reset(self.index(temp, 1))
			self.free(2)
		self.ifelse(self.not_(self.index(temp, 1)), one_digit_parsing,
			lambda: (self.dec(self.index(temp, 1), ord("0")),
				self.ifelse(self.not_(self.index(temp, 2)),
					two_digit_parsing, three_digit_parsing)))
		self.free(reset=True)
		self.move(result, self.index(temp, 0))
		result = self.index(temp, 0)
		self.free(2)
		return result
	
	def toDigit(self, cell):
		return self.sub(cell, ord("0"))

	def toArr(self, cell):
		result = self.malloc(3)
		temp = self.index(result, 2)
		self.setVar(temp, cell)
		self.while_(lambda: self.or_(self.gt(temp, 100), self.eq(temp, 100)),
			lambda: (self.dec(temp, 100), self.inc(self.index(result, 0))))
		self.while_(lambda: self.or_(self.gt(temp, 10), self.eq(temp, 10)),
			lambda: (self.dec(temp, 10), self.inc(self.index(result, 1))))
		self.ifelse(self.index(result, 0),
			lambda: (self.inc(self.index(result, 0), ord("0")),
				self.inc(self.index(result, 1), ord("0"))),
			lambda: self.if_(self.index(result, 1),
				lambda: self.inc(self.index(result, 1), ord("0"))))
		self.inc(self.index(result, 2), ord("0"))
		return result

	def toChr(self, cell):
		return self.add(cell, ord("0"))
