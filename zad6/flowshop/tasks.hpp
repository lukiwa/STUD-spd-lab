#pragma once

#include <fstream>
#include <memory>
#include <stdexcept>

#include <gecode/int.hh>
#include <gecode/minimodel.hh>


struct Tasks
{
    Tasks() = default;

    Tasks(int tasks_no, int machine_no, Gecode::IntArgs tasks)
        : tasks_no(tasks_no)
        , machine_no(machine_no)
        , tasks(std::move(tasks))
    {}

    int tasks_no, machine_no;
    Gecode::IntArgs tasks;

    Gecode::Matrix<Gecode::IntArgs> matrix() const
    {
        return Gecode::Matrix<Gecode::IntArgs>(tasks, machine_no, tasks_no);
    }
};

std::unique_ptr<Tasks> load_file(const std::string& filename)
{
    std::ifstream file(filename);
    if (!file)
        throw std::runtime_error("Wrong filename");

    auto result = std::make_unique<Tasks>();
    file >> result->tasks_no >> result->machine_no;

    for (int i = 0; i < result->tasks_no; ++i)
    {
        for (int j = 0; j < result->machine_no; ++j)
        {
            int val;
            file >> val;
            result->tasks << val;
        }
    }

    return result;
}

int get_cmax(const Tasks& tasks, const std::vector<int>& order)
{
    assert(order.size() == tasks.tasks_no);

    const auto task_matrix = tasks.matrix();

    std::vector<int> time_on_machines(tasks.machine_no, 0);
    for (int task : order)
    {
        int task_time = time_on_machines[0];

        for (int machine = 0; machine < tasks.machine_no; ++machine)
        {
            time_on_machines[machine] = std::max(task_time, time_on_machines[machine]) + task_matrix(machine, task);
            task_time = time_on_machines[machine];
        }
    }

    return time_on_machines.back();
}
