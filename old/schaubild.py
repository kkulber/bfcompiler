from bfcompiler import *

bf = bf_compiler()

bf.defArr("Message", "Abstraktion mit brainf*ck\n")
bf.forever(lambda: bf.printArr("Message"))

bf.result("schaubild")
