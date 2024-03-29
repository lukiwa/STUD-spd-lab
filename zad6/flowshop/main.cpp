#include <iostream>
#include <algorithm>
#include <numeric>
#include <chrono>

#include <gecode/int.hh>
#include <gecode/gist.hh>
#include <gecode/minimodel.hh>

#include "tasks.hpp"
#include "allocate_on_all_machines_after_first.hpp"
#include "branch_on_order_and_starts.hpp"
#include "johnson.hpp"

class FlowshopSpace : public Gecode::IntMinimizeSpace
{
public:
    FlowshopSpace(const Tasks& tasks)
        : tasks_(tasks)
    {
        auto est_cmax = get_est_cmax();
        cmax_ = Gecode::IntVar(*this, 0, est_cmax);
        starts_ = Gecode::IntVarArray(*this, tasks_.tasks_no * tasks_.machine_no, 0, est_cmax);
        order_ = Gecode::IntVarArray(*this, tasks_.tasks_no, 0, tasks_.tasks_no - 1);

        // distinct order
        Gecode::distinct(*this, order_);

        // no overlap on machines
        Gecode::Matrix<Gecode::IntVarArray> starts_matrix(starts_, tasks_.machine_no, tasks_.tasks_no);
        auto task_matrix = tasks_.matrix();
        for (int machine = 0; machine < tasks_.machine_no; ++machine)
        {
            Gecode::unary(*this, starts_matrix.col(machine), task_matrix.col(machine));
        }

        // task precedence and cmax
        Gecode::IntVarArgs lastJobsEnd;
        for (int task = 0; task < tasks_.tasks_no; ++task)
        {
            auto start_times_of_a_task = static_cast<Gecode::IntVarArgs>(starts_matrix.row(task));

            for (int machine = 1; machine < tasks_.machine_no; ++machine)
            {
                Gecode::rel(*this, start_times_of_a_task[machine] >= start_times_of_a_task[machine - 1] + task_matrix(machine - 1, task));
            }

            lastJobsEnd << Gecode::expr(*this, start_times_of_a_task[start_times_of_a_task.size() - 1] + task_matrix(tasks_.machine_no - 1, task));
        }
        Gecode::rel(*this, cmax_ == Gecode::max(lastJobsEnd));

        // task i before task j
        for (int i = 0; i < tasks_.tasks_no; ++i)
        {
            for (int j = 0; j < tasks_.tasks_no; ++j)
            {
                if (i != j)
                {
                    Gecode::BoolVarArgs i_is_exactly_before_j;

                    i_is_exactly_before_j << Gecode::expr(*this, starts_matrix(0, j) == starts_matrix(0, i) + task_matrix(0, i));
                    for (int machine = 1; machine < tasks_.machine_no; ++machine)
                    {
                        i_is_exactly_before_j << Gecode::expr(*this, starts_matrix(machine, j) == Gecode::max(
                            starts_matrix(machine - 1, j) + task_matrix(machine - 1, j),
                            starts_matrix(machine, i) + task_matrix(machine, i)
                        ));
                    }

                    Gecode::BoolVar i_is_exactly_before_j_all(*this, 0, 1);
                    Gecode::rel(*this, Gecode::BOT_AND, i_is_exactly_before_j, i_is_exactly_before_j_all);

                    Gecode::rel(*this,
                        (order_[i] + 1 == order_[j])
                        >> (i_is_exactly_before_j_all)
                    );
                }
            }

            Gecode::BoolVarArgs i_is_first;
            i_is_first << Gecode::expr(*this, starts_matrix(0, i) == 0);
            for (int machine = 1; machine < tasks_.machine_no; ++machine)
            {
                i_is_first << Gecode::expr(*this, starts_matrix(machine, i) == starts_matrix(machine - 1, i) + task_matrix(machine - 1, i));
            }

            Gecode::BoolVar i_is_first_all(*this, 0, 1);
            Gecode::rel(*this, Gecode::BOT_AND, i_is_first, i_is_first_all);

            Gecode::rel(*this,
                (order_[i] == 0)
                >> (i_is_first_all));
        }

        branchOnOrderAndStarts(*this, tasks_, cmax_, order_, starts_);
        Gecode::IntVarArgs a;
        for (const auto& orderVar : order_)
        {
            a << orderVar;
        }
        std::random_shuffle(a.begin(), a.end());

        //Gecode::branch(*this, a, Gecode::INT_VAR_CHB_SIZE_MAX(), Gecode::INT_VAL_MIN());
        //Gecode::branch(*this, a, Gecode::INT_VAR_CHB_MAX(), Gecode::INT_VAL_MIN());
    }

