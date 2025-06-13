@echo off

REM Set JAVA_HOME and add to PATH (adjust if your Java path is different)
set JAVA_HOME=C:\Program Files\Java\jdk-17 REM IMPORTANT: ADJUST THIS PATH IF YOUR JDK IS ELSEWHERE
set PATH=%JAVA_HOME%\bin;%PATH%

REM Create necessary directories
if not exist build\classes mkdir build\classes
if not exist build\libs mkdir build\libs

REM Compile Java source code
echo Compiling src\Main.java...
javac -d build\classes src\Main.java
if %errorlevel% neq 0 (
    echo ERROR: Java compilation failed!
    goto :eof
)

REM Verify Main.class was created
if not exist build\classes\Main.class (
    echo ERROR: Main.class not found in build\classes after compilation!
    goto :eof
)

REM Create the JAR file, specifying the Main-Class
REM Assumes your main class is 'Main' and is in the default package
echo Creating executable JAR file...
jar cfe build\libs\project.jar Main -C build\classes .
if %errorlevel% neq 0 (
    echo ERROR: JAR creation failed!
    goto :eof
)

echo.
echo JAR file 'project.jar' created successfully at build\libs\ 