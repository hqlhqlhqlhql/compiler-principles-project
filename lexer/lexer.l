%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int line_num = 1;

void print_token(const char* type, const char* value);
%}

%option noyywrap

/* 状态定义，用于处理多行注释 */
%x COMMENT

%%

"//"              { while(input() != '\n'); line_num++; }
"/*"              { BEGIN(COMMENT); }
<COMMENT>"*/"     { BEGIN(INITIAL); }
<COMMENT>\n       { line_num++; }
<COMMENT>.        { }

"const"           { print_token("KEYWORD", yytext); }
"int"             { print_token("KEYWORD", yytext); }
"float"           { print_token("KEYWORD", yytext); }
"void"            { print_token("KEYWORD", yytext); }
"if"              { print_token("KEYWORD", yytext); }
"else"            { print_token("KEYWORD", yytext); }
"while"           { print_token("KEYWORD", yytext); }
"break"           { print_token("KEYWORD", yytext); }
"continue"        { print_token("KEYWORD", yytext); }
"return"          { print_token("KEYWORD", yytext); }

[a-zA-Z_][a-zA-Z0-9_]*   { print_token("IDENTIFIER", yytext); }

0[xX][0-9a-fA-F]+        { print_token("HEX_CONST", yytext); }
0[0-7]*                   { print_token("OCT_CONST", yytext); }
[1-9][0-9]*               { print_token("DEC_CONST", yytext); }

[0-9]+\.[0-9]*([eE][+-]?[0-9]+)?   { print_token("FLOAT_CONST", yytext); }
[0-9]*\.[0-9]+([eE][+-]?[0-9]+)?   { print_token("FLOAT_CONST", yytext); }
[0-9]+[eE][+-]?[0-9]+              { print_token("FLOAT_CONST", yytext); }

"<="              { print_token("OP", yytext); }
">="              { print_token("OP", yytext); }
"=="              { print_token("OP", yytext); }
"!="              { print_token("OP", yytext); }
"&&"              { print_token("OP", yytext); }
"||"              { print_token("OP", yytext); }
"+"               { print_token("OP", yytext); }
"-"               { print_token("OP", yytext); }
"*"               { print_token("OP", yytext); }
"/"               { print_token("OP", yytext); }
"%"               { print_token("OP", yytext); }
"<"               { print_token("OP", yytext); }
">"               { print_token("OP", yytext); }
"!"               { print_token("OP", yytext); }
"="               { print_token("OP", yytext); }

"("               { print_token("SEP", yytext); }
")"               { print_token("SEP", yytext); }
"["               { print_token("SEP", yytext); }
"]"               { print_token("SEP", yytext); }
"{"               { print_token("SEP", yytext); }
"}"               { print_token("SEP", yytext); }
","               { print_token("SEP", yytext); }
";"               { print_token("SEP", yytext); }

[ \t\r]+          { }
\n                { line_num++; }
.                 { fprintf(stderr, "Line %d: Unexpected character: %s\n", line_num, yytext); }

%%

void print_token(const char* type, const char* value) {
    printf("%-4d | %-12s | %s\n", line_num, type, value);
}
