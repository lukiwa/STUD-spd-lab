#include <iostream>
#include <algorithm>
#include <numeric>
#include <map>

#include <gecode/int.hh>
#include <gecode/gist.hh>
#include <gecode/minimodel.hh>

#include "tasks.hpp"

class JobshopSpace : public Gecode::IntMinimizeSpace
{
public:
    JobshopSpace(const Tasks& tasks)
        : tasks_(tasks)
    {
        auto est_cmax = get_est_cmax();
        starts_ = Gecode::IntVarArray(*this, tasks_.jobs_no, 0, est_cmax);
        cmax_ = Gecode::IntVar(*this, 0, est_cmax);

        // starts_matrix(i, j) -> ith task and jth job in sequence
        Gecode::Matrix<Gecode::IntVarArray> starts_matrix(starts_, tasks_.machine_no, tasks_.task_no);

        // precedence
        for (int task = 0; task < tasks_.tasks.size(); ++task)
        {
            for (int job = 1; job < tasks_.tasks[task].jobs.size(); ++job)
            {
                Gecode::rel(*this, starts_matrix(task, job) >= starts_matrix(task, job - 1) + tasks_.tasks[task].jobs[job].duration);
            }
        }

        // no overlap on machines
        std::map<unsigned, std::vector<std::pair<Gecode::IntVar, Tasks::Task::Job>>> machine_to_starts_map;
        for (int task = 0; task < tasks_.tasks.size(); ++task)
        {
            for (int job = 1; job < tasks_.tasks[task].jobs.size(); ++job)
            {
                const auto& job_el = tasks_.tasks[task].jobs[job];
                auto& el = machine_to_starts_map[job_el.machine];
                el.push_back({starts_matrix(task, job), job_el});
            }
        }

        for (const auto& [machine, jobs_on_machine] : machine_to_starts_map)
        {
            Gecode::IntVarArgs jobs_start_times;
            Gecode::IntArgs jobs_duration;

            for (const auto& [start_time, job] : jobs_on_machine)
            {
                jobs_start_times << start_time;
                jobs_duration << job.duration;
            }

            Gecode::unary(*this, jobs_start_times, jobs_duration);
        }

        // cmax setting
        for (int task = 0; task < tasks_.tasks.size(); ++task)
        {
            for (int job = 0; job < tasks_.tasks[task].jobs.size(); ++job)
            {
                Gecode::rel(*this, cmax_ >= starts_matrix(task, job) + tasks_.tasks[task].jobs[job].duration);
            }
        }

        Gecode::branch(*this, starts_, Gecode::INT_VAR_SIZE_MIN(), Gecode::INT_VAL_MIN());
        Gecode::branch(*this, cmax_, Gecode::INT_VAL_MIN());
    }

    int get_est_cmax() const
    {
        std::vector<int> time_on_machines(tasks_.task_no, 0);

        for (const auto& task : tasks_.tasks)
        {
            int current_task_time = 0;
            for (const auto& job : task.jobs)
            {
                current_task_time = std::max(current_task_time, time_on_machines[job.machine]) + job.duration;
                time_on_machines[job.machine] = current_task_time;
            }
        }

        return *std::max_element(time_on_machines.begin(), time_on_machines.end());
    }

    Gecode::IntVar cost() const override
    {
        return cmax_;
    }

    JobshopSpace(JobshopSpace& other)
        : Gecode::IntMinimizeSpace(other)
        , tasks_(other.tasks_)
    {
        starts_.update(*this, other.starts_);
        cmax_.update(*this, other.cmax_);
    }

    Gecode::Space* copy() override
    {
        return new JobshopSpace(*this);
    }

    void print(std::ostream& os) const
    {
        os << "cmax: " << cmax_
            << "\nstarts: " << starts_ << std::endl;
    }

private:
    const Tasks& tasks_;
    Gecode::IntVarArray starts_;
    Gecode::IntVar cmax_;
};

int main()
{
    const auto tasks = load_file("data.001");
    JobshopSpace space(*tasks);


    Gecode::Gist::Print<JobshopSpace> p("Print solution");
    Gecode::Gist::Options o;
    o.inspect.click(&p);
    Gecode::Gist::bab(&space, o);


    /*
    Gecode::BAB<JobshopSpace> engine(&space);
    while (auto* solution = engine.next())
    {
        std::cout << "-- SOLUTION FOUND --" << std::endl;
        solution->print(std::cout);
        std::cout << "--------------------" << std::endl;
        delete solution;
    }
    */
}
