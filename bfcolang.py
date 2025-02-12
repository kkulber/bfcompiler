from bfcompiler import *
from sys import argv

unary = ["->", "~", "^", ".", ",", "!", "++", "--", "*!"]
binary = ["[", "*", "/", "%", "+", "-", ">", "<", ">=", "<=", "==", "!=",
         "&", "|", "=", "@=", "@", "@>", "?", "?*", "[*"]
ternary = ["]=", ">@", "!?"]
ternary_cut = {"]=": "[", ">@": "<", "!?": "?"}
quaternary = [":"]
operators  = unary + binary + ternary + quaternary

op_order = ("->", "~", "^", "[", "]="), ("!", ".", ",", "++", "--"), \
    ("*", "/", "%"), ("+", "-"), (">", "<", ">=", "<=", "==", "!="), \
    ("&",), ("|",), ("=", "@=", "@", "@>", ">@"), ("?", "!?", "?*", "*!", "[*", ":")     

types = ["int", "char", "arr", "str", "func"]
valid_var = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"

def get_source():
    with open(argv[1], "r") as source:
        return "".join(source.readlines())

def preprocessor(source):
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
    def save_function(functions, i, parent_index):
        func_index = len(functions)
        functions += [""]
        i += 1
        while source[i] != "}":
            if source[i] == "{":
                i = save_function(functions, i, func_index)
            functions[func_index] += source[i]
            i += 1
        functions[parent_index] += "{" + str(func_index) + "}"
        return i    
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
            i = save_function(functions, i, 0)
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
            function_tokens += [lexer(i)]
        tokens += [function_tokens]
    return tokens

def lexer(expression):
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
            func_index = ""
            i += 1
            while expression[i] != "}":
                func_index += expression[i]
                i += 1
            tokens += [("func", int(func_index))]

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
            tokens += [lexer(content)]
        
        i += 1
    return tokens

def AST(tokens):
    # Compute subexpressions
    i = 0
    while i < len(tokens):
        if type(tokens[i]) == list:
            tokens[i] = AST(tokens[i])
        i += 1

    # Cut quaternary fill operators
    i = 0
    while i < len(tokens) - 5:
        if tokens[i][0] == "op" and tokens[i][1] in quaternary \
                and tokens[i+2][0] == "op" and tokens[i+2][1] == tokens[i][1] \
                and tokens[i+4][0] == "op" and tokens[i+4][1] == tokens[i][1]:
            del tokens[i+2], tokens[i+3]
        i += 1

    # Cut ternary fill operators
    i = 0
    while i < len(tokens):
        if tokens[i][0] == "op" and tokens[i][1] in ternary:
            j = 0
            while tokens[j][0] != "op" or tokens[j][1] != ternary_cut[tokens[i][1]]:
                j -= 1
            del tokens[j]
            i -= 1
        i += 1

    # Group tokens based on presedence fields
    for field in op_order:
        i = 0
        while i < len(tokens):
            if tokens[i][0] == "op" and tokens[i][1] in field:
                if tokens[i][1] in unary and tokens[i+1][0] != "op": 
                    tokens[i:i+2] = [[tokens[i], tokens[i+1]]]
    
                elif tokens[i][1] in binary:
                    tokens[i-1:i+2] = [[tokens[i], tokens[i-1], tokens[i+1]]]

                elif tokens[i][1] in ternary:
                    tokens[i-2:i+2] = [[tokens[i], tokens[i-2], tokens[i-1], tokens[i+1]]]
        
                elif tokens[i][1] in quaternary:
                    tokens[i-1:i+4] = [[tokens[i], tokens[i-1], tokens[i+1], 
                            tokens[i+2], tokens[i+3]]]
                i = 0
            i += 1
    return tokens[0]

cells = []
var_func = {}
aliases = {}
DEBUG = False
if len(argv) == 3 and len(argv[2]) > 0:
    DEBUG = True 

def eval_function(function, tokens, bf, params=[]):
    return_token = None
    for e in function:
        return_token = eval_expression(e, tokens, bf, params)
    return return_token

