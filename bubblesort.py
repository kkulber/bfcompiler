from bfcompiler import *

bf = bf_compiler()

LENGTH = 7

# Definiere die Liste
bf.defArr("list", LENGTH)

# Nehme eine Zahl Eingabe für jede Zelle in der Liste
def getInput(cell):
    bf.move(bf.toInt(bf.inputArr()), cell)
    
bf.foreach("list", getInput)

bf.printStr("Sortiert...\n")

# Bildet eine for-Schleife (i = 0, i <= LENGTH-2, i++)
bf.def_("temp")
def zeroStart(i):
    bf.set(i, 0)
    
def lenListCond(i):
    return bf.not_(bf.gt(i, LENGTH-2))
    
def checkSort(i):
    # Sortier Helferfunktion. Tauscht zwei nebeneinanderliegende Zellen in der Liste
    def sort():
        bf.move(bf.getIndex("list", bf.add(i, 1)), "temp")
        bf.setIndexVar("list", bf.add(i, 1), bf.getIndex("list", i))
        bf.setIndexVar("list", i, "temp")
        
    # Prüft, ob die Zellen getauscht werden sollen
    bf.if_(bf.gtVar(bf.getIndex("list", i), bf.getIndex("list", bf.add(i, 1))), sort)
    bf.inc(i)

# Geht die Liste LENGTH-2 mal durch
def sortCycle(i):
    bf.for_(zeroStart, lenListCond, checkSort)
    bf.inc(i)

bf.for_(zeroStart, lenListCond, sortCycle)

# Schleife, um alle Zahlen auszugeben
def printItem(cell):
    bf.printArr(bf.toArr(cell))
    bf.printStr(" ")

bf.foreach("list", printItem)

bf.result("bubblesort")