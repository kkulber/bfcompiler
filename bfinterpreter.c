#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <unistd.h>

#define TAPE_SIZE 30000

unsigned char tape[TAPE_SIZE];
int pointer;

int main(int argc, char* argv[]){
	if (argc != 2){
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
	fgets(instrv, instrc, file); 
	fclose(file);
	
	for (int i = 0; i < instrc-1; i++){
		//usleep(20000);
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
				do{
					tape[pointer] = getchar();
				} while (tape[pointer] == '\n');
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

	printf("\n%s halted.\n", argv[1]);
	
	return 1;
}
