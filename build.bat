@echo off
mkdir build\libs 2>nul
javac -d build src/Main.java
cd build
jar cf libs/project.jar Main.class
cd ..
echo Build completed successfully! 