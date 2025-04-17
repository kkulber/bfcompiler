from sys import stdin

bytes_list = list(map(int, stdin.read().strip().split()))
decimal = 0
for i, byte in enumerate(bytes_list):
    decimal += byte * (256 ** i)
print(decimal)