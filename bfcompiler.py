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
        instr = sum([self.code.count(instr) for instr in ["+", "-", "<", ">", ".", ",", "[", "]"]])
        print("Program compiled successfully!\n" + 
            f"Generated brainf*ck program has a length of {instr} instructions.")
        file = open(f"generated/{filename}.bf", "w")
        file.write(self.code)
        file.close()
        print(f"Saved to generated/{filename}.bf")
        return self.code

    def trim(self):
        # Remove Operations that undo themselves
        for seq in "+-", "-+", "<>", "><":
            while self.code.find(seq) != -1:
                self.code = self.code.replace(seq, "")
    
        # Remove leading pointer moves
        i = 0
        while i < len(self.code):
            if self.code[i] not in "<>":
                self.code = self.code[i:]
                break
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

        # Remove redundant code after last input/ouput
        find = max(self.code.rfind("."), self.code.rfind(","))
        if find == -1:
            self.code = ""
        else:
            i = 0
            depth = 0
            while i < len(self.code):
                if i >= find and depth == 0:
                    self.code = self.code[:i]
                    break
                if self.code[i] == "[":
                    depth += 1
                elif self.code[i] == "]":
                    depth -= 1
                i += 1
            

    def algorithm(self, filename, part=0):
        file = open(f"algorithms/{filename}.bf", "r")
        self.code += file.readlines()[part].strip()
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
            return arr[0] + index
        return self.vars[arr][0] + index
    
    def length(self, arr):
        if type(arr) != str:
            return arr[1]
        return self.vars[arr][1]


    # Memory Allocation

    def def_(self, name, value=0):
        if type(value) == str:
                value = ord(value)
        free = self.used_mem
        self.vars[name] = free
        self.used_mem += 1
        if value != 0:
            self.set(free, value, reset=False)
        return free

    def defArr(self, name, values):
        if type(values) == str:
            values = list(values) + [0]
        if type(values) == int:
            length = values
        else:
            length = len(values)
        free = (self.used_mem + 4, length)
        self.used_mem += length + 4
        self.vars[name] = free
        if type(values) != int:
            self.setArr(free, values, reset=False)
        return free
    
    def defBig(self, name, size, value=0):
        free = (self.used_mem, size)
        self.vars[name] = free
        self.used_mem += size
        if value != 0:
            self.setBig(free, value)
        return free

    def malloc(self, num=1):
        if num == 1:
            free = -(self.used_temp + 1)
        else:
            free = tuple(range(-(self.used_temp + 1), -(self.used_temp + 1 + num), -1))
        self.used_temp += num
        return free

    def mallocArr(self, num):
        free = (-(self.used_temp + num), num)
        self.used_temp += num + 4
        return free
    
    def mallocBig(self, size, num=1):
        if num == 1:
            free = (-(self.used_temp + size), size)
        else:
            free = tuple((-(self.used_temp + size * i), size) for i in range(1, num + 1))
        self.used_temp += num * size
        return free

    def arrAccessCell(self, arr, num):
        return self.get(arr)[0] - num - 1

    def free(self, num=1, reset=False):
        if reset:
            for cell in range(-self.used_temp, -self.used_temp + num):
                self.reset(cell)
        self.used_temp -= num

    def freeArr(self, arr, reset=False):
        if reset:
            self.resetArr(arr)
        self.used_temp -= arr[1] + 4

    def freeBig(self, size, num=1, reset=False):
        if reset:
            for cell in range(-self.used_temp, -self.used_temp + num * size):
                self.reset(cell)
        self.used_temp -= num * size

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
            self.code += diff * ">"
        else:
            self.code += -diff * "<"
        return cell

    def gotoRel(self, diff):
        if diff > 0:
            self.code += diff * ">"
        else:
            self.code += -diff * "<"

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
    
    def setRel(self, value):
        if type(value) == str:
            value = ord(value)
        if value < 128:
            self.code += value * "+"
        else:
            self.code += (256 - value) * "-"

    def move(self, from_, to, reset=True):
        if reset:
            self.reset(to)
        self.goto(from_)
        self.code += "[-"
        self.inc(to)
        self.goto(from_)
        self.code += "]"
        return to

    def copy(self, from_, to, reset=True, negate=False):
        if reset:
            self.reset(to)
        temp = self.malloc()
        self.goto(from_)
        self.code += "[-"
        if negate:
            self.dec(to)
        else:
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
        self.copy(cell, result, reset=False)
        self.inc(result, value)
        return result

    def addVar(self, cell1, cell2):
        result = self.malloc()
        self.copy(cell1, result, reset=False)
        self.copy(cell2, result, reset=False)
        return result

    def subl(self, cell, value):
        result = self.malloc()
        self.copy(cell, result, reset=False)
        self.dec(result, value)
        return result

    def subr(self, value, cell):
        result = self.malloc()
        self.set(result, value, reset=False)
        self.copy(cell, result, reset=False, negate=True)
        return result

    def subVar(self, cell1, cell2):
        result = self.malloc()
        self.copy(cell1, result, reset=False)
        self.copy(cell2, result, reset=False, negate=True)
        return result

    def mul(self, cell, value):
        result, temp1, temp2 = self.malloc(3)
        self.copy(cell, temp1, reset=False)
        self.set(temp2, value, reset=False)
        self.goto(temp1)
        self.algorithm("mul")
        self.pointer = temp2
        self.free(2)
        return result
    
    def mulVar(self, cell1, cell2):
        result, temp1, temp2 = self.malloc(3)
        self.copy(cell1, temp1, reset=False)
        self.copy(cell2, temp2, reset=False)
        self.goto(temp1)
        self.algorithm("mul")
        self.pointer = temp2
        self.free(2)
        return result

    def divModVar(self, cell1, cell2):
        quotient, remainder, temp0, temp1, temp2, temp3 = self.malloc(6)
        self.copy(cell1, temp3, reset=False)
        self.copy(cell2, temp2, reset=False)
        self.goto(temp1)
        self.algorithm("divMod")
        self.pointer = temp0
        self.free(4)
        return quotient, remainder

    def divModl(self, cell, value):
        quotient, remainder, temp0, temp1, temp2, temp3 = self.malloc(6)
        self.copy(cell, temp3, reset=False)
        self.set(temp2, value, reset=False)
        self.goto(temp1)
        self.algorithm("divMod")
        self.pointer = temp0
        self.free(4)
        return quotient, remainder
    
    def divModr(self, value, cell):
        quotient, remainder, temp0, temp1, temp2, temp3 = self.malloc(6)
        self.set(temp3, value, reset=False)
        self.copy(cell, temp2, reset=False)
        self.goto(temp1)
        self.algorithm("divMod")
        self.pointer = temp0
        self.free(4)
        return quotient, remainder


    # Logic

    def not_(self, cell):
        result, temp = self.malloc(2)
        self.copy(cell, result, reset=False)
        self.goto(temp)
        self.algorithm("not")
        self.free()
        return result

    def and_(self, cell1, cell2):
        result, temp1, temp2 = self.malloc(3)
        self.copy(cell1, temp1)
        self.copy(cell2, temp2)
        self.goto(temp1)
        self.algorithm("and")
        self.pointer = temp2
        self.free(2)
        return result

    def or_(self, cell1, cell2):
        result, temp1, temp2 = self.malloc(3)
        self.copy(cell1, temp1)
        self.copy(cell2, temp2)
        self.goto(temp1)
        self.algorithm("or")
        self.pointer = temp2
        self.free(2)
        return result


    # Comparison

    def eqVar(self, cell1, cell2):
        result, temp = self.malloc(2)
        self.copy(cell1, result)
        self.copy(cell2, temp)
        self.goto(result)
        self.algorithm("eqVar")
        self.pointer = temp
        self.free()
        return result

    def eq(self, cell, value):
        if type(value) == str:
            value = ord(value)
        result, temp = self.malloc(2)
        self.copy(cell, temp, reset=False)
        self.dec(temp, value)
        self.goto(temp)
        self.algorithm("eq")
        self.free()
        return result

    def neqVar(self, cell1, cell2):
        result, temp1, temp2 = self.malloc(3)
        self.copy(cell1, temp1, reset=False)
        self.copy(cell2, temp2, reset=False)
        self.goto(temp1)
        self.algorithm("neqVar")
        self.pointer = temp2
        self.free(2)
        return result

    def neq(self, cell, value):
        if type(value) == str:
            value = ord(value)
        result, temp = self.malloc(2)
        self.copy(cell, temp, reset=False)
        self.dec(temp, value)
        self.goto(temp)
        self.algorithm("neq")
        self.free()
        return result

    def gtl(self, cell, value):
        result, temp1, temp2, temp3, temp4, temp5 = self.malloc(6)
        self.set(temp1, value, reset=False)
        self.copy(cell, temp2, reset=False)
        self.goto(temp3)
        self.algorithm("gt")
        self.free(5)
        return result

    def gtr(self, value, cell):
        result, temp1, temp2, temp3, temp4, temp5 = self.malloc(6)
        self.copy(cell, temp1, reset=False)
        self.set(temp2, value, reset=False)
        self.goto(temp3)
        self.algorithm("gt")
        self.free(5)
        return result

    def gtVar(self, cell1, cell2):
        result, temp1, temp2, temp3, temp4, temp5 = self.malloc(6)
        self.copy(cell2, temp1, reset=False)
        self.copy(cell1, temp2, reset=False)
        self.goto(temp3)
        self.algorithm("gt")
        self.free(5)
        return result
    
    def ltVar(self, cell1, cell2):
        result, temp1, temp2, temp3, temp4, temp5 = self.malloc(6)
        self.copy(cell2, temp1, reset=False)
        self.copy(cell1, temp2, reset=False)
        self.goto(temp3)
        self.algorithm("lt")
        self.free(5)
        return result

    def ltl(self, cell, value):
        result, temp1, temp2, temp3, temp4, temp5 = self.malloc(6)
        self.set(temp1, value, reset=False)
        self.copy(cell, temp2, reset=False)
        self.goto(temp3)
        self.algorithm("lt")
        self.free(5)
        return result

    def ltr(self, value, cell):
        result, temp1, temp2, temp3, temp4, temp5 = self.malloc(6)
        self.copy(cell, temp1, reset=False)
        self.set(temp2, value, reset=False)
        self.goto(temp3)
        self.algorithm("lt")
        self.free(5)
        return result

    def gtEqVar(self, cell1, cell2):
        result, temp1, temp2, temp3, temp4, temp5 = self.malloc(6)
        self.copy(cell2, temp1, reset=False)
        self.copy(cell1, temp2, reset=False)
        self.goto(temp3)
        self.algorithm("gtEq")
        self.free(5)
        return result

    def gtEql(self, cell, value):
        result, temp1, temp2, temp3, temp4, temp5 = self.malloc(6)
        self.set(temp1, value, reset=False)
        self.copy(cell, temp2, reset=False)
        self.goto(temp3)
        self.algorithm("gtEq")
        self.free(5)
        return result

    def gtEqr(self, value, cell):
        result, temp1, temp2, temp3, temp4, temp5 = self.malloc(6)
        self.copy(cell, temp1, reset=False)
        self.set(temp2, value, reset=False)
        self.goto(temp3)
        self.algorithm("gtEq")
        self.free(5)
        return result 
    
    def ltEqVar(self, cell1, cell2):
        result, temp1, temp2, temp3, temp4, temp5 = self.malloc(6)
        self.copy(cell2, temp1, reset=False)
        self.copy(cell1, temp2, reset=False)
        self.goto(temp3)
        self.algorithm("ltEq")
        self.free(5)
        return result

    def ltEql(self, cell, value):
        result, temp1, temp2, temp3, temp4, temp5 = self.malloc(6)
        self.set(temp1, value, reset=False)
        self.copy(cell, temp2, reset=False)
        self.goto(temp3)
        self.algorithm("ltEq")
        self.free(5)
        return result

    def ltEqr(self, value, cell):
        result, temp1, temp2, temp3, temp4, temp5 = self.malloc(6)
        self.copy(cell, temp1, reset=False)
        self.set(temp2, value, reset=False)
        self.goto(temp3)
        self.algorithm("ltEq")
        self.free(5)
        return result 


    # Control Flow

    def if_(self, cell, do):
        temp = self.malloc()
        self.copy(cell, temp, reset=False)
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
        self.copy(cell, temp1, reset=False)
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
        self.copy(cond(), temp)
        self.loadMemState(memState)
        self.goto(temp)
        self.code += "["
        do()
        self.loadMemState(memState)
        self.copy(cond(), temp)
        self.loadMemState(memState)
        self.goto(temp)
        self.code += "]"
        self.free()

    def for_(self, start, cond, step, do):
        cell, temp = self.malloc(2)
        start(param=cell)
        memState = self.saveMemState()
        self.copy(cond(param=cell), temp)
        self.loadMemState(memState)
        self.goto(temp)
        self.code += "["
        do(param=cell)
        step(param=cell)
        self.loadMemState(memState)
        self.copy(cond(param=cell), temp)
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
        def start(param):
            self.set(param, 0)
        def cond(param):
            return self.neq(param, self.length(arr))
        def step(param):
            self.inc(param)
        self.for_(start, cond, step, do)


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
        self.goto(self.index(arr, 0))
        self.algorithm("printArr")
        self.pointer = self.arrAccessCell(arr, 0)
        return arr

    def input(self):
        result, newline = self.malloc(2)
        self.goto(result)
        self.code += ","
        self.goto(newline)
        self.code += ","
        self.free(reset=True)
        return result

    def inputArr(self, len_=4):
        result = self.mallocArr(len_)
        self.set(self.arrAccessCell(result, 3), len_, reset=False)
        self.algorithm("inputArr", 0)
        self.code += (len_) * "+"
        self.algorithm("inputArr", 1)
        self.code += (len_) * "+"
        self.algorithm("inputArr", 2)
        self.reset(self.index(result, len_-1))
        return result
    

    # Arrays

    def resetArr(self, arr):
        self.set(self.arrAccessCell(arr, 0), self.length(arr))
        self.algorithm("resetArr")
        self.pointer = self.index(arr, self.length(arr)-1)
        return arr

    def setArr(self, arr, values, reset=True):
        for i, value in enumerate(values):
            self.set(self.index(arr, i), value, reset=reset)
        return arr

    def copyArr(self, arr1, arr2, reset=True):
        if reset:
            self.resetArr(arr2)
        self.set(self.arrAccessCell(arr1, 1), self.length(arr1))
        self.set(self.arrAccessCell(arr1, 0), self.length(arr1))
        self.goto(self.arrAccessCell(arr1, 0))
        self.algorithm("copyArr", 0)
        self.gotoRel(self.index(arr2, 0) - self.index(arr1, 0) + 3)
        self.algorithm("copyArr", 1)
        self.gotoRel(-(self.index(arr2, 0) - self.index(arr1, 0) + 3))
        self.algorithm("copyArr", 2)
        self.pointer = self.arrAccessCell(arr1, 1)
        return arr2

    def getIndex(self, arr, index):
        result = self.malloc()
        temp0, temp1, temp2, temp3 = list(range(min(self.get(arr)) - 4, min(self.get(arr))))
        self.copy(index, temp1, reset=False)
        self.goto(temp1)
        self.algorithm("getIndex")
        self.pointer = temp3
        self.move(temp0, result)
        return result

    def setIndex(self, arr, index, value):
        temp0, temp1, temp2, temp3 = list(range(self.index(arr, 0) - 4, self.index(arr, 0)))
        self.copy(index, temp1, reset=False)
        self.goto(temp1)
        self.algorithm("setIndex", 0)
        self.setRel(value)
        self.algorithm("setIndex", 1)
        self.pointer = temp2
        return arr

    def setIndexVar(self, arr, index, data):
        temp0, temp1, temp2, temp3 = list(range(self.index(arr, 0) - 4, self.index(arr, 0)))
        self.copy(index, temp1, reset=False)
        self.copy(data, temp3, reset=False)
        self.goto(temp1)
        self.algorithm("setIndexVar")
        self.pointer = temp2
        return arr


    # Datatype Conversion

    def toInt(self, arr):
        temp = self.mallocArr(4)
        self.copyArr(arr, temp, reset=False)
        self.goto(self.index(temp, 0))
        self.algorithm("toInt")
        self.freeArr(temp)
        result = self.malloc()
        return result
    
    def toDigit(self, cell):
        return self.sub(cell, ord("0"))

    def toArr(self, cell):
        result = self.mallocArr(4)
        self.copy(cell, self.arrAccessCell(result, 3), reset=False)
        self.goto(self.arrAccessCell(result, 2))
        self.algorithm("toArr")
        self.pointer = self.index(result, 0)
        return result

    def toChr(self, cell):
        return self.add(cell, ord("0"))
    

    ## Big Number Operations

    # Cell Management

    def resetBig(self, big):
        for i in range(self.length(big)):
            self.reset(self.index(big, i))

    def setBig(self, big, value, reset=True):
        remainder = value
        for i in range(self.length(big)):
            print(self.index(big, i))
            self.set(self.index(big, i), remainder // 256 ** (self.length(big) - 1 - i), reset=reset)
            remainder = remainder % 256 ** (self.length(big) - 1 - i)