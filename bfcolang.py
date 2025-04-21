from bfcompiler import *
from typing import List, Tuple, Any, Union, Optional
import sys

Token = Union[Tuple[str, Union[str, int]], Tuple[str, Optional[str], str]]
Expression = List[Union[Token, "Expression"]]
Function = List[Expression]
Program = List[Function]

DEBUG_OP_WORDS = {
        "->": "CALL", "~": "PARAM", "^": "LENGTH",
        ".": "OUT", ",": "IN", "!" : "NOT",
        "++": "INC", "--": "DEC", "*!": "FOREVER",
        "[": "GET_INDEX", "*": "MUL", "/": "DIV",
        "%": "MOD", "+": "ADD", "-": "SUB",
        ">": "GT", "<": "LT", ">=": "GTEQ", "<=": "LTEQ",
        "==": "EQ", "!=": "NEQ", "&": "AND", "|": "OR",
        "=": "ASSIGN", "@=": "ALIAS", "@": "DEFINE",
        "@>": "CAST", "?": "IF", "?*": "WHILE",
        "[*": "FOREACH", "]=": "INDEX_SET", ">@": "DEF_SIZED",
        "!?": "IFELSE", ":": "FOR"
    }

unary = ["->", "~", "^", ".", ",", "!", "++", "--", "*!"]
binary = ["[", "*", "/", "%", "+", "-", ">", "<", ">=", "<=", "==", "!=",
         "&", "|", "=", "@=", "@", "@>", "?", "?*", "[*"]
ternary = ["]=", ">@", "!?"]
ternary_cut = {"]=": "[", ">@": "<", "!?": "?"}
quaternary = [":"]
operators  = unary + binary + ternary + quaternary

op_presedence = ("->", "~", "^", "["), ("!", ".", ",", "++", "--"), \
    ("*", "/", "%"), ("+", "-"), (">", "<", ">=", "<=", "==", "!="), \
    ("&",), ("|",), ("=", "]=", "@=", "@", "@>", ">@"), ("?", "!?", "?*", "*!", "[*", ":")     

types = ["int", "char", "arr", "str", "func"]
valid_var = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"

def pre_processor(source : str) -> List[List[str]]:
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
    
    return expressions


def lexer(expression : str) -> Expression:
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
            tokens += [("var", None, var)]

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

def AST(tokens : Expression) -> Expression:
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
    for field in op_presedence:
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

variables = {}
functions = {}
aliases = {}

DEBUG = False
if len(sys.argv) == 3 and len(sys.argv[2]) > 0:
    DEBUG = True 

def eval_function(function : Function, tokens : Program, bf : bf_compiler, params : Any = []) -> Token:
    return_token = None
    for e in function:
        return_token = eval_expression(e, tokens, bf, params)
    return return_token

