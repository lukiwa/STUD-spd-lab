#include <iostream>
#include <algorithm>
#include <numeric>
#include <map>

#include <boost/range/adaptors.hpp>

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
        cmax_ = Gecode::IntVar(*this, 0, Gecode::Int::Limits::max);

        auto starts_matrix = matrix();

        // precedence
        for (int task = 0; task < tasks_.tasks.size(); ++task)
        {
            for (int job = 1; job < tasks_.tasks[task].jobs.size(); ++job)
            {
                Gecode::rel(*this, starts_matrix(job, task) >= starts_matrix(job - 1, task) + tasks_.tasks[task].jobs[job - 1].duration);
            }
        }

        // no overlap on machines
        std::map<unsigned, std::vector<std::pair<Gecode::IntVar, Tasks::Task::Job>>> machine_to_starts_map;
        for (int task = 0; task < tasks_.tasks.size(); ++task)
        {
            for (int job = 0; job < tasks_.tasks[task].jobs.size(); ++job)
            {
                const auto& job_el = tasks_.tasks[task].jobs[job];
                machine_to_starts_map[job_el.machine].push_back({starts_matrix(job, task), job_el});
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
        Gecode::IntVarArgs lastJobsEnd;
        for (int task = 0; task < tasks_.tasks.size(); ++task)
        {
            lastJobsEnd << Gecode::expr(*this, starts_matrix(tasks_.machine_no - 1, task) + tasks_.tasks[task].jobs.back().duration);
        }
        Gecode::rel(*this, cmax_ == Gecode::max(lastJobsEnd));

        ///////////////////////////////////////////////////////////////////

        Gecode::branch(*this, starts_, Gecode::INT_VAR_CHB_MAX(), Gecode::INT_VAL_SPLIT_MIN());
    }

    int get_est_cmax() const
    {
        using namespace boost::adaptors;

        std::vector<OrderType> order;
        for (const auto& task : tasks_.tasks | indexed())
        {
            for (const auto& job : task.value().jobs | indexed())
            {
                order.push_back(OrderType{(int) task.index(), (int) job.index()});
            }
        }

        //return 7000;
        return get_cmax(tasks_, order);
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

    // starts_matrix(i, j) -> ith task and jth job in sequence
    Gecode::Matrix<Gecode::IntVarArray> matrix() const
    {
        return Gecode::Matrix<Gecode::IntVarArray>(starts_, tasks_.machine_no, tasks_.task_no);
    }

    std::vector<OrderType> deduceOrder() const
    {
        using namespace boost::adaptors;

        struct TaggedStart
        {
            int start;
            OrderType job_tag;
        };

        //////////////////////////////////////////////////////////////

        assert(std::all_of(starts_.begin(), starts_.end(), [](const auto& el){ return el.assigned(); }));

        std::vector<TaggedStart> taggedStarts;
        taggedStarts.reserve(tasks_.jobs_no);
        auto starts_matrix = matrix();
        for (const auto& task : tasks_.tasks | indexed())
        {
            for (const auto& job : task.value().jobs | indexed())
            {
                taggedStarts.push_back(TaggedStart{
                    starts_matrix(job.index(), task.index()).val(),
                    OrderType{(int) task.index(), (int) job.index()}
                });
            }
        }

        std::sort(taggedStarts.begin(), taggedStarts.end(), [](const auto& lhs, const auto& rhs){
            return lhs.start < rhs.start;
        });

        std::vector<OrderType> result;
        result.reserve(taggedStarts.size());
        std::transform(taggedStarts.begin(), taggedStarts.end(), std::back_inserter(result), [](const auto& el){
            return el.job_tag;
        });

        return result;
    }

private:
    const Tasks& tasks_;
    Gecode::IntVarArray starts_;
    Gecode::IntVar cmax_;
};

int main(int argc, char** argv)
{
    constexpr bool USE_GIST = false;

    if (argc != 2)
    {
        std::cout << "usage: ./a.out <input_file>" << std::endl;
        return -1;
    }

    const auto tasks = load_file(argv[1]);
    JobshopSpace space(*tasks);

    if (USE_GIST)
    {
        Gecode::Gist::Print<JobshopSpace> p("Print solution");
        Gecode::Gist::Options o;
        o.inspect.click(&p);
        Gecode::Gist::bab(&space, o);
    }
    else
    {
        Gecode::BAB<JobshopSpace> engine(&space);
        std::cout << "cmax: " << space.cost().max() << std::endl;
        while (auto* solution = engine.next())
        {
            std::cout << "cmax : " << solution->cost() << std::endl;

            auto order = solution->deduceOrder();
            assert(get_cmax(*tasks, order) == solution->cost().val());

            delete solution;
        }
    }
}
