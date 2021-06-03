CC=g++
CC_ARGS=-std=c++2a -fconcepts -g
LIBS=-lgecodekernel -lgecodesupport -lgecodesearch -lgecodeint -lgecodegist -lgecodeminimodel


a.out: main.cpp tasks.hpp
	${CC} ${CC_ARGS} main.cpp -o a.out ${LIBS}
