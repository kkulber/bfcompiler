# bfcompiler #
A compiler and a compiler language for creating brainf*ck (bf) code

## Installation (Linux) ##
You need `git` to clone the project and `gcc` if you want to use the interpreter.
To clone, change your working directory to the one where you want the *bfcompiler* folder to be cloned to

``` cd PROJECT_DIRECTORY_PATH ```

then, clone

``` git clone https://github.com/kkulber/bfcompiler.git ```

If you want to use the interpreter, build it using gcc. Ideally you'll name it as shown below so the shortcut script for compiling and interpreting (*run_bfcl.sh*) works. Change directory into the cloned project

``` cd bfcompiler```

and build

``` gcc bfinterpreter.c -o bfinterpreter```

## Usage ##
Write programs (Ideally in /programs, so the script works) in *bfcolang* (Tutorial below). To compile a program, run it using the *bfcolang interpreter*. It uses the compiler internally

``` python3 bfcolang.py programs/MYPROGRAM.bfcl ```

Then run it using the interpreter (Or any other exterior bf interpreter that supports either a bi-dimensional tape or tape wrapping):

``` ./bfinterpreter generated/MYPROGRAM.bf ```

To do this in one step, for example for debug purposes, use the provided bash script

``` ./run_bfcl MYPROGRAM ```

## Bfcl Tutorial ##
### Running code ###
Either write programs (ideally in the /programs directory) with the file descriptor bfcl, or use the *bfcl_shell* shell script to test syntax

### Tokens ###
The language is made up of 9 different types of *tokens*

### Integers ### 
which can be expressed using numerical characters e.g `1  20  255` (Note that for now, only numbers up to 255 are supported for writing to bf memory, due to the limitation of using single cells for variable storage)

### Characters ### 
which can be expressed using single quotes and one character between them e.g `'A'  '0'  '"'` (For now, the same limitations as for Integers apply)

### Arrays ###
a data type that can store multiple Integers, which can be expressed using dollar signs and Integers inbetween them, seperated by spaces, except the first and last element e.g `$1 2 3$  $1 20 255$  $0 0 0$`

### Strings ###
a data type that can store multiple Characters, which can be expressed using double quotes e.g `"Hello World!" "Abstraktion mit brainf*ck" "!"`

### Types ###
specifies a data type. Can be any of the following `int  char  arr  str  func`

### Operators ###
One of the following 34 operators `->, ~, ^, ., ,, !, ++, --, *!, [, *, /, %, +, -, >, <, >=, <=, │, ==, !=, &, |, =, @=, @, @>, ?, ?*, [*, ]=, >@, !?, :`. More on operators in the section for functionality

### Variables ###
Custom names for both bf memory and compiler memory. Can be any string of lowercase and uppercase letters, as well as `_` e.g `x  path  sum`. They cannot contain any of the datatypes. More on variables in the section for functionality

### Comments ###
*Any* text between hashtags will be ignores by the compiler as a comment. e.g `# This is a comment #  # I can write comments! #  ## ` (Btw, all space-like character e.g Space, Tab, Newline are ignored as well)

### Expression Control ###
There are four kinds of operators in bfcl. 

Unary operators, that take one argument e.g `++x  ."Hello World!"  !True`

Binary operators, that take two arguments e.g `x + y  list[0  be | not_be`

Ternary operators, that take three argument e.g `arr<5> @ list  list[0] = 100` 

Quaternary operators, that take four arguments e.g ` {i = 0;} : {i < 100;} : {++i;} : {.i}`

All valid operations habe a return token. Single-token expression return themselves.

Operators are handled left to right (right to left for unary operators) and have a hierachy (the hierachy will be explained in the section for functionality). The order of operation evaluation can be modified using parenthesis e.g ` 2 * (3 + 4)  !(x | y)`. Expressions are seperated using semicolons e.g `x = x + 1; .x;`

## Functions ##
Are stored as tokens and can be defined using curly brackets and expressions inside (Which also have to be structured using semicolons) e.g `{ ++i; }  { ."Hello "; .name} `. The code that you write into the file itself is also a function, namely the *main function*, internally indexed *0*;

## Functionality ##
This section focuses on all operators, what they do, what arguments they take and what they return. It's sorted into catgories based on operation presedence from first-evaluated to last-evaluated.

