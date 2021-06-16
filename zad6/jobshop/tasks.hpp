#pragma once

#include <fstream>
#include <sstream>
#include <memory>

#include <boost/range/adaptors.hpp>

#include <gecode/int.hh>

struct Tasks
{
    struct Task
    {
        struct Job
        {
            int machine;
            int duration;
        };

        std::vector<Job> jobs;
    };

    std::vector<Task> tasks;
    int machine_no, task_no, jobs_no ;
};

std::unique_ptr<Tasks> load_file(const std::string& s)
{
    std::ifstream file(s);
    assert(file);

    auto result = std::make_unique<Tasks>();

    file >> result->task_no >> result->machine_no >> result->jobs_no;
    file.ignore(50, '\n');

    int processed_jobs = 0;
    for (int i = 0; i < result->task_no; ++i)
    {
        std::string line;
        std::getline(file, line, '\n');

        std::stringstream ssr(line);

        int sentinel;
        ssr >> sentinel;
        assert(sentinel == result->machine_no);

        Tasks::Task task;
        int machine_no, task_time;
        while (ssr >> machine_no >> task_time)
        {
            task.jobs.push_back({machine_no - 1, task_time});
            processed_jobs += 1;
        }

        result->tasks.push_back(std::move(task));
    }

    assert(processed_jobs == result->jobs_no);
    return result;
}

struct OrderType
{
    int task_no;
    int job_no;
};

bool isGoodOrder(const Tasks& tasks, const std::vector<OrderType>& order)
{
    using namespace boost::adaptors;
    const auto job_no_comp = [](const auto& lhs, const auto& rhs){
        return lhs.job_no < rhs.job_no;
    };

    for (int task = 0; task < tasks.task_no; ++task)
    {
        auto jobs_in_task = order | filtered([task](const auto& el){ return el.task_no == task; });

        if (!std::is_sorted(jobs_in_task.begin(), jobs_in_task.end(), job_no_comp))
        {
            return false;
        }
    }

    return true;
}

int get_cmax(const Tasks& tasks, const std::vector<OrderType>& order)
{
    assert(isGoodOrder(tasks, order));

    std::vector<int> machine_to_time(tasks.machine_no, 0);
    std::vector<int> task_to_last_job_finish(tasks.task_no, 0);
    for (const auto& order_el : order)
    {
        const auto& job = tasks.tasks[order_el.task_no].jobs[order_el.job_no];

        int finish_time = std::max(
            machine_to_time[job.machine],
            task_to_last_job_finish[order_el.task_no]) + job.duration;

        machine_to_time[job.machine] = finish_time;
        task_to_last_job_finish[order_el.task_no] = finish_time;
    }

    return *std::max_element(machine_to_time.begin(), machine_to_time.end());
}
