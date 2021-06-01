#pragma once

#include <vector>
#include <deque>
#include <vector>
#include <memory>
#include <numeric>

#include "tasks.hpp"

std::unique_ptr<Tasks> decayTo2Machines(const Tasks& tasks)
{
    auto current_tasks = std::make_unique<Tasks>(tasks);

    while (current_tasks->machine_no > 2)
    {
        auto new_tasks = std::make_unique<Tasks>(
            current_tasks->tasks_no,
            current_tasks->machine_no - 1,
            Gecode::IntArgs(current_tasks->tasks_no * (current_tasks->machine_no - 1))
        );

        auto old_matrix = current_tasks->matrix();
        auto new_matrix = new_tasks->matrix();

        for (int task = 0; task < new_tasks->tasks_no; ++task)
        {
            for (int machine = 0; machine < new_tasks->machine_no; ++machine)
            {
                new_matrix(machine, task) = old_matrix(machine, task) + old_matrix(machine + 1, task);
            }
        }

        current_tasks = std::move(new_tasks);
    }

    return current_tasks;
}

std::tuple<int, int> pick_min(const std::vector<int>& a, const Tasks& tasks)
{
    auto tasks_matrix = tasks.matrix();
    int min_time = tasks_matrix(0, a.front());
    std::tuple<int, int> min_time_task_machine{a.front(), 0};

    for (int taskIdx : a)
    {
        for (int machine = 0; machine < tasks.machine_no; ++machine)
        {
            if (min_time > tasks_matrix(machine, taskIdx))
            {
                min_time = tasks_matrix(machine, taskIdx);
                min_time_task_machine = {taskIdx, machine};
            }
        }
    }

    return min_time_task_machine;
}

std::vector<int> johnson(const Tasks& tasks_other)
{
    auto tasks = decayTo2Machines(tasks_other);

    std::vector<int> a(tasks->tasks_no, 0);
    std::iota(a.begin(), a.end(), 0);

    std::vector<int> l1;
    std::deque<int> l2;

    while (!a.empty())
    {
        auto min_time_task_machine = pick_min(a, *tasks);
        std::erase_if(a, [&min_time_task_machine](int el){ return el == std::get<0>(min_time_task_machine); });

        if (std::get<1>(min_time_task_machine) == 0)
        {
            l1.push_back(std::get<0>(min_time_task_machine));
        }
        else
        {
            l2.push_front(std::get<0>(min_time_task_machine));
        }
    }

    std::copy(l2.begin(), l2.end(), std::back_inserter(l1));

    return l1;
}
