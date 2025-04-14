from tkinter import *
import sys

# Constants
SHOWN_CELL_RANGE = 4
FRAME_PAD = 15
CELL_SIZE = 50
CELL_PADX = 10
CELL_POINTER_ARROW = 8
BUTTON_PADX = 10
BUTTON_FONT = ("Arial", 15)
MAX_STEP_TIME = 999
STEP_TIME_INTEVAL = 499
MAX_STEP_SIZE = 99
STEP_SIZE_INTERVAL = 49
TITLE_FONT = ("Arial", 20)
MAX_OUTPUT_LINES = 7

# Interpreter Variables
tape = [0]
offset = 0
pointer = 0
index = 0
code = ""

# GUI
root = Tk()
root.title("Brainf*ck Visualizer")
root.resizable(False, False)

tape_focus = 0
waiting_for_input = False
running = False
step_time = IntVar()
step_size = IntVar()

left = Frame(root)
left.pack(side=LEFT, padx=FRAME_PAD, pady=FRAME_PAD, fill=Y)
right = Frame(root)
right.pack(side=LEFT, padx=FRAME_PAD, pady=FRAME_PAD, fill=Y)

# Tape Widgets
cell_frames = []
tape_frame = Frame(left)
tape_frame.pack(side=TOP)

for i in range(2 * SHOWN_CELL_RANGE + 1):
    cell_frame = Frame(tape_frame)
    cell_frame.pack(side=LEFT, padx=CELL_PADX)
    
    cell_label_container = Frame(cell_frame, width=CELL_SIZE, height=CELL_SIZE,
                                 highlightbackground="black", highlightthickness=1)
    cell_label_container.pack()
    cell_label_container.pack_propagate(False)
    
    cell_label = Label(cell_label_container)
    cell_label.pack(fill=BOTH, expand=True)
    
    cell_index = Label(cell_frame)
    cell_index.pack()
    
    cell_pointer = Canvas(cell_frame, width=CELL_SIZE, height=CELL_POINTER_ARROW)
    cell_pointer.pack()
    
    # cell_frames[i][n] => n=0 : cell_label, n=1 : pointer, n=2 : index
    cell_frames += [(cell_pointer, cell_index, cell_label)]

# Code Widget
code_text = Text(left)
code_text.pack()

def set_code(event):
    global code
    update_statistics()
    code = code_text.get("1.0", END)
    restart()
code_text.bind("<KeyRelease>", set_code)

# Insert Code from file
if len(sys.argv) == 2 and len(sys.argv[1]) > 0:
    with open(sys.argv[1]) as file:
        for line in file.readlines():
            code_text.insert(END, line)

# Control Widgets
controls = Frame(right)
controls.pack()
buttons = Frame(controls)
buttons.pack()

def start():
    global running, index, code
    if not running:
        if index >= len(code):
            reset()
        running = True
        execute_command()
        root.focus_set()
start_button = Button(buttons, text="Start", font=BUTTON_FONT, command=start)
start_button.pack(side=LEFT, padx=BUTTON_PADX)

def stop():
    global running
    running = False
stop_button = Button(buttons, text="Stop", font=BUTTON_FONT, command=stop)
stop_button.pack(side=LEFT, padx=BUTTON_PADX)

def step():
    global index, code
    if index >= len(code):
        reset()
    stop()
    step_size.set(1)
    execute_command()
step_button = Button(buttons, text="Step", font=BUTTON_FONT, command=step)
step_button.pack(side=LEFT, padx=BUTTON_PADX)

# After waiting for commands to finish, resets interpreter, statistics and output
def reset():
    global tape, offset, pointer, index, waiting_for_input
    global executed, modifications, pointer_movements, comparisons, \
           characters_output, characters_input
    tape = [0]
    offset = 0
    pointer = 0
    index = 0
    waiting_for_input = False
    executed = 0
    modifications = 0
    pointer_movements = 0
    comparisons = 0
    characters_output = 0
    characters_input = 0
    output.config(state=NORMAL)
    output.delete("1.0", END)
    output.config(state=DISABLED)