    FlowshopSpace(FlowshopSpace& other)
        : Gecode::IntMinimizeSpace(other)
        , tasks_(other.tasks_)
    {
        cmax_.update(*this, other.cmax_);
        starts_.update(*this, other.starts_);
        order_.update(*this, other.order_);
    }

    Gecode::Space* copy() override
    {
        return new FlowshopSpace(*this);
    }

    Gecode::IntVar cost() const override
    {
        return cmax_;
    }

    void print(std::ostream& os) const
    {
        os << "cmax: " << cmax_
            << "\norder: " << order_
            << "\nstarts:\n";

        if (true)
        {
            os << std::flush;
            return;
        }

        Gecode::Matrix<Gecode::IntVarArray> starts_matrix(starts_, tasks_.machine_no, tasks_.tasks_no);
        for (int task = 0; task < tasks_.tasks_no; ++task)
        {
            for (int machine = 0; machine < tasks_.machine_no; ++machine)
            {
                os << starts_matrix(machine, task) << ", ";
            }
            os << "\n";
        }

        os << std::flush;
    }

    std::vector<int> deduceOrder() const
    {
        Gecode::Matrix<Gecode::IntVarArray> starts_matrix(starts_, tasks_.machine_no, tasks_.tasks_no);
        auto starts_on_machine_1 = static_cast<Gecode::IntVarArgs>(starts_matrix.col(0));
        assert(std::all_of(starts_on_machine_1.begin(), starts_on_machine_1.end(), [](const auto& el){ return el.assigned(); }));

        std::vector<std::pair<int, int>> partial_result;
        for (int i = 0; i < tasks_.tasks_no; ++i)
        {
            partial_result.push_back({i, starts_on_machine_1[i].val()});
        }

        std::sort(partial_result.begin(), partial_result.end(), [](const auto& lhs, const auto& rhs){
            return lhs.second < rhs.second;
        });

        std::vector<int> result;
        std::transform(partial_result.begin(), partial_result.end(), std::back_inserter(result), [](const auto& partial){
            return partial.first;
        });

        return result;
    }

    const Gecode::IntVarArray& getStarts() const
    {
        return starts_;
    }

    const Tasks& getTasks() const
    {
        return tasks_;
    }

private:
    int get_est_cmax()
    {
        int est = get_cmax(tasks_, johnson(tasks_));
        std::cout << "est from johnson: " << est << std::endl;
        return est;
    }

    const Tasks& tasks_;
    Gecode::IntVar cmax_;
    Gecode::IntVarArray starts_;  // matrix denoting start times for (machine, task)
    Gecode::IntVarArray order_;
};

int main(int argc, char** argv)
{
    if (argc != 2)
    {
        std::cout << "usage: ???" << std::endl;
        return -1;
    }

    constexpr bool USE_GIST = false;

    //std::srand(std::time(nullptr));
    std::srand(42);

    const auto tasks = load_file(argv[1]);
    FlowshopSpace space(*tasks);

    if (USE_GIST)
    {
        Gecode::Gist::Print<FlowshopSpace> p("Print solution");
        Gecode::Gist::Options o;
        o.inspect.click(&p);
        Gecode::Gist::bab(&space, o);
    }
    else
    {
        Gecode::Search::Options o;
        Gecode::Search::TimeStop stop(15 * 1000);
        //o.stop = &stop;
        Gecode::BAB<FlowshopSpace> engine(&space, o);
        auto now = std::chrono::high_resolution_clock::now();

        while (auto* solution = engine.next())
        {
            auto order = solution->deduceOrder();

            assert(solution->cost().val() == get_cmax(*tasks, order));

            std::cout << "-- SOLUTION FOUND --\n";
            solution->print(std::cout);
            std::cout << "--------------------\n";
            std::cout << "cmax from deduced order: " << get_cmax(*tasks, order) << '\n';

            auto now2 = std::chrono::high_resolution_clock::now();
            std::cout << "time passed: " << (std::chrono::duration_cast<std::chrono::milliseconds>(now2 - now).count() / 1000.0) << " sec\n";

            std::cout << "--------------------" << std::endl;

            delete solution;
        }
    }
}
