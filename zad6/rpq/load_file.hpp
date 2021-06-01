#pragma once

#include <fstream>
#include <iostream>

#include "tasks.hpp"

Tasks load_stream(int task_no, std::istream& os)
{
    Gecode::IntArgs r_args, p_args, q_args;

    int r, p, q;
    while (os >> r >> p >> q)
    {
        r_args << r;
        p_args << p;
        q_args << q;
    }

    return Tasks(std::move(r_args), std::move(p_args), std::move(q_args));
}

Tasks load_file(const std::string& filename)
{
    std::ifstream file_stream;
    file_stream.open(filename);

    if (!file_stream)
    {
        throw std::runtime_error("Wrong filename");
    }

    file_stream.ignore(50, '\n');
    return load_stream(0, file_stream);
}
