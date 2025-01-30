from bfcompiler import *
from sys import argv

unary = ["!", "++", "--", ".", ",", "^", "->", "~", "*!"]
binary = ["?", "?*", "&", "|", "==", "!=", ">", "<", ">=", "<=", 
		"*", "/", "%", "+", "-", "@", "[", "="]
ternary = [">@", "]=", "!?"]
quaternary = [":"]
operators = unary + ternary + quaternary + binary
 
types = ["int", "char", "arr", "str", "func"]
valid_var = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"

def get_source():
	with open(argv[1], "r") as source:
		return "".join(source.readlines())

def lexer(source):
	# Remove Spaces and comments
	trimmed_source = ""
	i = -1
	while i + 1 < len(source):
		i += 1
		# Don't remove spaces or comments in string
		if source[i] == "\"" and source[i-1] != "\\":
			trimmed_source += "\""
			i += 1
			while source[i] != "\"" or source[i-1] == "\\":
				trimmed_source += source[i]
				i += 1
			trimmed_source += source[i]
			continue

		# Don't remove spaces or comments in characters
		if source[i] == "\'":
			trimmed_source += source[i:i+3]
			i += 2 
			continue

		# Don't remove spaces or comments in arrays
		if source[i] == "$":
			trimmed_source += "$"
			i += 1
			while source[i] != "$":
				trimmed_source += source[i]
				i += 1
			trimmed_source += source[i]
			continue		

		# Skip comments
		if source[i] == "#":
			i += 1
			while source[i] != "#":
				i += 1
			continue

		# Remove all other spaces
		if source[i].isspace():
			continue
		
		trimmed_source += source[i]
	source = trimmed_source
	# Seperate functions
	functions = [""]
	i = 0
	current_content = None
	while i < len(source):
		# Skip strings and characters
		if source[i] == "\"":
			if current_content == None:
				current_content = "str"
			elif current_content == "str":
				current_content = None
		if source[i] == "\'":
			if current_content == None:
				current_content = "char"
			elif current_content == "char":
				current_content = None
		if source[i] != "{" or current_content != None:
			functions[0] += source[i]
		else:
			index = len(functions)
			functions += [""]
			i += 1
			while source[i] != "}":
				functions[index] += source[i]
				i += 1
			functions[0] += "{" + str(index) + "}"
		i += 1
	
	# Seperate expressions
	expressions = []
	for f in functions:
		function_expressions = []
		expression = ""
		i = 0
		while i < len(f):
			if f[i] == ";":
				function_expressions += [expression]
				expression = ""
			else:
				expression += f[i]
			i += 1
		expressions += [function_expressions]
	
	# Split into tokens
	tokens = []
	for function in expressions:
		function_tokens = []
		for i in function:
			function_tokens += [tokenize(i)]
		tokens += [function_tokens]
	return tokens

def tokenize(expression):
	tokens = []
	i = 0 
	while i < len(expression):
		# Get types
		is_type = False
		for t in types:
			if expression[i:i+len(t)] == t and \
				expression[i:i+len(t)] not in valid_var:
				tokens += [("type", expression[i:i+len(t)])]
				i += len(t)
				is_type = True
				break
		if is_type:
			continue

		# Get operators of length 2
		if expression[i:i+2] in operators:
			tokens += [("op", expression[i:i+2])]
			i += 1

		# Get operators of length 1
		elif expression[i] in operators:
			tokens += [("op", expression[i])]

		# Get integers
		elif expression[i].isnumeric():
			integer = ""
			while i < len(expression) and \
				expression[i].isnumeric():
				integer += expression[i]
				i += 1
			i -= 1
			tokens += [("int", int(integer))]

		# Get characters
		elif expression[i] == "\'":
			tokens += [("char", expression[i+1])]
			i += 2

		# Get strings
		elif expression[i] == "\"" and expression[i-1] != "\\":
			string = ""
			i += 1
			while expression[i] != "\"" or expression[i-1] == "\\":
				string += expression[i]
				i += 1
			tokens += [("str", 
				string.encode().decode("unicode_escape"))]

		# Get arrays
		elif expression[i] == "$":
			array = ""
			i += 1
			while expression[i] != "$":
				array += expression[i]
				i += 1
			tokens += [("arr", 
				[int(item) for item in array.split(" ")])]

		# Get functions
		elif expression[i] == "{":
			tokens += [("func", int(expression[i+1]))]
			i += 2

		# Get variables
		elif expression[i] in valid_var:
			var = ""
			while i < len(expression) and \
				expression[i] in valid_var:
				var += expression[i]
				i += 1
			i -= 1
			tokens += [("var", var)]

		# Get parenthesis
		elif expression[i] == "(":
			content = ""
			count = 1
			while count != 0:
				i += 1
				if expression[i] == "(":
					count += 1
				if expression[i] == ")":
					count -= 1
				if count != 0:
					content += expression[i]
			tokens += [("exp", tokenize(content))]
		
		i += 1
	return tokens

