@echo off
setlocal

set FLEX=win_flex_bison3-latest\win_flex.exe
set GCC=tdm64-gcc-10.3.0-2\bin\gcc.exe

echo [1/3] Generating lexer with Flex...
%FLEX% -o lex.yy.c lexer.l
if errorlevel 1 (
    echo Flex failed!
    exit /b 1
)

echo [2/3] Compiling...
%GCC% -o lexer.exe main.c lex.yy.c
if errorlevel 1 (
    echo Compilation failed!
    exit /b 1
)

echo [3/3] Build successful: lexer.exe
echo.
echo Usage: lexer.exe test\test1.sy
endlocal
