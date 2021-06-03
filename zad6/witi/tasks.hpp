#pragma once

#include <fstream>
#include <memory>

#include <gecode/int.hh>

struct Tasks
{
public:
    Gecode::IntArgs p, w, d;


};


std::unique_ptr<Tasks> load_file(const std::string& filename)
{
    std::ifstream file(filename);
    assert(static_cast<bool>(file));

    auto result = std::make_unique<Tasks>();

    file.ignore(50, '\n');
    int pi, wi, di;
    while (file >> pi >> wi >> di)
    {
        result->p << pi;
        result->w << wi;
        result->d << di;
    }

    return result;
}
