#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TAPE_SIZE 30000

unsigned char tape[TAPE_SIZE];
int pointer;

int main(int argc, char* argv[]){
	if (argc < 2){
		printf("Please provide a file\n");
		return -1;
	}
	
	memset(tape, 0, TAPE_SIZE);	
	pointer = (TAPE_SIZE / 2);

	FILE* file = fopen(argv[1], "rb");
	if (file == NULL){
		printf("File not found\n");
		return -1;
	}

	fseek(file, 0, SEEK_END);
	int instrc = ftell(file)+1;
	fseek(file, 0, SEEK_SET);

	char*  instrv = malloc(instrc * sizeof(char));
	fread(instrv, 1, instrc, file);
	fclose(file);

	for (int i = 0; i < instrc-1; i++){
		switch(instrv[i]){
			case '+':
				tape[pointer]++;
				break;
			case '-':
				tape[pointer]--;
				break;
			case '<':
				pointer--;
				break;
			case '>':
				pointer++;
				break;
			case '.':
				printf("%c", tape[pointer]);
				break;
			case ',':
				tape[pointer] = getchar();
				break;
			case '[':
				if (tape[pointer] == 0){
					int wraps = 1;
					while (wraps != 0){
						i++;
						if (instrv[i] == '['){
							wraps++;
						}
						else if (instrv[i] == ']'){
							wraps--;
						}
					}
				}
				break;
			case ']':
				if (tape[pointer] != 0){
					int wraps = 1;
					while (wraps != 0){
						i--;
						if (instrv[i] == ']'){
							wraps++;
						}
						else if (instrv[i] == '['){
							wraps--;
						}
	
					}
				}
				break;
		}
	}
	free(instrv);
	printf("\n");
	if (argc == 3){
		printf("[DEBUG] Value at cell index %d: %d\n", atoi(argv[2]), tape[(int)(TAPE_SIZE / 2) + atoi(argv[2])]);
		printf("[DEBUG] Pointer at cell index %d\n", pointer - (int)(TAPE_SIZE / 2));
	}
	return 1;
}
