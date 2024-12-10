from bfcompiler import *

bf = bf_compiler()

LENGTH = 7

# Definiere die Liste
bf.defArr("list", LENGTH)

# Nehme eine Zahl Eingabe für jede Zelle in der Liste
def getInput(param):
    bf.move(bf.toInt(bf.inputArr()), param)
    
bf.foreach("list", getInput)

bf.printStr("Sortiert...\n")

# Bildet eine for-Schleife (i = 0, i <= LENGTH-2, i++)
bf.def_("temp")
def zeroStart(param):
    bf.set(param, 0)
    
def lenListCond(param):
    return bf.not_(bf.gt(param, LENGTH-2))
    
def checkSort(param):
    # Sortier Helferfunktion. Tauscht zwei nebeneinanderliegende Zellen in der Liste
    def sort():
        bf.move(bf.getIndex("list", bf.add(param, 1)), "temp")
        bf.setIndexVar("list", bf.add(param, 1), bf.getIndex("list", param))
        bf.setIndexVar("list", param, "temp")
        
    # Prüft, ob die Zellen getauscht werden sollen
    bf.if_(bf.gtVar(bf.getIndex("list", param), bf.getIndex("list", bf.add(param, 1))), sort)
    bf.inc(param)

# Geht die Liste LENGTH-2 mal durch
def sortCycle(param):
    bf.for_(zeroStart, lenListCond, checkSort)
    bf.inc(param)

bf.for_(zeroStart, lenListCond, sortCycle)

# Schleife, um alle Zahlen auszugeben
def printItem(param):
    bf.printArr(bf.toArr(param))
    bf.printStr(" ")

bf.foreach("list", printItem)

bf.result("bubblesort")
