#pragma once

#include <fstream>
#include <sstream>
#include <memory>

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
