from bfcompiler import *

bf = bf_compiler()


# Erstellt die Variablen a, b und temp
bf.def_("a", 0)
bf.def_("b", 1)
bf.def_("temp")

# Bedingung: b >= a, also es gab noch keinen Memory Overflow
def cond():
    return bf.or_(bf.gtVar("b", "a"), bf.eqVar("b", "a"))
    
def loop():
    # Gebe a aus, Konvertiere a dafür zu einer Zeichenkette
    bf.printArr(bf.toArr("a"))
    bf.printStr(" ")
    # Addiere a und b, nutze die temp Variable als Zwischenspeicher
    bf.move("a", "temp")
    bf.move("b", "a")
    bf.move(bf.addVar("a", "temp"), "b")
    
# Starte die Schleife mit Bedingung
bf.while_(cond, loop)
# Gibt die letzte Zahl der Folge aus (mit begrenztem Sepeicher)
bf.printArr(bf.toArr("a"))

bf.result("fibonacci")