CC=g++
CC_ARGS=-std=c++2a -fconcepts -g
LIBS=-lgecodekernel -lgecodesupport -lgecodesearch -lgecodeint -lgecodegist -lgecodeminimodel


a.out: main.cpp load_file.hpp tasks.hpp brancher.hpp schrage.hpp
	${CC} ${CC_ARGS} main.cpp -o a.out ${LIBS}