All parameters can also be variables containing the parameters, except if they are followed by *(lit.)*. Sometimes it can only be variables, then its followed by (var.). Both ints and chars are referred to as singles, both arrays and strings are referred to as mults

### 1. Primary Expressions ###
#### Call ####
-> func, -> int => func

Evaluates a function, a function stored in a variable or a function based on it's integer ID. Returns the function itself

#### Parameter Stack Access ####
~ int (lit.) => any

Returns a token from the parameter stack (More later) using indices with *0* being the top of the stack

#### Length ####
^ mult => int

Returns the length of an array, a string or one of the two stored in a variable

#### Get Index ####
mult [ int => single

Returns element with a specific index from a mult-type

#### Set Index ####
mult (var.) \[ int \]= single => single

Sets element with a specific index in a mult to a single. Returns the single.

### 2. Strong unary operators ###
#### Not ####
! int => int

Returns the logical not of an integer value (one for zero, zero for non-zero)

#### Increment ####
++ int => int

Increments an integer by one. Returns the integer

#### Decrement ####
-- int => int

Decrements an integer by one. Returns the integer

#### Output ####
. any => any

Prints any datatype to the console in a human readable format. Returns the printed token

#### Input ####
, type , , any (var.) => any

Requests and returns user input of a type specified directly or a using the type of a variable (especially usefor for mults of specific sizes)

### 3a. Arithmetic Operators ###
#### Product ####
int * int => int

Returns product of two integers

#### Quotient ####
int / int => int

Returns integer quotient of two integers

#### Modulus ####
int % int => int

Returns modulus of two integers

### 3b. Arithmetic Operators ###
#### Sum / Concatination ####
int + int => int

Returns the sum of two integers

#### Difference ####
int - int => int

Returns difference of two integers

### 4. Comparison Operators ###
#### Equal ####
single == single => int

Returns 1 if two singles are equal, else 0

#### Not equal ####
single != single => int

Returns 0 if two singles are equal. else 1

#### Greater than ####
int > int => int

Returns 1 if one integer is greater than another, else 0

#### Greater than or equal to ####
int >= int => int

Returns 1 if one integer is greater than or equal to another, else 0

#### Less than ####
int < int => int

Returns 1 if one integer is smaller than another, else 0

#### Less than or equal to ####
int <= int => int

Returns 1 if one integer is smaller than or equal to another, else 0

### 5a. Logical Operators ###
#### And ####
int & int => int

Returns 1 if two integers are both non-zero, else 0

### 5b. Logical Operators ###
#### Or ####
int | int => int

Returns 1 if one of two integers is non-zero, else 0

### 6. Definition and Assignement Operators ###
#### Define alias ####
any (var.) @= any_tokens => any_tokens

Defines an alias with a variable name. When using this alias in following code, it will be replaced with the tokens it was assigned. Returns these tokens

#### Define ####
type @ any (var.) => any (var.)

Defines a variable of a specified type. If its a mult type, sets size whenever a value is assigned. Returns the variable

#### Define with size ####
mult (var.) < int (lit.) >@ var => var
Defines a variable of a specified type and a specified size. Returns the variable

#### Parse ####
any @> type => any

Returns any data type interpreted as another type. Special cases are parsing integers to strings and strings to integers.

#### Assign ####
var = any => var

Assignes any data type (single to single, mult of same size to mult of same size) to variable. Returns variable

### Control flow ###
#### If ####
int ? func => int

Runs a function if an integer is non-zero. Returns the integer

#### Ifelse ####
int ? func !? func => int

Runs a function if an integer is non-zero, else runs another function. Returns the integer

#### While ####
func ?* func => 1

As long as one function returns a non-zero integer variable, runs another function. Returns 1

#### Foreach ####
mult [* func => mult 

Runs a function for each element of a mult, putting the item of the current iteration at the top of the parameter stack. Returns the mult.

#### Forever ####
!* func => 1

Runs a function indefinitely. Returns 1

#### For ####
func : func : func : func => 1

First, runs function 1, then runs function 3 and 4 while function 2 returns a non-zero integer variable. Returns 1

## Final words ##
When encountering errors, check the console, check that you didnt miss any semicolons and look at the sample programs to learn how the syntax works together
