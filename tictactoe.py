from bfcompiler import *

bf = bf_compiler()

WIN_POSITIONS = [0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]
EMPTY, X, O = 0, 1, 2

# Erstelle Brett
bf.defArr("board", 3*3)

# Funktion, um das Brett im vorhandenen Zustand zu malen
bf.def_("columnCounter")
def drawBoard():
    bf.reset("columnCounter")
    bf.printStr("\n")
    # Malt ein Feld, zählt die Anzahl an Spalten und geht in die nächste Zeile, wenn es drei sind
    def drawField(param):
        bf.if_(bf.eq("columnCounter", 3), lambda: (bf.reset("columnCounter"),
                                                   bf.printStr("\n------\n")))
        bf.ifelse(bf.eq(param, O), lambda: bf.printStr("O"),
                  lambda: bf.ifelse(bf.eq(param, X), lambda: bf.printStr("X"),
                                                    lambda: bf.printStr(" ")))
        bf.printStr("|")
        bf.inc("columnCounter")
    bf.foreach("board", drawField)
    bf.printStr("\n")

# Funktion die eine Eingabe nimmt
bf.def_("input")
bf.def_("valid", False)
def getBoardInput():
    bf.move(bf.sub(bf.input(), 1), "input")
    bf.set("valid", False)
    def correctRange():
        def fieldEmpty():
            # Setzt das Feld für den jetzigen Spieler
            bf.setIndexVar("board", bf.toDigit("input"), "player")
            bf.set("valid", True)
        def fieldTaken():
            bf.printStr("\nThat square is already taken.\n")
        # Prüft, ob das Feld schon belegt ist
        bf.ifelse(bf.eq(bf.getIndex("board", bf.toDigit("input")), EMPTY), fieldEmpty, fieldTaken)
    def incorrectRange():
        bf.printStr("\nPlease enter a digit between 1 and 9.\n")
    # Prüft, ob die Eingabe eine Zahl zwischen 1 und 9 ist
    bf.ifelse(bf.and_(bf.gt("input", ord("0")-1), bf.not_(bf.gt("input", ord("8")))), correctRange, incorrectRange)
    
# Funktion die prüft, ob eine der Siegerpositionen erreicht wurde
bf.def_("winner", EMPTY)
def checkWin():
    for position in WIN_POSITIONS:
        bf.if_(bf.and_(bf.and_(bf.eqVar(bf.index("board", position[0]), "player"),
                               bf.eqVar(bf.index("board", position[1]), "player")),
                               bf.eqVar(bf.index("board", position[2]), "player")), lambda: bf.setVar("winner", "player"))

# Funktion die auf ein unentschieden prüft, also ob alle Felder bedeckt sind
bf.def_("draw", False)
def checkDraw():
    bf.set("draw", True)
    def checkEmpty(param):
        bf.if_(bf.eq(param, EMPTY),lambda: bf.set("draw", False))
    bf.foreach("board", checkEmpty)
    
# Einleitungstext
bf.printStr("""
TicTacToe

Please enter a digit from 1 to 9 to place your symbol into the according space

1|2|3|
------
4|5|6|
------
7|8|9|
------
""")

# malt Brett, nimmt Eingabe und wechselt den Spieler wenn sie valide ist, bis jemand Gewinnt oder ein Unentschieden erreicht ist
bf.def_("player", X)
def loop():
    bf.ifelse(bf.eq("player", X), lambda: bf.printStr("\nX's turn!\n"), lambda: bf.printStr("\nO's turn!\n"))
    getBoardInput()
    drawBoard()
    checkWin()
    checkDraw()
    bf.if_("valid",
           lambda: bf.ifelse(bf.eq("player", X), lambda: bf.set("player", O), lambda: bf.set("player", X)))
bf.while_(lambda: bf.and_(bf.eq("winner", EMPTY), bf.eq("draw", False)), loop)

# Gibt das Ergebnis des Spiels aus
bf.ifelse(bf.eq("winner", X), lambda: bf.printStr("\n\nX wins!"),
          lambda: bf.ifelse(bf.eq("winner", O), lambda: bf.printStr("\n\nO wins!"),
                    lambda: bf.printStr("\n\\nDraw!")))

bf.result("tictactoe")