def eval_expression(expression, tokens, bf, params):
    global cells
    def get_type(cell):
        result = None
        for var in cells:
            if cell == var[0] or cell == var[1]:
                result = var[2]
        return result
    
    def get_func(func):
        if type(func) == int:
            return tokens[func]
        elif type(func) == list:
            return func
        elif type(func) == str:
            return tokens[var_func[func]]
 
    # NOP return expression
    if type(expression) == tuple:
        return expression

    # Recursively run expressions
    current_expression = expression.copy()
    i = 0
    while i < len(current_expression):
        # Check for alias definition operator (Pre-evaluation)
        if current_expression[i][0] == "op" and current_expression[i][1] == "@=":
            while type(current_expression[i+1]) == list:
                current_expression[i+1] = eval_expression(current_expression[i], tokens, bf, params) 
            aliases[current_expression[i+1][1]] = current_expression[i+2]
            current_expression[i:i+3] = (current_expression[i+2],)
            if len(current_expression) == 1:
                return current_expression[0]
    
        # Replace aliases with tokens
        while current_expression[i][0] == "var" and current_expression[i][1] in aliases:
            current_expression[i] = aliases[current_expression[i][1]]

        if type(current_expression[i]) is list:
            current_expression[i] = eval_expression(current_expression[i], tokens, bf, params)

        i += 1

       # Run expressions depending on operator and argument types
    if DEBUG:
        print("[DEBUG]", current_expression)
    op = current_expression[0][1]
    argt = tuple([t[0] for t in current_expression[1:]])
    argv = tuple([t[1] for t in current_expression[1:]])

    if op == "@":
        if argt == ("type", "var"):
            if argv[0] == "int" or argv[0] == "char":
                defined = bf.def_(argv[1])
                cells += ((defined, argv[1], argv[0]),) 
                return "var", defined
            elif argv[0] == "arr" or argv[0] == "str":
                cells += ((None, argv[1], argv[0]),)
                return "var", argv[1]
            elif argv[0] == "func":
                var_func[argv[1]] = None
                return "var", argv[1]
    elif op == ">@":
        if argt == ("type", "int", "var"):
            defined = bf.defArr(argv[2], argv[1])
            cells += ((defined, argv[2], argv[0]),)
            return "var", defined
    elif op == "@>":
        if argt == ("var", "type"):
            if get_type(argv[0]) == "int" and argv[1] == "char" or\
                get_type(argv[0]) == "char" and argv[1] == "int":
                    cell = bf.malloc()
                    bf.setVar(cell, argv[0])
                    cells += ((cell, None, argv[1]),)
                    return "var", cell
            elif get_type(argv[0]) == "arr" and argv[1] == "str" or\
                get_type(argv[0]) == "str" and argv[1] == "arr":
                    cell = bf.malloc(bf.length(argv[0]))
                    bf.copyArr(argv[0], cell)
                    cells += ((cell, None, argv[1]),)
                    return "var", cell            
            elif get_type(argv[0]) == "int" and argv[1] == "str":
                cell = bf.toArr(argv[0])
                cells += ((cell, None, "str"),)
                return "var", cell
        elif argt == ("int", "type"):
            if argv[1] == "char":
                return "char", chr(argv[0])
            elif argv[1] == "str":
                return "str", str(argv[0])
            elif argv[1] == "func":
                return "func", get_func(argv[0])
        elif argt == ("char", "type"):
            if argv[1] == "int":
                return "int", ord(argv[0])
            elif argv[1] == "str":
                return "str", str(argv[0])
        elif argt == ("arr", "type"):
            if argv[1] == "str":
                return "str", "".join([chr(i) for i in argv[0]])
        elif argt == ("str", "type"):
            if argv[1] == "arr":
                return "arr", [ord(i) for i in argv[0]]    
        elif argt == ("func", "type"):
            if argv[1] == "int":
                for i in range(len(tokens)):
                    if get_func(i) == get_func(argv[0]):
                        return "int", i
            elif argv[1] == "str":
                return "str", str(get_func(argv[0]))
    elif op == "->":
        if argt == ("var",) or argt == ("int",) or argt == ("func",):
            return eval_function(get_func(argv[0]), tokens, bf)
    elif op == "~":
        if argt == ("int",):
            return params[argv[0]]
    elif op == "=":
        if argt == ("var", "var"):
            if get_type(argv[0]) in ("int", "char") and \
                    get_type(argv[1]) in ("int", "char"):
                    bf.setVar(argv[0], argv[1])
                    return "var", argv[0]
            elif get_type(argv[0]) in ("arr", "str") and \
                    get_type(argv[1]) in ["arr", "str"]:
                    if bf.get(argv[0]) == None:
                            defined = bf.defArr(argv[0], bf.length(argv[1]))
                    for cell in cells:
                        if cell[1] == argv[0]:
                            cells += ((defined, cell[1], 
                                cell[2]),)
                            cells.remove(cell)
                            break
                    bf.copyArr(argv[1], argv[0])
                    return "var", argv[0]
        elif argt == ("var", "int") or argt == ("var", "char"):
            bf.set(argv[0], argv[1])
            return "var", argv[0]
        elif argt == ("var", "arr") or argt == ("var", "str"):
            if bf.get(argv[0]) == None:
                defined = bf.defArr(argv[0], argv[1])
                for cell in cells:
                    if cell[1] == argv[0]:
                        cells += ((defined, cell[1], 
                            cell[2]),)
                        cells.remove(cell)
                        break
            bf.setArr(argv[0], argv[1])
            return "var", argv[0]
        elif argt == ("var", "func"):
            if argv[0] in var_func:
                var_func[argv[0]] = argv[1]
            return "func", argv[0]
    elif op == "^":
        if argt == ("var",):    
            return "int", bf.length(argv[0])
        elif argt == ("arr",) or argt == ("str",):
            return "int", len(argv[0])    
    elif op == "[":
        if argt == ("var", "var"):
            cell = bf.getIndex(argv[0], argv[1])
            if get_type(argv[0]) == "arr":
                cells += ((cell, None, "int"),)
            elif get_type(argv[0]) == "str":
                cells += ((cell, None, "char"),)
            return "var", cell
        elif argt == ("arr", "var"):
            cell = bf.malloc()
            temp = bf.malloc(len(argv[0]))
            bf.setArr(temp, argv[0])
            bf.move(bf.getIndex(temp, argv[1]), cell, reset=False)
            bf.free(len(argv[0]) + 1, reset=True)
            cells += ((cell, None, "int"),)
            return "var", cell
        elif argt == ("str", "var"):
            cell = bf.malloc()
            temp = bf.malloc(len(argv[0]))
            bf.setArr(temp, argv[0])
            bf.move(bf.getIndex(temp, argv[1]), cell, reset=False)
            bf.free(len(argv[0]) + 1, reset=True)
            cells += ((cell, None, "char"),)
            return "var", cell
        elif argt == ("var", "int"):
            cell = bf.index(argv[0], argv[1])
            if get_type(argv[0]) == "arr":
                cells += ((cell, None, "int"),)
            elif get_type(argv[0]) == "str":
                cells += ((cell, None, "char"),)
            return "var", cell
        elif argt == ("arr", "int"):
            return "int", argv[0][argv[1]]
        elif argt == ("str", "int"):
            return "char", argv[0][argv[1]]
    elif op == "]=":
        if argt == ("var", "var", "var"):
            bf.setIndexVar(argv[0], argv[1], argv[2])
            return "var", argv[0]
        elif argt == ("var", "var", "int") or argt == ("var", "var", "char"):
            bf.setIndex(argv[0], argv[1], argv[2])
            return "var", argv[0]
        elif argt == ("var", "int", "var"):
            bf.setVar(bf.index(argv[0], argv[1]), argv[2])    
            return "var", argv[0]
        elif argt == ("var", "int", "int") or argt == ("var", "int", "char"):
            bf.set(bf.index(argv[0], argv[1]), argv[2])
            return "var", argv[0]
    elif op == "!":
        if argt == ("var",):
            cell = bf.not_(argv[0])
            cells += ((cell, None, "int"),)
            return "var", cell    
    elif op == "&":
        if argt == ("var", "var"):
            cell = bf.and_(argv[0], argv[1])
            cells += ((cell, None, "int"),)
            return "var", cell    
    elif op == "|":
        if argt == ("var", "var"):
            cell = bf.or_(argv[0], argv[1])
            cells += ((cell, None, "int"),)
            return "var", cell
    elif op == "+":
        if argt == ("var", "var"):
            if get_type(argv[0]) == "int" and get_type(argv[0]) == "int":
                cell = bf.addVar(argv[0], argv[1])
                cells += ((cell, None, "int"),)
                return "var", cell
            elif get_type(argv[0]) == "str" and get_type(argv[1]) == "str":
                cell = bf.concat(argv[0], argv[1])
                cells += ((cell, None, "str"),)
                return "var", cell
            elif get_type(argv[0]) == "arr" and get_type(argv[1]) == "arr":
                cell = bf.concat(argv[0], argv[1])
                cells += ((cell, None, "arr"),)
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
        elif argt == ("var", "str") or argt == ("var", "arr"):
            cell = bf.concatStrl(argv[0], argv[1])
            cells += ((cell, None, argt[1]),)
            return "var", cell
        elif argt == ("str", "var") or argt == ("arr", "var"):
            cell = bf.concatStrr(argv[0], argv[1])
            cells += ((cell, None, argt[0]),)
            return "var", cell
        elif argt == ("str", "str") or argt == ("arr", "arr"):
            return argt[0], argv[0] + argv[1]
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
        if argt == ("var", "var"):
            cell = bf.eqVar(argv[0], argv[1])
            cells += ((cell, None, "int"),)
            return "var", cell
        elif (argt == ("var", "int") or argt == ("var", "char")) and get_type(argv[0]) == argt[1]:
            op = argv[1] if argt[1] == "int" else ord(argv[1])
            cell = bf.eq(argv[0], op)
            cells += ((cell, None, "int"),)
            return "var", cell
        elif (argt == ("int", "var") or argt == ("char", "var")) and get_type(argv[1]) == argt[0]:
            op = argv[0] if argt[0] == "int" else ord(argv[0])
            cell = bf.eq(argv[1], op)
            cells += ((cell, None, "int"),)
            return "var", cell
        elif argt == ("int", "int") or argt == ("char", "char"):
            return "int", int(argv[0] == argv[1])
    elif op == "!=":
        if argt == ("var", "var"):
            cell = bf.neqVar(argv[0], argv[1])
            cells += ((cell, None, "int"),)
            return "var", cell
        elif (argt == ("var", "int") or argt == ("var", "char")) and get_type(argv[0]) == argt[1]:
            op = argv[1] if argt[1] == "int" else ord(argv[1])
            cell = bf.neq(argv[0], op)
            cells += ((cell, None, "int"),)
            return "var", cell
        elif (argt == ("int", "var") or argt == ("char", "var")) and get_type(argv[1]) == argt[0]:
            op = argv[0] if argt[0] == "int" else ord(argv[0])
            cell = bf.neq(argv[1], op)
            cells += ((cell, None, "int"),)
            return "var", cell
        elif argt == ("int", "int") or argt == ("char", "char"):
            return "int", int(argv[0] != argv[1])
    elif op == ">":
        if argt == ("var", "var"):
            cell = bf.gtVar(argv[0], argv[1])
            cells += ((cell, None, "int"),)
            return "var", cell
        elif argt == ("var", "int"):
            cell = bf.gtl(argv[0], argv[1])
            cells += ((cell, None, "int"),)
            return "var", cell
        elif argt == ("int", "var"):
            cell = bf.gtr(argv[0], argv[1])
            cells += ((cell, None, "int"),)
            return "var", cell
        elif argt == ("int", "int"):
            return "int", int(argv[0] > argv[1])
    elif op == ">=":
        if argt == ("var", "var"):
            cell = bf.gtEqVar(argv[0], argv[1])
            cells += ((cell, None, "int"),)
            return "var", cell
        elif argt == ("var", "int"):
            cell = bf.gtEql(argv[0], argv[1])
            cells += ((cell, None, "int"),)
            return "var", cell
        elif argt == ("int", "var"):
            cell = bf.gtEqr(argv[0], argv[1])
            cells += ((cell, None, "int"),)
            return "var", cell
        elif argt == ("int", "int"):
            return "int", int(argv[0] >= argv[1])
    elif op == "<":
        if argt == ("var", "var"):
            cell = bf.ltVar(argv[0], argv[1])
            cells += ((cell, None, "int"),)
            return "var", cell
        elif argt == ("var", "int"):
            cell = bf.ltl(argv[0], argv[1])
            cells += ((cell, None, "int"),)
            return "var", cell
        elif argt == ("int", "var"):
            cell = bf.ltr(argv[0], argv[1])
            cells += ((cell, None, "int"),)
            return "var", cell
        elif argt == ("int", "int"):
            return "int", int(argv[0] < argv[1])
    elif op == "<=":
        if argt == ("var", "var"):
            cell = bf.ltEqVar(argv[0], argv[1])
            cells += ((cell, None, "int"),)
            return "var", cell
        elif argt == ("var", "int"):
            cell = bf.ltEql(argv[0], argv[1])
            cells += ((cell, None, "int"),)
            return "var", cell
        elif argt == ("int", "var"):
            cell = bf.ltEqr(argv[0], argv[1])
            cells += ((cell, None, "int"),)
            return "var", cell
        elif argt == ("int", "int"):
            return "int", int(argv[0] <= argv[1])
    elif op == ".":
        if argt == ("var",):
            if get_type(argv[0]) == "char":
                bf.print(argv[0])
                return "var", argv[0]
            elif get_type(argv[0]) == "str":
                bf.printArr(argv[0])
                return "var", argv[0]
            elif get_type(argv[0]) == "int":
                bf.printArr(bf.toArr(argv[0]))
                bf.free(3, reset=True)
                return "var", argv[0]
            elif get_type(argv[0]) == "arr":
                def do(param):
                    bf.printArr(bf.toArr(param))
                    bf.printStr(" ")
                bf.foreach(argv[0], do)
                return "var", argv[0]
        elif argt == ("str",) or argt == ("char",):
            bf.printStr(argv[0])
            return argt[0], argv[0]
        elif argt == ("int",):
            bf.printStr(str(argv[0]))
            return "int", argv[0]
        elif argt == ("arr",):
            bf.printStr(" ".join([str(i) for i in argv[0]]))
            return "arr", argv[0]
        elif argt == ("func",):
            bf.printStr(f"func: {get_func(argv[0])}")
            return "func", argv[0]
    elif op == ",":
        if argt == ("type",):
            if argv[0] == "char":
                cell = bf.input()
                cells += ((cell, None, "char"),)
                return "var", cell
            elif argv[0] == "int":
                cell = bf.malloc()
                bf.move(bf.toInt(bf.inputArr()), cell, reset=False)
                bf.free(4, reset=True)
                cells += ((cell, None, "int"),)
                return "var", cell
        elif argt == ("var",):
            if get_type(argv[0]) == "char":
                cell = bf.input()
                cells += ((cell, None, "char"),)
                return "var", cell
            elif get_type(argv[0]) == "int":
                cell = bf.malloc()
                bf.move(bf.toInt(bf.inputArr()), cell, reset=False)
                bf.free(4, reset=True)
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
        if argt == ("var", "func"):
            def do():
                eval_function(get_func(argv[1]), tokens, bf, params=params)
            bf.if_(argv[0], do)
            return "var", argv[0]
    elif op == "!?":
        if argt == ("var", "func", "func"):
            def ifdo():
                eval_function(get_func(argv[1]), tokens, bf, params=params)
            def elsedo():
                eval_function(get_func(argv[2]), tokens, bf, params=params)
            bf.ifelse(argv[0], ifdo, elsedo)
            return "var", argv[0]
    elif op == "?*":
        if argt == ("func", "func"):
            def cond():
                return eval_function(get_func(argv[0]), tokens, bf, params=params)[1]
            def do():
                eval_function(get_func(argv[1]), tokens, bf, params=params)
            bf.while_(cond, do)
            return "int", 1
    elif op == ":":
        if argt == ("func", "func", "func", "func"):
            def start(param):
                global cells
                cells += ((param, None, "int"),)
                eval_function(get_func(argv[0]), tokens, bf, params=[("var", param)] + params)
            def cond(param):
                return eval_function(get_func(argv[1]), tokens, bf, params=[("var", param)] + params)[1]
            def step(param):
                eval_function(get_func(argv[2]), tokens, bf, params=[("var", param)] + params)
            def do(param):            
                eval_function(get_func(argv[3]), tokens, bf, params=[("var", param)] + params)
            bf.for_(start, cond, step, do)    
            return "int", 1
    elif op == "*!":
        if argt == ("func",):
            def do():
                eval_function(get_func(argv[0]), tokens, bf, 
                    params=params)
            bf.forever(do)
            return "int", 1
    elif op == "[*":
        if argt == ("var", "func"):
            def do(param):
                global cells
                if get_type(argv[0]) == "arr":
                    cells += ((param, None, "int"),)
                elif get_type(argv[0]) == "str":
                    cells += ((param, None, "char"),)
                eval_function(get_func(argv[1]), tokens, bf, params=[("var", param)] + params)
            bf.foreach(argv[0], do)
            return "var", argv[0]
        elif argt == ("arr", "func"):
            memstate = bf.saveMemState()
            for param in argv[0]:
                eval_function(get_func(argv[1]), tokens, bf, params=[("int", param)] + params)
                bf.loadMemState(memstate)
            return "arr", argv[0]
        elif argt == ("str", "func"):
            memstate = bf.saveMemState()
            for param in argv[0]:
                eval_function(get_func(argv[1]), tokens, bf, params=[("char", param)] + params)
                bf.loadMemState(memstate)
            return "arr", argv[0]

    # No return -> No evaluation happened
    try:
        types = [(argt[i] if argt[i] != "var" else "var:" + get_type(argv[i])) + f" ({argv[i]})" for i in range(len(argt))]
    except:
        raise TypeError(f"Couldn't get type of argument in expression {expression}") 
    if len(types) > 1:
        formatted_types = ", ".join(types)
        raise TypeError(f"Arguments of types \"{formatted_types}\" are not supported for operator \"{op}\"." + \
                f"\nExpression: {expression}")    
    else:
        raise TypeError(f"Argument of type \"{types[0]}\" is not supported for operator \"{op}\"." + \
                f"\nExpression: {expression}")
        
def compile():
    tokens = preprocessor(get_source())
    for f in range(len(tokens)):
        for e in range(len(tokens[f])):
            tokens[f][e] = AST(tokens[f][e])
    bf = bf_compiler()
    result = eval_function(tokens[0], tokens, bf, params=[("str", argv[1])])
    if DEBUG:
        print("[DEBUG] Return:", result, 
            "\n[DEBUG] Variable List:", cells, "\n[DEBUG] Alias List:", aliases,
            "\n[DEBUG] Function List:", var_func,
            "\n[DEBUG] Used mem:", bf.used_mem, "\n[DEBUG] Used temp mem:", bf.used_temp,
            "\n[DEBUG] Pointer position:", bf.pointer)
    bf.result(argv[1][argv[1].find("/")+1:argv[1].find(".")], trimmed=not DEBUG)

compile()    
