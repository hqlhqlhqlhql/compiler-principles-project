#include <stdio.h>
#include <stdlib.h>

extern int yylex(void);
extern FILE* yyin;

int main(int argc, char* argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <input_file>\n", argv[0]);
        return 1;
    }

    yyin = fopen(argv[1], "r");
    if (!yyin) {
        fprintf(stderr, "Error: Cannot open file '%s'\n", argv[1]);
        return 1;
    }

    printf("%-4s | %-12s | %s\n", "Line", "Type", "Value");
    printf("-----+--------------+----------------\n");

    yylex();

    fclose(yyin);
    return 0;
}
