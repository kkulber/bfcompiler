from bfcompiler import *
from sys import argv

unary = ["!", "++", "--", ".", ",", "->", "<-", "*!"]
binary = ["?", "?*", "&", "|", "==", "!=", ">", "<", ">=", "<=", 
		"*", "/", "%", "+", "-", "@", "@>", "[", "="]
ternary = [">@", "]=", "!?", "=*"]
quaternary = [":"]
operators = unary + ternary + quaternary + binary
 
types = ["int", "char", "arr", "str", "func"]
valid_var = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"

def get_source():
	if len(argv) != 2:
		raise Exception("No source file provided.")
	with open(argv[1], "r") as source:
		return "\n".join(source.readlines())

def lexer(source):
	# Remove Spaces and comments
	trimmed_source = ""
	i = -1
	while i + 1 < len(source):
		i += 1
		# Skip comments
		if source[i] == "#":
			i += 1
			while source[i] != "#":
				i += 1
			continue
		# Don't remove spaces in string
		if source[i] == "\"":
			trimmed_source += "\""
			i += 1
			while source[i] != "\"":
				trimmed_source += source[i]
				i += 1
			trimmed_source += source[i]
			continue
		# Don't remove spaces in arrays
		if source[i] == "$":
			trimmed_source += "$"
			i += 1
			while source[i] != "$":
				trimmed_source += source[i]
				i += 1
			trimmed_source += source[i]
			continue
		# Remove all other spaces
		if source[i].isspace():
			continue
		trimmed_source += source[i]
	source = trimmed_source

	# Seperate functions
	functions = [""]
	i = 0
	while i < len(source):
		if source[i] != "{":
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
	i = -1
	while i + 1 < len(expression):
		i += 1

		# Get operators of length 2
		if expression[i:i+2] in operators:
			tokens += [("op", expression[i:i+2])]
			i += 1
			continue

		# Get operators of length 1
		if expression[i] in operators:
			tokens += [("op", expression[i])]
			continue

		# Get types
		is_type = False
		for t in types:
			if expression[i:i+len(t)] == t and \
				expression[i+len(t)] not in valid_var:
				tokens += [("type", expression[i:i+len(t)])]
				i += len(t)-1
				is_type = True
				break
		if is_type:
			continue

		# Get integers
		if expression[i].isnumeric():
			integer = ""
			while i < len(expression) and \
				expression[i].isnumeric():
				integer += expression[i]
				i += 1
			i -= 1
			tokens += [("int", int(integer))]
			continue

		# Get characters
		if expression[i] == "\'":
			tokens += [("char", expression[i+1])]
			i += 2
			continue

		# Get strings
		if expression[i] == "\"":
			string = ""
			i += 1
			while expression[i] != "\"":
				string += expression[i]
				i += 1
			tokens += [("str", string)]
			continue

		# Get arrays
		if expression[i] == "$":
			array = ""
			i += 1
			while expression[i] != "$":
				array += expression[i]
				i += 1
			tokens += [("arr", 
				[int(item) for item in array.split(" ")])]
			continue

		# Get functions
		if expression[i] == "{":
			tokens += [("func", expression[i+1])]
			i += 2
			continue

		# Get variables
		if expression[i] in valid_var:
			var = ""
			while i < len(expression) and \
				expression[i] in valid_var:
				var += expression[i]
				i += 1
			i -= 1
			tokens += [("var", var)]
			continue

		# Get parenthesis
		if expression[i] == "(":
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
			continue
	return tokens

def computation_tree(tokens):
	i = 0
	while i < len(tokens):
		if tokens[i][0] == "exp":
			tokens[i] = computation_tree(tokens[i][1])
		i += 1
	for op in operators:
		i = 0
		while i < len(tokens):
			if tokens[i][1] == op:
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

def compile():
	tokens = lexer(get_source())
	for f in range(len(tokens)):
		for e in range(len(tokens[f])):
			tokens[f][e] = computation_tree(tokens[f][e])	
	return tokens		
		
