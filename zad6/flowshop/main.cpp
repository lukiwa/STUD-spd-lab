#include <iostream>
#include <algorithm>
#include <numeric>

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

        Gecode::distinct(*this, order_);

        Gecode::Matrix<Gecode::IntVarArray> starts_matrix(starts_, tasks_.machine_no, tasks_.tasks_no);
        auto task_matrix = tasks_.matrix();
        for (int machine = 0; machine < tasks_.machine_no; ++machine)
        {
            Gecode::unary(*this, starts_matrix.col(machine), task_matrix.col(machine));
        }


        for (int task = 0; task < tasks_.tasks_no; ++task)
        {
            auto start_times_of_a_task = static_cast<Gecode::IntVarArgs>(starts_matrix.row(task));

            for (int machine = 1; machine < tasks_.machine_no; ++machine)
            {
                Gecode::rel(*this, start_times_of_a_task[machine] >= start_times_of_a_task[machine - 1] + task_matrix(machine - 1, task));
            }

            Gecode::rel(*this, cmax_ >= start_times_of_a_task[start_times_of_a_task.size() - 1] + task_matrix(tasks_.machine_no - 1, task));
        }

        branchOnOrderAndStarts(*this, tasks_, order_, starts_);
        Gecode::branch(*this, starts_, Gecode::INT_VAR_MIN_MIN(), Gecode::INT_VAL_MIN());
        Gecode::branch(*this, cmax_, Gecode::INT_VAL_MIN());
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
        Gecode::Matrix<Gecode::IntVarArray> starts_matrix(starts_, tasks_.machine_no, tasks_.tasks_no);
        /*
        os << "starts:\n";
        for (int task = 0; task < tasks_.tasks_no; ++task)
        {
            os << starts_matrix.row(task) << '\n';
        }
        */
        os << "cmax: " << cmax_
            << "\norder: " << order_ << std::endl;
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
        //std::vector<int> order(tasks_.tasks_no, 0);
        //std::iota(order.begin(), order.end(), 0);

        //return get_cmax(tasks_, johnson(tasks_));
        return 5918;
    }

    const Tasks& tasks_;
    Gecode::IntVar cmax_;
    Gecode::IntVarArray starts_;  // matrix denoting start times for (machine, task)
    Gecode::IntVarArray order_;
};

int main()
{
    const auto tasks = load_file("data.080");
    FlowshopSpace space(*tasks);

    std::cout << "johnson: " << get_cmax(*tasks, johnson(*tasks)) << std::endl;


    Gecode::Gist::Print<FlowshopSpace> p("Print solution");
    Gecode::Gist::Options o;
    o.inspect.click(&p);
    Gecode::Gist::bab(&space, o);



    /*
    Gecode::Search::Options o;
    Gecode::Search::TimeStop timeStop(200 * 1000);
    o.stop = &timeStop;

    Gecode::BAB<FlowshopSpace> engine(&space, o);

    while (auto* solution = engine.next())
    {
        auto order = solution->deduceOrder();

        std::cout << "-- SOLUTION FOUND --\n";
        solution->print(std::cout);
        std::cout << "--------------------\n";
        std::cout << "cmax from deduced order: " << get_cmax(*tasks, order) << '\n';
        std::cout << "--------------------" << std::endl;

        delete solution;
    }
    */
}
