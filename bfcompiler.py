from math import log

ARRAY_ACCESS_CELL_COUNT = 4
BIG_ACCESS_CELL_COUNT = 2

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

    def get(self, obj):
        if type(obj) == tuple and obj[1] == 1:
            return obj[0]
        if type(obj) != str:
            return obj
        if obj not in self.vars:
            return None
        return self.vars[obj]
    
    def get_name(self, var):
        try:
            return list(self.vars.keys())[list(self.vars.values()).index(var)]
        except:
            return None

    def index(self, obj, index):
        obj = self.get(obj)
        if type(obj) == int:
            return obj + index
        return obj[0] + index

    
    def length(self, obj):
        obj = self.get(obj)
        if type(obj) == int:
            return 1
        return obj[1]
    
    def bigReqLength(self, value):
        return int(log(value, 256) + 1)


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
        free = (self.used_mem + ARRAY_ACCESS_CELL_COUNT, length)
        self.used_mem += length + ARRAY_ACCESS_CELL_COUNT
        self.vars[name] = free
        if type(values) != int:
            self.setArr(free, values, reset=False)
        return free
    
    def defBig(self, name, size, value=0):
        if size == 1:
            return self.def_(name, value)
        free = (self.used_mem + BIG_ACCESS_CELL_COUNT, size)
        self.vars[name] = free
        self.used_mem += size + BIG_ACCESS_CELL_COUNT
        if value != 0:
            self.setBig(free, value, reset=False)
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
        self.used_temp += num + ARRAY_ACCESS_CELL_COUNT
        return free
    
    def mallocBig(self, size, num=1):
        if size == 1:
            return self.malloc(num)
        if num == 1:
            free = (-(self.used_temp + size), size)
        else:
            free = tuple((-(self.used_temp + size * i), size) for i in range(1, num + 1))
        self.used_temp += num * size + BIG_ACCESS_CELL_COUNT
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
        self.used_temp -= arr[1] + ARRAY_ACCESS_CELL_COUNT

    def freeBig(self, size, num=1, reset=False):
        if size == 1:
            self.free(num, reset=reset)
            return
        if reset:
            for cell in range(-self.used_temp, -self.used_temp + num * size):
                self.reset(cell)
        self.used_temp -= num * size + BIG_ACCESS_CELL_COUNT

    def saveMemState(self):
        return self.used_temp

    def loadMemState(self, memState):
        self.free(self.used_temp - memState, reset=True)


    # Cell Management

    def goto(self, cell):
        cell = self.get(cell)
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

    def managedWhile(self, cond, do):
        self.goto(cond())
        self.code += "["
        self.free(reset=True)
        do()
        self.goto(cond())
        self.code += "]"
        self.free(reset=True)

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
        temp = self.malloc()
        self.set(self.arrAccessCell(arr, 3), self.length(arr), reset=False)
        self.algorithm("foreach", 0)
        self.setRel(self.length(arr)-1)
        self.algorithm("foreach", 1)
        self.pointer = 2
        self.move(self.arrAccessCell(arr, 1), temp)
        memState = self.saveMemState()
        do(param=temp)
        self.loadMemState(memState)
        self.goto(self.arrAccessCell(arr, 3))
        self.algorithm("foreach", 2)


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
        self.copy(index, self.arrAccessCell(arr, 0), reset=False)
        self.goto(self.arrAccessCell(arr, 0))
        self.algorithm("getIndex")
        self.pointer = self.arrAccessCell(arr, 2)
        result = self.malloc()
        self.move(self.arrAccessCell(arr, 1), result, reset=False)
        return result

    def setIndex(self, arr, index, value):
        self.copy(index, self.arrAccessCell(arr, 0), reset=False)
        self.goto(self.arrAccessCell(arr, 0))
        self.algorithm("setIndex", 0)
        self.setRel(value)
        self.algorithm("setIndex", 1)
        self.pointer = self.arrAccessCell(arr, 1)
        return arr

    def setIndexVar(self, arr, index, data):
        self.copy(data, self.arrAccessCell(arr, 0), reset=False)
        self.copy(index, self.arrAccessCell(arr, 1), reset=False)
        self.goto(self.arrAccessCell(arr, 1))
        self.algorithm("setIndexVar")
        self.pointer = self.arrAccessCell(arr, 2)
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
            self.set(self.index(big, self.length(big) - i - 1), 
                     remainder // 256 ** (self.length(big) - 1 - i), reset=reset)
            remainder = remainder % 256 ** (self.length(big) - 1 - i)

    def moveBig(self, from_, to, reset=True):
        if reset:
            self.resetBig(to)
        for i in range(self.length(from_)):
            self.goto(self.index(from_, i))
            self.code += "[-"
            self.inc(self.index(to, i))
            self.goto(self.index(from_, i))
            self.code += "]"
        return to

    def copyBig(self, from_, to, reset=True, negate=False):
        if reset:
            self.resetBig(to)
        temp = self.mallocBig(self.length(from_))
        for i in range(self.length(from_)):
            self.goto(self.index(from_, i))
            self.code += "[-"
            if negate:
                self.dec(self.index(to, i))
            else:
                self.inc(self.index(to, i))
            self.inc(self.index(temp, i))
            self.goto(self.index(from_, i))
            self.code += "]"
            self.moveBig(temp, from_, reset=False)
        self.freeBig(self.length(from_))
        return to
    
    def incBig(self, big):
        if self.length(big) == 1:
            self.inc(big)
            return big
        self.goto(self.index(big, 0))
        for _ in range(self.length(big)-1):
            self.algorithm("incBig", 0)
        self.algorithm("incBig", 1)
        for _ in range(self.length(big)-1):
            self.algorithm("incBig", 2)
        self.pointer = self.arrAccessCell(big, 0)
        return big

    def decBig(self, big):
        if self.length(big) == 1:
            self.dec(big)
            return big
        self.goto(self.index(big, 0))
        for _ in range(self.length(big)-1):
            self.algorithm("decBig", 0)
        self.algorithm("decBig", 1)
        for _ in range(self.length(big)-1):
            self.algorithm("decBig", 2)
        self.pointer = self.arrAccessCell(big, 0)
        return big
    

    # Arithmetic

    def addBigVar(self, big1, big2):
        bigger = max(big1, big2, key=self.length)
        smaller = big1 if bigger == big2 else big2
        result = self.mallocBig(self.length(bigger))
        self.malloc()
        temp = self.mallocBig(self.length(smaller))
        self.malloc()
        self.copyBig(bigger, result, reset=False)
        self.copyBig(smaller, temp, reset=False)
        for i in range(self.length(temp)):
            current_temp = (self.index(temp, i), self.length(temp) - i)
            current_result = (self.index(result, i), self.length(result) - i)
            def cond():
                return self.neq(self.index(temp, i), 0)
            def do():
                self.decBig(current_temp)
                self.incBig(current_result)
            self.managedWhile(cond, do)
            self.move(self.index(current_temp, 0), self.index(current_temp, -3), reset=False)
            self.move(self.index(current_result, 0), self.index(current_result, -3), reset=False)
        for i in range(self.length(temp)):
            self.move(self.index(result, self.length(temp) - 4 - i), 
                      self.index(result, self.length(temp) - 1 - i), reset=False)
        self.freeBig(self.length(temp), reset=True)
        self.free(2, reset=True)
        return result

    def addBig(self, big, value):
        if self.length(big) > self.bigReqLength(value):
            result = self.mallocBig(self.length(big))
            self.malloc()
            temp = self.mallocBig(self.bigReqLength(value))
            self.malloc()
            self.copyBig(big, result, reset=False)
            self.setBig(temp, value, reset=False)
        else:
            result = self.mallocBig(self.bigReqLength(value))
            self.malloc()
            temp = self.mallocBig(self.length(big))
            self.malloc()
            self.setBig(result, value, reset=False)
            self.copyBig(big, temp, reset=False)
        for i in range(self.length(temp)):
            current_temp = (self.index(temp, i), self.length(temp) - i)
            current_result = (self.index(result, i), self.length(result) - i)
            def cond():
                return self.neq(self.index(temp, i), 0)
            def do():
                self.decBig(current_temp)
                self.incBig(current_result)
            self.managedWhile(cond, do)
            self.move(self.index(current_temp, 0), self.index(current_temp, -3), reset=False)
            self.move(self.index(current_result, 0), self.index(current_result, -3), reset=False)
        for i in range(self.length(temp)):
            self.move(self.index(result, self.length(temp) - 4 - i), 
                      self.index(result, self.length(temp) - 1 - i), reset=False)
        self.freeBig(self.length(temp), reset=True)
        self.free(2, reset=True)
        return result
    
    def decBigVar(self, big1, big2):
        result = self.mallocBig(self.length(big1))
        self.malloc()
        temp = self.mallocBig(self.length(big2))
        self.malloc()
        self.copyBig(big1, result, reset=False)
        self.copyBig(big2, temp, reset=False)
        for i in range(self.length(temp)):
            current_temp = (self.index(temp, i), self.length(temp) - i)
            current_result = (self.index(result, i), self.length(result) - i)
            def cond():
                return self.neq(self.index(temp, i), 0)
            def do():
                self.decBig(current_temp)
                self.decBig(current_result)
            self.managedWhile(cond, do)
            self.move(self.index(current_temp, 0), self.index(current_temp, -3), reset=False)
            self.move(self.index(current_result, 0), self.index(current_result, -3), reset=False)
        for i in range(self.length(temp)):
            self.move(self.index(result, self.length(temp) - 4 - i), 
                      self.index(result, self.length(temp) - 1 - i), reset=False)
        self.freeBig(self.length(temp), reset=True)
        self.free(2, reset=True)
        return result

    # Temporary
    def printBig(self, big):
        for i in range(self.length(big)):
            self.printArr(self.toArr(self.index(big, i)))
            self.printStr(" ")
            self.free(3, reset=True)