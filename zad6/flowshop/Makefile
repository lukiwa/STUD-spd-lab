CC=g++
CC_ARGS=-std=c++2a -fconcepts -O3
LIBS=-lgecodekernel -lgecodesupport -lgecodesearch -lgecodeint -lgecodegist -lgecodeminimodel


a.out: main.cpp tasks.hpp allocate_on_all_machines_after_first.hpp branch_on_order_and_starts.hpp johnson.hpp
	${CC} ${CC_ARGS} main.cpp -o a.out ${LIBS}
