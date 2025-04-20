from math import log
from typing import Tuple, Iterable, Callable, Union, Optional, Literal

ARRAY_ACCESS_CELL_COUNT = 4

Cell = Union[int, str]
Int = Cell
Char = Cell
Array = Union[Tuple[int, int], str]
String = Array
Big = Union[Array, Cell]
Multi_Cell = Union[Array, Cell]
Object = Union[Cell, Array, Big]
Set_Mode = Literal["NORMAL", "LEFT", "RIGHT"]

class bf_compiler:
    def __init__(self):
        self.code = ""
        self.pointer = 0
        self.vars = {}
        self.used_mem = 0
        self.used_temp = 0
        self.reserved = []

    def result(self, filename : str, trimmed : bool = True) -> str:
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
            

    def algorithm(self, filename : str, part : int = 0):
        file = open(f"algorithms/{filename}.bf", "r")
        self.code += file.readlines()[part].strip()
        file.close()


    # Variable Access

    def get(self, obj : Object) -> Optional[Object]:
        if type(obj) != str:
            return obj
        if obj not in self.vars:
            return None
        return self.vars[obj]

    def index(self, obj : Object, index : int) -> Cell:
        obj = self.get(obj)
        if type(obj) == int:
            return obj + index
        return obj[0] + index
    
    def length(self, obj : Object) -> int:
        obj = self.get(obj)
        if type(obj) == int:
            return 1
        return obj[1]

    def isTemp(self, obj : Object) -> bool:
        obj = self.get(obj)
        if type(obj) == int:
            return obj < 0
        return obj[0] < 0
 
    def overlap(self, obj1 : Object, obj2 : Object) -> bool:
        obj1 = self.get(obj1) if type(self.get(obj1)) == tuple else (self.get(obj1), 1)
        obj2 = self.get(obj2) if type(self.get(obj2)) == tuple else (self.get(obj2), 1)
        end1 = obj1[0] + obj1[1]
        end2 = obj2[0] + obj2[1] 
        return obj1[0] < end2 and obj2[0] < end1
    
    def bigReqLength(self, value : int) -> int:
        if value == 0:
            return 1
        return int(log(value, 256) + 1)


    # Memory Allocation

    def def_(self, name : str, value : Union[int, str] = 0) -> Cell:
        if type(value) == str:
                value = ord(value)
        free = self.used_mem
        self.vars[name] = free
        self.used_mem += 1
        if value != 0:
            self.set(free, value, reset=False, mode="RIGHT")
        return free

    def defArr(self, name : str, values : Union[int, Iterable[int], str]) -> Multi_Cell:
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
            self.setArr(free, values, reset=False, mode="RIGHT")
        return free
    
    def defBig(self, name : str, size : int, value : int = 0) -> Big:
        free = (self.used_mem + ARRAY_ACCESS_CELL_COUNT, size)
        self.used_mem += size + ARRAY_ACCESS_CELL_COUNT
        self.vars[name] = free
        if value != 0:
            self.setBig(free, value, reset=False, mode="LEFT")
        return free

    def malloc(self, num : int = 1) -> Tuple[Cell, ...]:
        if num == 1:
            free = -(self.used_temp + 1)
        else:
            free = tuple(range(-(self.used_temp + 1), -(self.used_temp + 1 + num), -1))
        self.used_temp += num
        return free

    def memMove(self, obj1 : Object, obj2 : Object, negate : bool = False):
        if type(self.get(obj1)) == int:
            if self.get(obj1) < 0 and obj1 not in self.reserved:
                self.move(obj1, obj2, reset=False, negate=negate)
            else:
                self.copy(obj1, obj2, reset=False, negate=negate)
        elif type(self.get(obj1)) == tuple and not negate and obj1 not in self.reserved:
            if self.get(obj1)[0] < 0:
                self.moveArr(obj1, obj2, reset=False)
            else:
                self.copyArr(obj1, obj2, reset=False)

    def mallocMap(self, map : Tuple[Union[Object, None, Tuple[None]], ...], 
            additional_cells : Tuple[Object, ...] = tuple()) -> Tuple[Union[Object, None]]:
        freed = []
        for obj in additional_cells + map[::-1]:
            if obj == None or (type(obj) == tuple and tuple[0] == None):
                continue
            if obj in self.reserved:
                break
            if type(self.get(obj)) == int and self.get(obj) < 0 and obj not in freed: 
                self.free()
                freed += [obj]
            elif type(self.get(obj)) == tuple and self.get(obj)[0] < 0 and obj not in freed:
                self.freeArr(obj)
                freed += [obj]

        temp = []
        for obj in map:
            if obj == None or type(self.get(obj)) == int:
                temp += [self.malloc()]
            elif type(self.get(obj)) == tuple:
                temp += [self.mallocArr(self.length(obj))]

        tasks = [obj for obj in map if obj != None and obj != (None,)]
        while tasks:
            for i, obj in enumerate(map):
                if obj == None or (type(obj) == tuple and tuple[0] == None):
                    continue
                if obj == temp[i]:
                    if obj in tasks:
                        tasks.remove(obj)
                    continue
                free = True
                for task in tasks:
                    if self.overlap(task, temp[i]):
                        free = False
                        break
                if free and obj in tasks:
                    self.memMove(obj, temp[i])
                    tasks.remove(obj)
        
        if len(temp) == 1:
            return temp[0]
        return temp

    def mallocArr(self, len_ : int) -> Multi_Cell:
        free = (-(self.used_temp + len_), len_)
        self.used_temp += len_ + ARRAY_ACCESS_CELL_COUNT
        return free

    def arrAccessCell(self, obj : Multi_Cell, index : int) -> Cell:
        return self.get(obj)[0] - index - 1

    def free(self, num : int = 1, reset : bool = False):
        if reset:
            for cell in range(-self.used_temp, -self.used_temp + num):
                self.reset(cell)
        self.used_temp -= num

    def freeArr(self, arr : Multi_Cell, reset : bool = False):
        if reset:
            self.resetArr(arr)
        self.used_temp -= arr[1] + ARRAY_ACCESS_CELL_COUNT

    def saveMemState(self) -> int:
        return self.used_temp

    def loadMemState(self, memState : int):
        self.free(self.used_temp - memState, reset=True)


    # Cell Management

    def goto(self, cell : Cell):
        cell = self.get(cell)
        diff = cell - self.pointer
        self.pointer = cell
        if diff > 0:
            self.code += diff * ">"
        else:
            self.code += -diff * "<"

    def gotoRel(self, diff : int):
        if diff > 0:
            self.code += diff * ">"
        else:
            self.code += -diff * "<"

    def reset(self, cell : Cell):
        self.goto(cell)
        self.code += "[-]"

    def set(self, cell : Cell, value : Union[int, str], reset : bool = True, mode : Set_Mode = "NORMAL"):
        if type(value) == str:
            value = ord(value)
        self.goto(cell)
        if reset:
            self.reset(cell)
        if mode == "NORMAL":
            if value < 128:
                self.code += value * "+"
            else:
                self.code += (256 - value) * "-"
        else:
            self.algorithm("setLeft" if mode == "LEFT" else "setRight", value)
    
    def setRel(self, value : Union[int, str], mode : Set_Mode):
        if type(value) == str:
            value = ord(value)
        self.algorithm("setLeft" if mode == "LEFT" else "setRight", value)

    def move(self, from_ : Cell, to : Cell, reset : bool = True, negate : bool = False):
        if reset: 
            self.reset(to)
        self.goto(from_)
        self.code += "[-"
        if negate:
            self.dec(to)
        else:
            self.inc(to)
        self.goto(from_)
        self.code += "]"

    def copy(self, from_ : Cell, to : Cell, reset : bool = True, negate : bool = False, to_mem : bool = False):
        if to_mem and self.isTemp(from_):
            self.move(from_, to, reset=reset, negate=negate)
            self.free()
            return
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

    def inc(self, cell : Cell, value : int = 1, mode : Set_Mode = "NORMAL"):
        self.goto(cell)
        self.setRel(value, mode=mode)

    def dec(self, cell : Cell, value : int = 1, mode : Set_Mode = "NORMAL"):
        self.goto(cell)
        self.setRel(-value, mode=mode)


    # Arithmetic

    def addVar(self, cell1 : Cell, cell2 : Cell) -> Cell:
        result = self.mallocMap((cell1,), additional_cells=(cell2,))
        self.memMove(cell2, result)
        return result

    def add(self, cell : Cell, value : int) -> Cell:
        result = self.mallocMap((cell,))
        self.inc(result, value)
        return result

    def subVar(self, cell1 : Cell, cell2 : Cell) -> Cell:
        result = self.mallocMap((cell1,), additional_cells=(cell2,))
        self.memMove(cell2, result, negate=True)
        return result

    def subl(self, cell : Cell, value : int) -> Cell:
        result, temp = self.mallocMap((cell, None))
        self.dec(result, value, mode="LEFT")
        self.free()
        return result

    def subr(self, value : int, cell : Cell) -> Cell:
        result, temp = self.mallocMap((None, None))
        self.set(result, value, reset=False, mode="LEFT")
        self.memMove(cell, result, negate=True)
        self.free()
        return result
    
    def mulVar(self, cell1 : Cell, cell2 : Cell) -> Cell:
        result, temp1, temp2 = self.mallocMap((None, cell1, cell2))
        self.goto(temp1)
        self.algorithm("mul")
        self.pointer = temp2
        self.free(2)
        return result

    def mul(self, cell : Cell, value : int) -> Cell:
        result, temp1, temp2, temp3 = self.mallocMap((None, cell, None, None))
        self.set(temp2, value, reset=False, mode="LEFT")
        self.goto(temp1)
        self.algorithm("mul")
        self.pointer = temp2
        self.free(3)
        return result

    def divModVar(self, cell1 : Cell, cell2 : Cell) -> Tuple[Cell, Cell]:
        quotient, remainder, temp0, temp1, temp2, temp3 = self.mallocMap((None, None, None, None, cell2, cell1))
        self.goto(temp1)
        self.algorithm("divMod")
        self.pointer = temp0
        self.free(4)
        return quotient, remainder

    def divModl(self, cell : Cell, value : int) -> Tuple[Cell, Cell]:
        quotient, remainder, temp0, temp1, temp2, temp3 = self.mallocMap((None, None, None, None, None, cell))
        self.set(temp2, value, reset=False, mode="RIGHT")
        self.goto(temp1)
        self.algorithm("divMod")
        self.pointer = temp0
        self.free(4)
        return quotient, remainder
    
    def divModr(self, value : int, cell : Cell) -> Tuple[Cell, Cell]:
        quotient, remainder, temp0, temp1, temp2, temp3 = self.mallocMap((None, None, None, None, cell, None))
        self.set(temp3, value, reset=False, mode="RIGHT")
        self.goto(temp1)
        self.algorithm("divMod")
        self.pointer = temp0
        self.free(4)
        return quotient, remainder


    # Logic

    def not_(self, cell : Cell) -> Cell:
        result, temp = self.mallocMap((cell, None))
        self.goto(temp)
        self.algorithm("not")
        self.free()
        return result

    def and_(self, cell1 : Cell, cell2 : Cell) -> Cell:
        result, temp1, temp2 = self.mallocMap((None, cell1, cell2))
        self.goto(temp1)
        self.algorithm("and")
        self.pointer = temp2
        self.free(2)
        return result

    def or_(self, cell1 : Cell, cell2 : Cell) -> Cell:
        result, temp1, temp2 = self.mallocMap((None, cell1, cell2))
        self.goto(temp1)
        self.algorithm("or")
        self.pointer = temp2
        self.free(2)
        return result


    # Comparison

    def eqVar(self, cell1 : Cell, cell2 : Cell) -> Cell:
        result, temp = self.mallocMap((cell1, cell2))
        self.goto(result)
        self.algorithm("eqVar")
        self.pointer = temp
        self.free()
        return result

    def eq(self, cell : Cell, value) -> Cell:
        if type(value) == str:
            value = ord(value)
        result, temp = self.mallocMap((None, cell))
        self.dec(temp, value, mode="RIGHT")
        self.goto(temp)
        self.algorithm("eq")
        self.free()
        return result

    def neqVar(self, cell1 : Cell, cell2 : Cell) -> Cell:
        result, temp1, temp2 = self.mallocMap((None, cell1, cell2))
        self.goto(temp1)
        self.algorithm("neqVar")
        self.pointer = temp2
        self.free(2)
        return result

    def neq(self, cell : Cell, value : int) -> Cell:
        if type(value) == str:
            value = ord(value)
        result, temp = self.mallocMap((None, cell))
        self.dec(temp, value, mode="RIGHT")
        self.goto(temp)
        self.algorithm("neq")
        self.free()
        return result

    def gtVar(self, cell1 : Cell, cell2 : Cell) -> Cell:
        result, temp1, temp2, temp3, temp4, temp5 = self.mallocMap((None, cell2, cell1, None, None, None))
        self.goto(temp3)
        self.algorithm("gt")
        self.free(5)
        return result

    def gtl(self, cell : Cell, value : int) -> Cell:
        result, temp1, temp2, temp3, temp4, temp5 = self.mallocMap((None, None, cell, None, None, None))
        self.set(temp1, value, reset=False, mode="RIGHT")
        self.goto(temp3)
        self.algorithm("gt")
        self.free(5)
        return result

    def gtr(self, value, cell : Cell) -> Cell:
        result, temp1, temp2, temp3, temp4, temp5 = self.mallocMap((None, cell, None, None, None, None))
        self.set(temp2, value, reset=False, mode="LEFT")
        self.goto(temp3)
        self.algorithm("gt")
        self.free(5)
        return result
    
    def ltVar(self, cell1 : Cell, cell2 : Cell) -> Cell:
        result, temp1, temp2, temp3, temp4, temp5 = self.mallocMap((None, cell2, cell1, None, None, None))
        self.goto(temp3)
        self.algorithm("lt")
        self.free(5)
        return result

    def ltl(self, cell : Cell, value : int) -> Cell:
        result, temp1, temp2, temp3, temp4, temp5 = self.mallocMap((None, None, cell, None, None, None))
        self.set(temp1, value, reset=False, mode="RIGHT")
        self.goto(temp3)
        self.algorithm("lt")
        self.free(5)
        return result

    def ltr(self, value, cell : Cell) -> Cell:
        result, temp1, temp2, temp3, temp4, temp5 = self.mallocMap((None, cell, None, None, None, None))
        self.set(temp2, value, reset=False, mode="LEFT")
        self.goto(temp3)
        self.algorithm("lt")
        self.free(5)
        return result

    def gtEqVar(self, cell1 : Cell, cell2 : Cell) -> Cell:
        result, temp1, temp2, temp3, temp4, temp5 = self.mallocMap((None, cell2, cell1, None, None, None))
        self.goto(temp3)
        self.algorithm("gtEq")
        self.free(5)
        return result

    def gtEql(self, cell : Cell, value : int) -> Cell:
        result, temp1, temp2, temp3, temp4, temp5 = self.mallocMap((None, None, cell, None, None, None))
        self.set(temp1, value, reset=False, mode="RIGHT")
        self.goto(temp3)
        self.algorithm("gtEq")
        self.free(5)
        return result

    def gtEqr(self, value, cell : Cell) -> Cell:
        result, temp1, temp2, temp3, temp4, temp5 = self.mallocMap((None, cell, None, None, None, None))
        self.set(temp2, value, reset=False, mode="LEFT")
        self.goto(temp3)
        self.algorithm("gtEq")
        self.free(5)
        return result
    
    def ltEqVar(self, cell1 : Cell, cell2 : Cell) -> Cell:
        result, temp1, temp2, temp3, temp4, temp5 = self.mallocMap((None, cell2, cell1, None, None, None))
        self.goto(temp3)
        self.algorithm("ltEq")
        self.free(5)
        return result

    def ltEql(self, cell : Cell, value : int) -> Cell:
        result, temp1, temp2, temp3, temp4, temp5 = self.mallocMap((None, None, cell, None, None, None))
        self.set(temp1, value, reset=False, mode="RIGHT")
        self.goto(temp3)
        self.algorithm("ltEq")
        self.free(5)
        return result

    def ltEqr(self, value, cell : Cell) -> Cell:
        result, temp1, temp2, temp3, temp4, temp5 = self.mallocMap((None, cell, None, None, None, None))
        self.set(temp2, value, reset=False, mode="LEFT")
        self.goto(temp3)
        self.algorithm("ltEq")
        self.free(5)
        return result


    # Control Flow

    def if_(self, cell : Cell, do : Callable[[], None]):
        temp = self.mallocMap((cell,))
        self.goto(temp)
        self.code += "["
        memState = self.saveMemState()
        do()
        self.loadMemState(memState)
        self.reset(temp)
        self.code += "]"
        self.free()

    def ifelse(self, cell : Cell, ifDo : Callable[[], None], elseDo : Callable[[], None]):
        temp1, temp2 = self.mallocMap((cell, None))
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
    
    def while_(self, cond : Callable[[], Cell], do : Callable[[], None]):
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

    def for_(self, start : Callable[[Cell], None], cond : Callable[[Cell], None], 
             step : Callable[[Cell], None], do : Callable[[Cell], None]):
        cell, temp = self.malloc(2)
        self.reserved += [cell]
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
        self.reserved.remove(cell)
        self.free(reset=True)

    def forever(self, do : Callable[[], None]):
        temp = self.malloc()
        self.set(temp, 1, reset=False)
        self.goto(temp)
        self.code += "["
        memState = self.saveMemState()
        do()
        self.loadMemState(memState)
        self.goto(temp)
        self.code += "]"
        self.free()

    def foreach(self, arr : Multi_Cell, do : Callable[[Cell], None]):
        temp = self.malloc()
        self.reserved += [temp]
        self.set(self.arrAccessCell(arr, 3), self.length(arr), reset=False, mode="RIGHT")
        self.goto(self.arrAccessCell(arr, 3))
        self.algorithm("foreach", 0)
        self.setRel(self.length(arr)-1, mode="LEFT")
        self.algorithm("foreach", 1)
        self.pointer = self.arrAccessCell(arr, 1)
        self.move(self.arrAccessCell(arr, 1), temp)
        memState = self.saveMemState()
        do(param=temp)
        self.loadMemState(memState)
        self.goto(self.arrAccessCell(arr, 3))
        self.algorithm("foreach", 2)
        self.reserved.remove(temp)
        self.free()

    # IO

    def print(self, cell : Char, clean : bool = False):
        self.goto(cell)
        self.code += "."
        if clean and self.isTemp(cell) and cell not in self.reserved:
            self.free(reset=True)

    def printArr(self, string : String, clean : bool = False):
        self.goto(self.index(string, 0))
        self.algorithm("printArr")
        self.pointer = self.arrAccessCell(string, 0)
        if clean and self.isTemp(string) and string not in self.reserved:
            self.freeArr(string, reset=True) 

    def printStr(self, string : str):
        temp1, temp2 = self.malloc(2)
        lastchar = 0
        for char in string:
            diff = ord(char) - lastchar
            lastchar = ord(char)
            self.goto(temp1)
            self.setRel(diff, mode="LEFT")
            self.print(temp1)
        self.free()
        self.free(reset=True)

    def input(self) -> Char:
        result, newline = self.malloc(2)
        self.goto(result)
        self.code += ","
        self.goto(newline)
        self.code += ","
        self.free(reset=True)
        return result

    def inputArr(self, len_ : int = 4) -> String:
        result = self.mallocArr(len_)
        self.set(self.arrAccessCell(result, 3), len_, reset=False, mode="RIGHT")
        self.goto(self.arrAccessCell(result, 3))
        self.algorithm("inputArr", 0)
        self.setRel(len_, mode="RIGHT")
        self.algorithm("inputArr", 1)
        self.setRel(len_, mode="RIGHT")
        self.algorithm("inputArr", 2)
        self.reset(self.index(result, len_-1))
        return result
    

    # Arrays

    def resetArr(self, arr : Multi_Cell):
        self.set(self.arrAccessCell(arr, 0), self.length(arr), mode="LEFT")
        self.goto(self.arrAccessCell(arr, 0))
        self.algorithm("resetArr")
        self.pointer = self.index(arr, self.length(arr)-1)

    def setArr(self, arr : Array, values : Union[Iterable[int], str], reset : bool = True, 
               mode : Set_Mode = "NORMAL"):
        for i, value in enumerate(values):
            self.set(self.index(arr, i), value, reset=reset, mode=mode)

    def moveArr(self, arr1: Multi_Cell, arr2 : Multi_Cell, reset : bool = True):
        if reset:
            self.resetArr(arr2)
        self.set(self.arrAccessCell(arr1, 0), self.length(arr1), mode="LEFT")
        self.goto(self.arrAccessCell(arr1, 0))
        self.algorithm("moveArr", 0)
        self.gotoRel(self.index(arr2, 0) - self.index(arr1, 0) + 3)
        self.algorithm("moveArr", 1)
        self.gotoRel(-(self.index(arr2, 0) - self.index(arr1, 0) + 3))
        self.algorithm("moveArr", 2)
        self.pointer = self.index(arr1, self.length(arr1) - 1)

    def copyArr(self, arr1 : Multi_Cell, arr2 : Multi_Cell, reset : bool = True, to_mem : bool = False):
        if to_mem and self.isTemp(arr1):
            self.moveArr(arr1, arr2, reset=reset)
            self.freeArr(arr1)
            return
        if reset:
            self.resetArr(arr2)
        self.set(self.arrAccessCell(arr1, 0), self.length(arr1), mode="LEFT")
        self.set(self.arrAccessCell(arr1, 1), self.length(arr1), mode="LEFT")
        self.goto(self.arrAccessCell(arr1, 0))
        self.algorithm("copyArr", 0)
        self.gotoRel(self.index(arr2, 0) - self.index(arr1, 0) + 3)
        self.algorithm("copyArr", 1)
        self.gotoRel(-(self.index(arr2, 0) - self.index(arr1, 0) + 3))
        self.algorithm("copyArr", 2)
        self.pointer = self.arrAccessCell(arr1, 1)

    def getIndex(self, arr : Multi_Cell, index : Cell) -> Cell:
        self.memMove(index, self.arrAccessCell(arr, 0))
        self.goto(self.arrAccessCell(arr, 0))
        self.algorithm("getIndex")
        self.pointer = self.arrAccessCell(arr, 2)
        result = self.malloc()
        self.move(self.arrAccessCell(arr, 1), result, reset=False)
        return result

    def setIndex(self, arr : Multi_Cell, index : Cell, value : Union[int, str]):
        self.memMove(index, self.arrAccessCell(arr, 0))
        self.goto(self.arrAccessCell(arr, 0))
        self.algorithm("setIndex", 0)
        self.setRel(value, mode="LEFT")
        self.algorithm("setIndex", 1)
        self.pointer = self.arrAccessCell(arr, 1)

    def setIndexVar(self, arr : Multi_Cell, index : Cell, data : Cell):
        self.memMove(data, self.arrAccessCell(arr, 0))
        self.memMove(index, self.arrAccessCell(arr, 1))
        self.goto(self.arrAccessCell(arr, 1))
        self.algorithm("setIndexVar")
        self.pointer = self.arrAccessCell(arr, 2)


    # Datatype Conversion

    def toInt(self, arr : String) -> Int:
        temp = self.mallocMap((arr,))
        self.goto(self.index(temp, 0))
        self.algorithm("toInt")
        self.freeArr(temp)
        result = self.malloc()
        return result

    def toArr(self, cell : Int) -> String:
        result = self.mallocArr(4)
        self.memMove(cell, self.arrAccessCell(result, 3))
        self.goto(self.arrAccessCell(result, 2))
        self.algorithm("toArr")
        self.pointer = self.index(result, 0)
        return result
    

    ## Big Number Operations

    # Cell Management

    def setBig(self, big : Big, value : int, reset : bool = True, mode : Set_Mode = "NORMAL"):
        remainder = value
        for i in range(self.length(big)):
            self.set(self.index(big, self.length(big) - i - 1), 
                     (remainder // 256 ** (self.length(big) - 1 - i)) % 256, reset=reset, mode=mode)
            remainder = remainder % 256 ** (self.length(big) - 1 - i)
    
    def incBig(self, big : Big):
        self.set(self.arrAccessCell(big, 0), self.length(big), reset=False, mode="LEFT")
        self.goto(self.arrAccessCell(big, 0))
        self.algorithm("incBig")
        self.pointer = self.arrAccessCell(big, 1)

    def decBig(self, big : Big):
        self.set(self.arrAccessCell(big, 0), self.length(big), reset=False, mode="LEFT")
        self.goto(self.arrAccessCell(big, 0))
        self.algorithm("decBig")
        self.pointer = self.arrAccessCell(big, 1)

    # Arithmetic

    def addBigVar(self, big1 : Big, big2 : Big) -> Big:
        bigger = max(big1, big2, key=self.length)
        smaller = big1 if bigger == big2 else big2
        result = self.mallocArr(self.length(bigger))
        temp = self.mallocArr(self.length(smaller))
        self.copyArr(bigger, result, reset=False)
        self.copyArr(smaller, temp, reset=False)
        self.set(self.arrAccessCell(temp, 0), self.length(temp), reset=False, mode="LEFT")
        self.set(self.arrAccessCell(temp, 1), self.length(result), reset=False, mode="LEFT")
        self.goto(self.arrAccessCell(temp, 0))
        for i, op in enumerate([">", "<", ">", "<", ">", "<"]):
            self.algorithm("addBig", i)
            self.code += self.length(temp) * op
        self.algorithm("addBig", 6)
        self.code += self.length(temp) * ">"
        self.setRel(self.length(temp), mode="RIGHT")
        self.algorithm("addBig", 7)
        self.pointer = self.arrAccessCell(result, 3)
        self.freeArr(temp, reset=False)
        return result
    
    def addBig(self, big : Big, value : int) -> Big:
        if self.length(big) >= self.bigReqLength(value):
            result = self.mallocArr(self.length(big))
            temp = self.mallocArr(self.bigReqLength(value))
            self.copyArr(big, result, reset=False)
            self.setBig(temp, value, reset=False)
        else:
            result = self.mallocArr(self.bigReqLength(value))
            temp = self.mallocArr(self.length(big))
            self.setBig(result, value, reset=False)
            self.copyArr(big, temp, reset=False)
        self.set(self.arrAccessCell(temp, 0), self.length(temp), reset=False, mode="LEFT")
        self.set(self.arrAccessCell(temp, 1), self.length(result), reset=False, mode="LEFT")
        self.goto(self.arrAccessCell(temp, 0))
        for i, op in enumerate([">", "<", ">", "<", ">", "<"]):
            self.algorithm("addBig", i)
            self.code += self.length(temp) * op
        self.algorithm("addBig", 6)
        self.code += self.length(temp) * ">"
        self.setRel(self.length(temp), mode="RIGHT")
        self.algorithm("addBig", 7)
        self.pointer = self.arrAccessCell(result, 3)
        self.freeArr(temp, reset=False)
        return result
    
    def subBigVar(self, big1 : Big, big2 : Big) -> Big:
        result = self.mallocArr(self.length(big1))
        temp = self.mallocArr(self.length(big2))
        self.copyArr(big1, result, reset=False)
        self.copyArr(big2, temp, reset=False)
        self.set(self.arrAccessCell(temp, 0), self.length(temp), reset=False, mode="LEFT")
        self.set(self.arrAccessCell(temp, 1), self.length(result), reset=False, mode="LEFT")
        self.goto(self.arrAccessCell(temp, 0))
        for i, op in enumerate([">", "<", ">", "<", ">", "<"]):
            self.algorithm("subBig", i)
            self.code += self.length(temp) * op
        self.algorithm("subBig", 6)
        self.code += self.length(temp) * ">"
        self.setRel(self.length(temp), mode="RIGHT")
        self.algorithm("subBig", 7)
        self.pointer = self.arrAccessCell(result, 3)
        self.freeArr(temp, reset=False)
        return result
    
    def subBigl(self, big : Big, value : int) -> Big:
        result = self.mallocArr(self.length(big))
        temp = self.mallocArr(self.bigReqLength(value))
        self.copyArr(big, result, reset=False)
        self.setBig(temp, value, reset=False)
        self.set(self.arrAccessCell(temp, 0), self.length(temp), reset=False, mode="LEFT")
        self.set(self.arrAccessCell(temp, 1), self.length(result), reset=False, mode="LEFT")
        self.goto(self.arrAccessCell(temp, 0))
        for i, op in enumerate([">", "<", ">", "<", ">", "<"]):
            self.algorithm("subBig", i)
            self.code += self.length(temp) * op
        self.algorithm("subBig", 6)
        self.code += self.length(temp) * ">"
        self.setRel(self.length(temp), mode="RIGHT")
        self.algorithm("subBig", 7)
        self.pointer = self.arrAccessCell(result, 3)
        self.freeArr(temp, reset=False)
        return result
    
    def subBigr(self, value : int, big : Big) -> Big:
        result = self.mallocArr(self.bigReqLength(value))
        temp = self.mallocArr(self.length(big))
        self.setBig(result, value, reset=False)
        self.copyArr(big, temp, reset=False)
        self.set(self.arrAccessCell(temp, 0), self.length(temp), reset=False, mode="LEFT")
        self.set(self.arrAccessCell(temp, 1), self.length(result), reset=False, mode="LEFT")
        self.goto(self.arrAccessCell(temp, 0))
        for i, op in enumerate([">", "<", ">", "<", ">", "<"]):
            self.algorithm("subBig", i)
            self.code += self.length(temp) * op
        self.algorithm("subBig", 6)
        self.code += self.length(temp) * ">"
        self.setRel(self.length(temp), mode="RIGHT")
        self.algorithm("subBig", 7)
        self.pointer = self.arrAccessCell(result, 3)
        self.freeArr(temp, reset=False)
        return result

    # Temporary
    def printBig(self, big : Big):
        for i in range(self.length(big)):
            self.printArr(self.toArr(self.index(big, i)))
            self.printStr(" ")
            self.free(3, reset=True)