def computation_tree(tokens):
	# Recursively compute trees of nested expressions
	i = 0
	while i < len(tokens):
		if tokens[i][0] == "exp":
			tokens[i] = computation_tree(tokens[i][1])
		i += 1
	for op in operators:
		i = 0
		while i < len(tokens):
			if tokens[i][1] == op:
				# Get opertors with different argc
				if op in unary:
					tokens[i:i+2] = [[tokens[i],
							 tokens[i+1]]]
				elif op in binary:
					tokens[i-1:i+2] = [[tokens[i],
						 tokens[i-1], tokens[i+1]]]
				elif op in ternary:
					tokens[i-3:i+2] = [[tokens[i],
				 tokens[i-3], tokens[i-1], tokens[i+1]]]
				elif op in quaternary:
					tokens[i-1:i+6] = [[tokens[i],
			tokens[i-1], tokens[i+1], tokens[i+3], tokens[i+5]]]
			i += 1
	return tokens[0]

cells = []
var_func = {}
DEBUG = False 

def eval_function(function, tokens, bf, params=[]):
	return_token = (None, None)
	for e in function:
		return_token = eval_expression(e, tokens, bf, params)
	return return_token

def eval_expression(expression, tokens, bf, params):
	global cells
	def get_type(cell):
		for var in cells:
			if cell == var[0] or cell == var[1]:
				return var[2]
	
	def get_func(func):
		if type(func) == int:
			return tokens[func]
		return tokens[var_func[func]]

	# NOP return expression
	if type(expression) == tuple:
		return expression

	# Recursively run expressions
	for i in range(1, len(expression)):
		if type(expression[i]) is list:
			expression[i] = \
				eval_expression(expression[i], tokens, 
							bf, params)

	# Run expressions depending on operator and argument types
	if DEBUG:
		print("[DEBUG]", expression)
	op = expression[0][1]
	argt = tuple([t[0] for t in expression[1:]])
	argv = tuple([t[1] for t in expression[1:]])
	if op == "@":
		if argt == ("type", "var"):
			if argv[0] == "int" or argv[0] == "char":
				defined = bf.def_(argv[1])
				cells += ((defined, argv[1], argv[0]),) 
				return "var", defined
			elif argv[0] == "arr" or argv[0] == "str" \
					or argv[0] == "func":
				cells += ((None, argv[1], argv[0]),)
				return "var", argv[1]
	elif op == ">@":
		if argt == ("type", "int", "var"):
			defined = bf.defArr(argv[2], argv[1])
			cells += ((defined, argv[2], argv[0]),)
			return "var", defined
	elif op == "->":
		if argt == ("var",):
			return eval_function(get_func(argv[0]), tokens, bf)
		elif argt == ("func",):
			return eval_function(tokens[argv[0]], tokens, bf)
	elif op == "~":
		if argt == ("int",):
			return params[argv[0]]
	elif op == "=":
		if argt == ("var", "var"):
			if get_type(argv[0]) in ("int", "char") and \
				get_type(argv[1]) in ("int", "char"):
				bf.setVar(argv[0], argv[1])
			elif get_type(argv[0]) in ("arr", "str") and \
				get_type(argv[1]) in ["arr", "str"]:
				if bf.get(argv[0]) == None:
					defined = bf.defArr(argv[0], bf.length(argv[1]))
					for cell in cells:
						if cell[1] == argv[0]:
							cells += ((defined, cell[1], 
								cell[2]),)
							del cell
							break
				bf.copyArr(argv[1], argv[0])
		elif argt == ("var", "int") or argt == ("var", "char"):
			return "var", bf.set(argv[0], argv[1])
		elif argt == ("var", "arr") or argt == ("var", "str"):
			if bf.get(argv[0]) == None:
				bf.defArr(argv[0], argv[1])
			bf.setArr(argv[0], argv[1])
		elif argt == ("var", "func"):
			var_func[argv[0]] = argv[1]
	elif op == "^":
		if argt == ("var",):	
			return "int", bf.length(argv[0])
		elif argt == ("arr",) or argt == ("str",):
			return "int", len(argv[0])	
	elif op == "[":
		pass
	elif op == "]=":
		pass
	elif op == "!":
		pass
	elif op == "&":
		pass
	elif op == "|":
		pass
	elif op == "*":
		if argt == ("var", "var"):
			cell = bf.mulVar(argv[0], argv[1])
			cells += ((cell, None, "int"),)
			return "var", cell
		elif argt == ("var", "int"):
			cell = bf.mul(argv[0], argv[1])
			cells += ((cell, None, "int"),)
			return "var", cell
		elif argt == ("int", "var"):
			cell = bf.mul(argv[1], argv[0])
			cells += ((cell, None, "int"),)
			return "var", cell
		elif argt == ("int", "int"):
			return "int", argv[0] * argv[1]	
	elif op == "/":
		if argt == ("var", "var"):
			cell = bf.divModVar(argv[0], argv[1])
			cells += ((cell[0], None, "int"),)
			return "var", cell[0]
		elif argt == ("var", "int"):
			cell = bf.divModl(argv[0], argv[1])
			cells += ((cell[0], None, "int"),)
			return "var", cell[0]
		elif argt == ("int", "var"):
			cell = bf.divModr(argv[0], argv[1])
			cells += ((cell[0], None, "int"),)
			return "var", cell[0]
		elif argt == ("int", "int"):
			return "int", argv[0] // argv[1]
	elif op == "%":
		if argt == ("var", "var"):
			cell = bf.divModVar(argv[0], argv[1])
			cells += ((cell[1], None, "int"),)
			return "var", cell[1]
		elif argt == ("var", "int"):
			cell = bf.divModl(argv[0], argv[1])
			cells += ((cell[1], None, "int"),)
			return "var", cell[1]
		elif argt == ("int", "var"):
			cell = bf.divModr(argv[0], argv[1])
			cells += ((cell[1], None, "int"),)
			return "var", cell[1]
		elif argt == ("int", "int"):
			return "int", argv[0] % argv[1]

	elif op == "+":
		if argt == ("var", "var"):
			cell = bf.addVar(argv[0], argv[1])
			cells += ((cell, None, "int"),)
			return "var", cell
		elif argt == ("var", "int"):
			cell = bf.add(argv[0], argv[1])
			cells += ((cell, None, "int"),)
			return "var", cell
		elif argt == ("int", "var"):
			cell = bf.add(argv[1], argv[0])
			cells += ((cell, None, "int"),)
			return "var", cell
		elif argt == ("int", "int"):
			return "int", argv[0] + argv[1]	
	elif op == "-":
		if argt == ("var", "var"):
			cell = bf.subVar(argv[0], argv[1])
			cells += ((cell, None, "int"),)
			return "var", cell
		elif argt == ("var", "int"):
			cell = bf.subl(argv[0], argv[1])
			cells += ((cell, None, "int"),)
			return "var", cell
		elif argt == ("int", "var"):
			cell = bf.subr(argv[0], argv[1])
			cells += ((cell, None, "int"),)
			return "var", cell
		elif argt == ("int", "int"):
			return "int", argv[0] - argv[1]
	elif op == "++":
		if argt == ("var",):
			bf.inc(argv[0])
			return "var", argv[0]	
		elif argt == ("int",):
			return "int", argv[0] + 1;
	elif op == "--":
		if argt == ("var",):
			bf.dec(argv[0])
			return "var", argv[0]	
		elif argt == ("int",):
			return "int", argv[0] - 1;

	elif op == "==":
		pass
	elif op == "!=":
		pass
	elif op == ">":
		pass
	elif op == ">=":
		if argt == ("var", "var"):
			cell = bf.gtEqVar(argv[0], argv[1])
			cells += ((cell, None, "int"),)
			return "var", cell
		# TODO
	elif op == "<":
		pass
	elif op == "<=":
		pass
	elif op == ".":
		if argt == ("var",):
			if get_type(argv[0]) == "char":
				bf.print(argv[0])
			elif get_type(argv[0]) == "str":
				bf.printArr(argv[0])
			elif get_type(argv[0]) == "int":
				bf.printArr(bf.toArr(argv[0]))
			elif get_type(argv[0]) == "arr":
				bf.foreach(argv[0], 
				lambda param:
			(bf.printArr(bf.toArr(param)), bf.printStr(" ")))
			elif get_type(argv[0]) == "func":
				bf.printStr(f"func: {argv[0]} at " \
					+ f"{var_func[argv[0]]}")
		elif argt == ("str",) or argt == ("char",):
			bf.printStr(argv[0])	
		elif argt == ("int",):
			bf.printStr(str(argv[0]))
		elif argt == ("arr",):
			bf.printStr("$ " + \
			" ".join([str(i) for i in argv[0]]) + " $")
		else:
			bf.printStr(f"{argt[0]}: {argv[0]}")
	elif op == ",":
		if argt == ("type",):
			if argv[0] == "char":
				cell = bf.input()
				cells += ((cell, None, "char"),)
				return "var", cell
			elif argv[0] == "int":
				cell = bf.toInt(bf.inputArr())
				cells += ((cell, None, "int"),)
				return "var", cell
		elif argt == ("var",):
			if get_type(argv[0]) == "char":
				cell = bf.input()
				cells += ((cell, None, "char"),)
				return "var", cell
			elif get_type(argv[0]) == "int":
				cell = bf.toInt(bf.inputArr())
				cells += ((cell, None, "int"),)
				return "var", cell
			elif get_type(argv[0]) == "str":
				cell = bf.inputArr(len_=bf.length(argv[0]))
				cells += ((cell, None, "str"),)
				return "var", cell
			elif get_type(argv[0]) == "arr":
				cell = bf.malloc(bf.length(argv[0]))
				def do(param):
					bf.setVar(param, bf.toInt(bf.inputArr()))
				bf.foreach(cell, do)
				cells += ((cell, None, "arr"),)
				return "var", cell
	elif op == "?":
		pass
	elif op == "!?":
		pass
	elif op == "?*":
		if argt == ("func", "func"):
			def cond():
				return eval_function(get_func(argv[0]), tokens, bf, 
					params=params)[1]
			def do():
				eval_function(get_func(argv[1]), tokens, bf, 
					params=params)
			bf.while_(cond, do)
	elif op == ":":
		if argt == ("func", "func", "func", "func"):
			def start(param):
				cells += [param, None, "int"]
				eval_function(get_func(argv[0]), tokens, bf, 
					params=[("var", param)] + params)
			def cond(param):
				return eval_function(get_func(argv[1]), tokens, bf, 
					params=[("var", param)] + params)[1]
				
			def step(param):
				eval_function(get_func(argv[2]), tokens, bf, 
					params=[("var", param)] + params)
			def do(param):			
				eval_function(get_func(argv[3]), tokens, bf, 
					params=[("var", param)] + params)
			bf.for_(start, cond, step, do)
	
	elif op == "*!":
		if argt == ("func",):
			def do():
				eval_function(get_func(argv[0]), tokens, bf, 
					params=params)
			bf.forever(do)	
	return "None", "None"
		

def compile():
	tokens = lexer(get_source())
	for f in range(len(tokens)):
		for e in range(len(tokens[f])):
			tokens[f][e] = computation_tree(tokens[f][e])
	bf = bf_compiler()
	result = eval_function(tokens[0], tokens, bf, params=[("str", argv[1])])
	if DEBUG:
		print("[DEBUG] Return:", result, "\n[DEBUG] Variable List:", cells)
	bf.result(argv[1][argv[1].find("/")+1:argv[1].find(".")], trimmed=not DEBUG)

compile()	