def restart():
    stop()
    root.after(step_time.get(), reset)
restart_button = Button(buttons, text="Restart", font=BUTTON_FONT, command=restart)
restart_button.pack(side=LEFT, padx=BUTTON_PADX)

step_time_scale = Scale(controls, from_=1, to=MAX_STEP_TIME, orient=HORIZONTAL,
                        tickinterval=STEP_TIME_INTEVAL, variable=step_time)
step_time_scale.pack()
step_time.set(MAX_STEP_TIME)

Label(controls, text="ms zwischen Programmschritten").pack()

step_size_scale = Scale(controls, from_=1, to=MAX_STEP_SIZE, orient=HORIZONTAL,
                        tickinterval=STEP_SIZE_INTERVAL, variable=step_size)
step_size_scale.pack()
step_size.set(1)

Label(controls, text="Befehle pro Programmschritt").pack()

# Output Widgets
output_label = Label(right, text="Output:", font=TITLE_FONT)
output_label.pack()
output_frame = Frame(right)
output_frame.pack(fill=BOTH, expand=True)
output_frame.pack_propagate(False)
output = Text(output_frame, state=DISABLED)
output.pack(fill=BOTH, expand=True)

# Statistic Widgets
executed = 0
modifications = 0
pointer_movements = 0
comparisons = 0
characters_output = 0
characters_input = 0

statistics = Frame(right)
statistics.pack(side=BOTTOM)
length_label = Label(statistics)
length_label.pack(side=BOTTOM)
executed_label = Label(statistics)
executed_label.pack(side=BOTTOM)
modifications_label = Label(statistics)
modifications_label.pack(side=BOTTOM)
pointer_movements_label = Label(statistics)
pointer_movements_label.pack(side=BOTTOM)
comparisons_label = Label(statistics)
comparisons_label.pack(side=BOTTOM)
characters_output_label = Label(statistics)
characters_output_label.pack(side=BOTTOM)
characters_input_label = Label(statistics)
characters_input_label.pack(side=BOTTOM)
cells_used_label = Label(statistics)
cells_used_label.pack(side=BOTTOM)

# Interpreter
def execute_command():
    global tape, offset, pointer, index, waiting_for_input, running
    global executed, modifications, pointer_movements, comparisons, \
           characters_output, characters_input
    
    if waiting_for_input:
        return
        
    tape_pointer = pointer + offset
    
    if code[index] in ["+", "-", "<", ">", "[", "]", ".", ","]:
        executed += 1
    
    if code[index] == "+":
        if tape[tape_pointer] == 255:
            tape[tape_pointer] = 0
        else:
            tape[tape_pointer] += 1
        modifications += 1
          
    elif code[index] == "-":
        if tape[tape_pointer] == 0:
            tape[tape_pointer] = 255
        else:
            tape[tape_pointer] -= 1
        modifications += 1
            
    elif code[index] == "<":
        if tape_pointer == 0:
            offset += 1
            tape = [0] + tape
        pointer -= 1
        pointer_movements += 1
        
    elif code[index] == ">":
        if tape_pointer == len(tape) - 1:
            tape += [0]
        pointer += 1
        pointer_movements += 1
        
    elif code[index] == "[":
        if tape[tape_pointer] == 0:
            openings = 1
            while code[index] != "]" or openings > 0:
                index += 1
                if code[index] == "[":
                    openings += 1
                elif code[index] == "]":
                    openings -= 1
        comparisons += 1
                    
    elif code[index] == "]":
        if tape[tape_pointer] != 0:
            closings = 1
            while code[index] != "[" or closings > 0:
                index -= 1
                if code[index] == "]":
                    closings += 1
                elif code[index] == "[":
                    closings -= 1
        comparisons += 1
                    
    elif code[index] == ".":
        output.config(state=NORMAL)
        output.insert(END, chr(tape[tape_pointer]))
        output.config(state=DISABLED)
        output.see(END)
        characters_output += 1
        
    elif code[index] == ",":
        update_code()
        waiting_for_input = True
        
    elif code[index] == "!":
        stop()
        
    index += 1
    
    if executed % step_size.get() == 0:
        update_tape()
        update_statistics()
        update_code()
    
    if index < len(code) and not waiting_for_input and running:
        root.after(step_time.get(), execute_command)
    else:
        update_tape()
        update_code()
        update_statistics()

