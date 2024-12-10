from bfcompiler import *

bf = bf_compiler()

# Nehme die erste Zahl als Eingabe, speicher die übergebene Zeichenkette und diese als Zahl
bf.printStr("Bitte geben Sie die erste Zahl ein: ")
bf.defArrVar("input1", bf.inputArr())
bf.defVar("num1", bf.toInt("input1"))

# Nehme den Operator als Eingabe
bf.printStr("Bitte geben Sie den Operator ein: ")
bf.defVar("op", bf.input())

# Nehme die zweite Zahl als Eingabe
bf.printStr("Bitte geben Sie die zweite Zahl ein: ")
bf.defArrVar("input2", bf.inputArr())
bf.defVar("num2", bf.toInt("input2"))

# Erstelle eine Variable, die die Lösung speichern wird, Länge von 2 um bei Division auch den Rest zu speichern
bf.defArr("result", 2)

# Helferfunktion für das Berechnen jeder einzelnen Operation und das Speichern in die Lösungsvariable
def add():
    bf.move(bf.addVar("num1", "num2"), bf.index("result", 0))
def sub():
    bf.move(bf.subVar("num1", "num2"), bf.index("result", 0))
def mul():
    bf.move(bf.mulVar("num1", "num2"), bf.index("result", 0))
def div():
    bf.moveArr(bf.divModVar("num1", "num2"), "result")

# Prüft für jeden validen Operator, ob dieser übergeben wurde und hängt entsprechende Helferfunktion an
bf.ifelse(bf.eq("op", "+"), add,
          lambda: bf.ifelse(bf.eq("op", "-"), sub,
                            lambda: bf.ifelse(bf.eq("op", "*"), mul,
                                              lambda: bf.if_(bf.eq("op", "/"), div))))

# Gibt die Rechnung aus
bf.printArr("input1")
bf.printStr(" ")
bf.print("op")
bf.printStr(" ")
bf.printArr("input2")
bf.printStr(" = ")

# Gibt das Ergebnis aus
bf.printArr(bf.toArr(bf.index("result", 0)))

# Gibt, falls es sich um eine Division handelt, den Rest aus
bf.if_(bf.eq("op", "/"),
       lambda: (bf.printStr(" R "),
                bf.printArr(bf.toArr(bf.index("result", 1)))))

bf.result("calculator")