def eval_expression(expression : Expression, tokens : Program, bf : bf_compiler, params : Any) -> Token:
    # Add variable types
    for i in range(len(expression)):
        if expression[i][0] == "var" and expression[i][1] == None and expression[i][2] in variables:
            expression[i] = (expression[i][0], variables[expression[i][2]], expression[i][2])
     
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
            aliases[current_expression[i+1][2]] = current_expression[i+2]
            current_expression[i:i+3] = (current_expression[i+2],)
            if len(current_expression) == 1:
                return current_expression[0]
    
        # Replace aliases with tokens
        while current_expression[i][0] == "var" and current_expression[i][2] in aliases:
            current_expression[i] = aliases[current_expression[i][2]]

        if type(current_expression[i]) is list:
            current_expression[i] = eval_expression(current_expression[i], tokens, bf, params)

        i += 1

    # Run expressions depending on operator and argument types
    if DEBUG:
        print("[DEBUG]", current_expression)
    op = current_expression[0][1]
    argt = tuple([t[0] for t in current_expression[1:]])
    argv = tuple([t[1] if t[0] != "var" else t[2] for t in current_expression[1:]])
    vart = tuple([None if t[0] != "var" else t[1] for t in current_expression[1:]])

    if DEBUG:
        bf.code += f"\n{DEBUG_OP_WORDS[op]} "
        bf.code += " ".join(argt)
        bf.code += "!\n"

    # DEFINE
    if op == "@":
        if argt == ("type", "var"):
            if argv[0] == "int" or argv[0] == "char":
                variables[argv[1]] = argv[0]
                return "var", argv[0], bf.def_(argv[1])
            elif argv[0] == "arr" or argv[0] == "str":
                variables[argv[1]] = argv[0]
                return "var", argv[0], argv[1]
            elif argv[0] == "func":
                functions[argv[1]] = None
                return "var", "func", argv[1]
    
    # DEFINE_SIZED
    elif op == ">@":
        if argt == ("type", "int", "var"):
            variables[argv[2]] = argv[0]
            return "var", argv[0], bf.defArr(argv[2], argv[1])
    
    # CAST
    elif op == "@>":
        if argt == ("var", "type"):        
            if vart[0] == "int" and argv[1] == "str":
                return "var", "str", bf.toArr(argv[0])
            elif vart[0] == "str" and argv[1] == "int":
                return "var", "int", bf.toInt(argv[0])
            else:
                return "var", argv[1], argv[0]
        elif argt == ("int", "type"):
            if argv[1] == "char":
                return "char", chr(argv[0])
            elif argv[1] == "str":
                return "str", str(argv[0])
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
            
    # CALL
    elif op == "->":
        if argt == ("var",):
            return eval_function(tokens[functions[argv[0]]], tokens, bf)
        
    # PARAM
    elif op == "~":
        if argt == ("int",):
            return params[argv[0]]
        
    # ASSIGN
    elif op == "=":
        if argt == ("var", "var"):
            if vart[0] in ("int", "char") and \
                    vart[1] in ("int", "char"):
                    bf.copy(argv[1], argv[0], assign=True)
                    return "var", vart[0], argv[0]
            elif vart[0] in ("arr", "str") and \
                    vart[1] in ("arr", "str"):
                    if bf.get(argv[0]) == None:
                        bf.defArr(argv[0], bf.length(argv[1]))
                    bf.copyArr(argv[1], argv[0], assign=True)
                    return "var", vart[0], argv[0]
        elif argt == ("var", "int") or argt == ("var", "char"):
            bf.set(argv[0], argv[1])
            return "var", vart[0], argv[0]
        elif argt == ("var", "arr") or argt == ("var", "str"):
            if bf.get(argv[0]) == None:
                bf.defArr(argv[0], argv[1])
            else:
                bf.setArr(argv[0], argv[1])
            return "var", vart[0], argv[0]
        elif argt == ("var", "func"):
            if argv[0] in functions:
                functions[argv[0]] = argv[1]
            return "var", vart[0], argv[0]
        
    # LENGTH
    elif op == "^":
        if argt == ("var",):    
            return "int", bf.length(argv[0])
        elif argt == ("arr",) or argt == ("str",):
            return "int", len(argv[0])

    # GET_INDEX    
    elif op == "[":
        if argt == ("var", "var"):
            return "var", "int" if vart[0] == "arr" else "char", bf.getIndex(argv[0], argv[1])
        elif argt == ("arr", "var") or argt == ("str", "var"):
            cell = bf.malloc()
            temp = bf.mallocArr(len(argv[0]))
            bf.setArr(temp, argv[0])
            bf.move(bf.getIndex(temp, argv[1]), cell, reset=False)
            bf.freeArr(argv[0], reset=True)
            return "var", "int" if argt[0] == "arr" else "char", cell
        elif argt == ("var", "int"):
            cell = bf.index(argv[0], argv[1])
            return "var", "int" if vart[0] == "arr" else "char", cell
        elif argt == ("arr", "int"):
            return "int", argv[0][argv[1]]
        elif argt == ("str", "int"):
            return "char", argv[0][argv[1]]
        
    # SET_INDEX
    elif op == "]=":
        if argt == ("var", "var", "var"):
            bf.setIndexVar(argv[0], argv[1], argv[2])
            return "var", vart[0], argv[0]
        elif argt == ("var", "var", "int") or argt == ("var", "var", "char"):
            bf.setIndex(argv[0], argv[1], argv[2])
            return "var", vart[0], argv[0]
        elif argt == ("var", "int", "var"):
            bf.copy(argv[2], bf.index(argv[0], argv[1]))    
            return "var", vart[0], argv[0]
        elif argt == ("var", "int", "int") or argt == ("var", "int", "char"):
            bf.set(bf.index(argv[0], argv[1]), argv[2])
            return "var", vart[0], argv[0]
        
    # NOT
    elif op == "!":
        if argt == ("var",):
            return "var", "int", bf.not_(argv[0])
        elif argt == ("int",):
            return "int", int(not argv[0])
        
    # AND
    elif op == "&":
        if argt == ("var", "var"):
            return "var", "int", bf.and_(argv[0], argv[1])
        elif argt == ("var", "int"):
            cell = bf.malloc()
            if argv[1]:
                bf.set(cell, 1)
            else:
                bf.copy(argv[0], cell)
            return "var", "int", cell
        elif argt == ("int", "var"):
            cell = bf.malloc()
            if argv[0]:
                bf.set(cell, 1)
            else:
                bf.copy(argv[1], cell)
            return "var", "int", cell
        elif argt == ("int", "int"):
            return "int", int(argv[0] and argv[1])
        
    # OR
    elif op == "|":
        if argt == ("var", "var"):
            return "var", "int", bf.or_(argv[0], argv[1])
        elif argt == ("var", "int"):
            cell = bf.malloc()
            if argv[1]:
                bf.copy(argv[0], cell)
            else:
                bf.set(cell, 0)
            return "var", "int", cell
        elif argt == ("int", "var"):
            cell = bf.malloc()
            if argv[0]:
                bf.copy(argv[1], cell)
            else:
                bf.set(cell, 0)
            return "var", "int", cell
        elif argt == ("int", "int"):
            return int(argv[0] and argv[1])
    
    # ADD
    elif op == "+":
        if argt == ("var", "var"):
            if vart[0] == "int" and vart[0] == "int":
                return "var", "int", bf.addVar(argv[0], argv[1])
        elif argt == ("var", "int"):
            return "var", "int", bf.add(argv[0], argv[1])
        elif argt == ("int", "var"):
            return "var", "int", bf.add(argv[1], argv[0])
        elif argt == ("int", "int"):
            return "int", argv[0] + argv[1]
        elif argt == ("arr", "arr"):
            return argt[0], argv[0] + argv[1]
        
    # SUB
    elif op == "-":
        if argt == ("var", "var"):
            return "var", "int", bf.subVar(argv[0], argv[1])
        elif argt == ("var", "int"):
            return "var", "int", bf.subl(argv[0], argv[1])
        elif argt == ("int", "var"):
            return "var", "int", bf.subr(argv[0], argv[1])
        elif argt == ("int", "int"):
            return "int", argv[0] - argv[1]   

    # MUL 
    elif op == "*":
        if argt == ("var", "var"): 
            return "var", "int", bf.mulVar(argv[0], argv[1])
        elif argt == ("var", "int"):
            return "var", "int", bf.mul(argv[0], argv[1])
        elif argt == ("int", "var"):
            return "var", "int", bf.mul(argv[1], argv[0])
        elif argt == ("int", "int"):
            return "int", argv[0] * argv[1]    
        
    # DIV
    elif op == "/":
        if argt == ("var", "var"):
            cell = bf.divModVar(argv[0], argv[1])
            bf.free(reset=True)
            return "var", "int", cell[0]
        elif argt == ("var", "int"):
            cell = bf.divModl(argv[0], argv[1])
            bf.free(reset=True)
            return "var", "int", cell[0]
        elif argt == ("int", "var"):
            cell = bf.divModr(argv[0], argv[1])
            bf.free(reset=True)
            return "var", "int", cell[0]
        elif argt == ("int", "int"):
            return "int", argv[0] // argv[1] 
           
    # MOD
    elif op == "%":
        if argt == ("var", "var"):
            result = bf.divModVar(argv[0], argv[1])
            bf.move(result[1], result[0], reset=True)
            bf.free()
            return "var", "int", result[0]
        elif argt == ("var", "int"):
            result = bf.divModl(argv[0], argv[1])
            bf.move(result[1], result[0], reset=True)
            bf.free()
            return "var", "int", result[0]
        elif argt == ("int", "var"):
            result = bf.divModr(argv[0], argv[1])
            bf.move(result[1], result[0], reset=True)
            bf.free()
            return "var", "int", result[0]
        elif argt == ("int", "int"):
            return "int", argv[0] % argv[1]  
          
    # INC
    elif op == "++":
        if argt == ("var",):
            bf.inc(argv[0])
            return "var", "int", argv[0]    
        elif argt == ("int",):
            return "int", argv[0] + 1
    
    # DEC
    elif op == "--":
        if argt == ("var",):
            bf.dec(argv[0])
            return "var", "int", argv[0]    
        elif argt == ("int",):
            return "int", argv[0] - 1
        
    # EQ
    elif op == "==":
        if argt == ("var", "var"):
            return "var", "int", bf.eqVar(argv[0], argv[1])
        elif (argt == ("var", "int") or argt == ("var", "char")) and vart[0] == argt[1]:
            op = argv[1] if argt[1] == "int" else ord(argv[1])
            return "var", "int", bf.eq(argv[0], op)
        elif (argt == ("int", "var") or argt == ("char", "var")) and vart[1] == argt[0]:
            op = argv[0] if argt[0] == "int" else ord(argv[0])
            return "var", "int", bf.eq(argv[1], op)
        elif argt == ("int", "int") or argt == ("char", "char"):
            return "int", int(argv[0] == argv[1])
    
    # NEQ
    elif op == "!=":
        if argt == ("var", "var"):
            return "var", "int", bf.neqVar(argv[0], argv[1])
        elif (argt == ("var", "int") or argt == ("var", "char")) and vart[0] == argt[1]:
            op = argv[1] if argt[1] == "int" else ord(argv[1])
            return "var", "int", bf.neq(argv[0], op)
        elif (argt == ("int", "var") or argt == ("char", "var")) and vart[1] == argt[0]:
            op = argv[0] if argt[0] == "int" else ord(argv[0])
            return "var", "int", bf.neq(argv[1], op)
        elif argt == ("int", "int") or argt == ("char", "char"):
            return "int", int(argv[0] != argv[1])
        
    # GT
    elif op == ">":
        if argt == ("var", "var"):
            return "var", "int", bf.gtVar(argv[0], argv[1])
        elif argt == ("var", "int"):
            return "var", "int", bf.gtl(argv[0], argv[1])
        elif argt == ("int", "var"):
            return "var", "int", bf.gtr(argv[0], argv[1])
        elif argt == ("int", "int"):
            return "int", int(argv[0] > argv[1])
        
    # GTEQ
    elif op == ">=":
        if argt == ("var", "var"):
            return "var", "int", bf.gtEqVar(argv[0], argv[1])
        elif argt == ("var", "int"):
            return "var", "int", bf.gtEql(argv[0], argv[1])
        elif argt == ("int", "var"):
            return "var", "int", bf.gtEqr(argv[0], argv[1])
        elif argt == ("int", "int"):
            return "int", int(argv[0] >= argv[1])
        
    # LT
    elif op == "<":
        if argt == ("var", "var"):
            return "var", "int", bf.ltVar(argv[0], argv[1])
        elif argt == ("var", "int"):
            return "var", "int", bf.ltl(argv[0], argv[1])
        elif argt == ("int", "var"):
            return "var", "int", bf.ltr(argv[0], argv[1])
        elif argt == ("int", "int"):
            return "int", int(argv[0] < argv[1])
        
    # LTEQ
    elif op == "<=":
        if argt == ("var", "var"):
            return "var", "int", bf.ltEqVar(argv[0], argv[1])
        elif argt == ("var", "int"):
            return "var", "int", bf.ltEql(argv[0], argv[1])
        elif argt == ("int", "var"):
            return "var", "int", bf.ltEqr(argv[0], argv[1])
        elif argt == ("int", "int"):
            return "int", int(argv[0] <= argv[1])
        
    # OUT
    elif op == ".":
        if argt == ("var",):
            if vart[0] == "char":
                bf.print(argv[0], clean=True)
                return "int", 1
            elif vart[0] == "str":
                bf.printArr(argv[0], clean=True)
                return "int", 1
            elif vart[0] == "int":
                bf.printArr(bf.toArr(argv[0]), clean=True)
                return "int", 1
            elif vart[0] == "arr":
                def do(param):
                    bf.printArr(bf.toArr(param), clean=True)
                    bf.printStr(" ")
                bf.foreach(argv[0], do)
                return "int", 1
        elif argt == ("str",) or argt == ("char",):
            bf.printStr(argv[0])
            return "int", 1
        elif argt == ("int",):
            bf.printStr(str(argv[0]))
            return "int", 1
        elif argt == ("arr",):
            bf.printStr(" ".join([str(i) for i in argv[0]]))
            return "int", 1
        
    # IN
    elif op == ",":
        if argt == ("type",):
            if argv[0] == "char":
                return "var", "char", bf.input()
            elif argv[0] == "int":
                return "var", "int", bf.toInt(bf.inputArr())
        elif argt == ("var",):
            if vart[0] == "char":
                return "var", "char", bf.input()
            elif vart[0] == "int":
                return "var", "int", bf.toInt(bf.inputArr())
            elif vart[0] == "str":
                return "var", "str", bf.inputArr(len_=bf.length(argv[0]))
            elif vart[0] == "arr":
                arr = bf.mallocArr(bf.length(argv[0]))
                def start(param):
                    pass
                def cond(param):
                    return bf.ltl(param, bf.length(argv[0]))
                def step(param):
                    bf.inc(param)
                def do(param):
                    bf.setIndexVar(arr, param, bf.toInt(bf.inputArr()))
                bf.for_(start, cond, step, do)
                return "var", "arr", arr
            
    # IF
    elif op == "?":
        if argt == ("var", "func"):
            def do():
                eval_function(tokens[argv[1]], tokens, bf, params=params)
            bf.if_(argv[0], do)
            return "var", argv[0]
        
    # IF_ELSE
    elif op == "!?":
        if argt == ("var", "func", "func"):
            def ifdo():
                eval_function(tokens[argv[1]], tokens, bf, params=params)
            def elsedo():
                eval_function(tokens[argv[2]], tokens, bf, params=params)
            bf.ifelse(argv[0], ifdo, elsedo)
            return "var", argv[0]
        
    # WHILE
    elif op == "?*":
        if argt == ("func", "func"):
            def cond():
                return eval_function(tokens[argv[0]], tokens, bf, params=params)[2]
            def do():
                eval_function(tokens[argv[1]], tokens, bf, params=params)
            bf.while_(cond, do)
            return "int", 1
    
    # FOR
    elif op == ":":
        if argt == ("func", "func", "func", "func"):
            def start(param):
                eval_function(tokens[argv[0]], tokens, bf, params=[("var", "int", param)] + params)
            def cond(param):
                return eval_function(tokens[argv[1]], tokens, bf, params=[("var", "int", param)] + params)[2]
            def step(param):
                eval_function(tokens[argv[2]], tokens, bf, params=[("var", "int", param)] + params)
            def do(param):            
                eval_function(tokens[argv[3]], tokens, bf, params=[("var", "int", param)] + params)
            bf.for_(start, cond, step, do)
            return "int", 1

    # FOREVER
    elif op == "*!":
        if argt == ("func",):
            def do():
                eval_function(tokens[argv[0]], tokens, bf, params=params)
            bf.forever(do)
            return "int", 1
        
    # FOREACH
    elif op == "[*":
        if argt == ("var", "func"):
            def do(param):
                eval_function(tokens[argv[1]], tokens, bf, params=
                              [("var", "int" if vart[0] == "arr" else "char", param)] + params)
            bf.foreach(argv[0], do)
            return "var", argv[0]
        elif argt == ("arr", "func") or argt == ("str", "func"):
            arr = bf.mallocArr(len(argv[0]))
            def do(param):
                eval_function(tokens[argv[1]], tokens, bf, params=
                              [("var", "int" if argt[0] == "arr" else "char", param)] + params)
            bf.setArr(arr, argv[0], reset=False)
            bf.foreach(arr, do)
            return "var", argv[0]

    # No return -> No evaluation happened
    try:
        types = [(argt[i] if argt[i] != "var" else "var:" + vart[i]) + f" ({argv[i]})" for i in range(len(argt))]
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
    with open(sys.argv[1]) as source:
        expressions = pre_processor("".join(source.readlines()))

    tokens = []
    for function in expressions:
        function_tokens = []
        for expression in function:
            function_tokens += [AST(lexer(expression))]
        tokens += [function_tokens]

    bf = bf_compiler()
    result = eval_function(tokens[0], tokens, bf, params=[("str", sys.argv[1])])

    if DEBUG:
        print("[DEBUG] Return:", result, 
            "\n[DEBUG] Variable List:", variables, "\n[DEBUG] Alias List:", aliases,
            "\n[DEBUG] Function List:", functions,
            "\n[DEBUG] Used mem:", bf.used_mem, "\n[DEBUG] Used temp mem:", bf.used_temp,
            "\n[DEBUG] Pointer position:", bf.pointer)
        
    bf.result(sys.argv[1][sys.argv[1].find("/")+1:sys.argv[1].find(".")], trimmed=not DEBUG)
compile()
