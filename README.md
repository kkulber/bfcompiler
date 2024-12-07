# bfcompiler #

---

## Using the compiler ##

A compiler for generating brainf\_ck code. To use, include `bfcompiler` in your new python file, create a `bf_compiler` object and use it's methods. To generate, call `bf_compiler.result(string name)` (Will be saved as `generated/{name}.bf`).

## Using the interpreter ##
Compile with `gcc bfinterpreter.c -o bfinterpreter`, then use with `./bfinterpreter <FILENAME>`. It takes stdin as input but does not accept newlines as many terminals make newlines mandatory for giving stdin and this probably shouldn't be handled by the brainf\*ck developer.

## Sample programs ##
All five sample programs were generated using the compiler and contain code fragments in german. They are all written in a way that accepts numeric input up to 255, if not all three digits are used you substitute using spaces e.g `5` would be `5  `. This is because as mentioned above newlines are tricky to handle using standard input. Might be subject to change in the future.

## bfcolang (WIP) ##
A minimalistic, operator-based language for using the compiler more easily. In the works.