# Update Tape after it changes in some way
def update_tape():
    focus_pointer = tape_focus + offset
    
    shown_cells = []
    for cell_index in range(focus_pointer - SHOWN_CELL_RANGE,
                            focus_pointer + SHOWN_CELL_RANGE + 1):
        if cell_index < 0 or cell_index >= len(tape):
            shown_cells += [0]
            continue
        shown_cells += [tape[cell_index]]
        
    for i in range(len(shown_cells)):
        cell_frames[i][0].delete(ALL)
        cell_frames[i][1].config(text=tape_focus - SHOWN_CELL_RANGE + i)
        cell_frames[i][2].config(text=shown_cells[i])
        if tape_focus - SHOWN_CELL_RANGE + i == pointer:
            cell_frames[i][0].create_line(CELL_SIZE / 2, 0, CELL_SIZE / 2,
                                          CELL_POINTER_ARROW, arrow=FIRST)

# Set the highlight in the text widget
def update_code():
    line = code[:index].count("\n") + 1
    char = index - code[:index].rfind("\n") - 2
    code_text.tag_delete("highlight")
    code_text.tag_add("highlight", f"{line}.{char}", f"{line}.{char+1}")
    code_text.tag_config("highlight", background="yellow")

# Updates statistics label
def update_statistics():
    global executed, modifications, pointer_movements, comparisons, \
           characters_output, characters_input
    
    length_label.config(text=f"""Code length: {code.count("+") + code.count("-") + code.count("<") + code.count(">") + 
                                code.count("[") + code.count("]") + code.count(".") + code.count(",")}""")
    executed_label.config(text=f"Commands executed: {executed}")
    modifications_label.config(text=f"Cells modified: {modifications}")
    pointer_movements_label.config(text=f"Pointer moved: {pointer_movements}")
    comparisons_label.config(text=f"Comparisons (with 0): {comparisons}")
    characters_output_label.config(text=f"Characters Output: {characters_output}")
    characters_input_label.config(text=f"Characters Input: {characters_input}")
    cells_used_label.config(text=f"Cells used: {len(tape)}")

# Lets you scroll the tape if code and output isnt in focus
def change_tape_focus(event):
    global tape_focus
    if root.focus_get() == code_text or root.focus_get() == output:
        return
    # For Windows
    if abs(event.delta) >= 120:
        tape_focus += event.delta // 120
    # For MacOS
    else:
        tape_focus += event.delta
    update_tape()
root.bind("<MouseWheel>", change_tape_focus)

# For Linux
def linux_inc_tape_focus(event):
    global tape_focus
    if root.focus_get() == code_text or root.focus_get() == output:
        return
    tape_focus += 1
    update_tape()
root.bind("<Button-4>", linux_inc_tape_focus)

def linux_inc_tape_focus(event):
    global tape_focus
    if root.focus_get() == code_text or root.focus_get() == output:
        return
    tape_focus -= 1
    update_tape()
root.bind("<Button-5>", linux_inc_tape_focus)

# Processes input if currently on an input command or if removing focus from text widget
def process_input(event):
    global tape, pointer, offset, waiting_for_input, running, characters_input
    if event.keysym == "Escape":
        root.focus_set()
    # Allows the use of the enter key as a line feed
    elif event.keysym == "Return":
        event.keysym_num = 10
    if event.keysym_num >= 0 and event.keysym_num <= 255 and waiting_for_input:
        tape[pointer + offset] = event.keysym_num
        waiting_for_input = False
        update_tape()
        execute_command()
        characters_input += 1
root.bind("<Key>", process_input)

# Display empty tape and statistics at start
update_tape()
update_statistics()

root.mainloop()
