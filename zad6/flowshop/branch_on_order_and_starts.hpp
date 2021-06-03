#pragma once

#include <boost/range/algorithm.hpp>
#include <boost/range/adaptors.hpp>

#include <gecode/kernel.hh>
#include <gecode/int.hh>

#include "tasks.hpp"

class BranchOnOrderAndStarts : public Gecode::Brancher
{
public:
    BranchOnOrderAndStarts(
        Gecode::Home home,
        const Tasks& tasks,
        Gecode::Int::IntView cmax,
        Gecode::ViewArray<Gecode::Int::IntView> order,
        Gecode::ViewArray<Gecode::Int::IntView> starts)
            : Gecode::Brancher(home)
            , cmax_(cmax)
            , order_(order)
            , starts_(starts)
            , tasks_(tasks)
    {
        assert(order.size() == tasks.tasks_no);
        assert(starts.size() == tasks.tasks_no * tasks.machine_no);
    }

    BranchOnOrderAndStarts(
        Gecode::Home home,
        BranchOnOrderAndStarts& other)
            : Gecode::Brancher(home, other)
            , tasks_(other.tasks_)
    {
        cmax_.update(home, other.cmax_);
        order_.update(home, other.order_);
        starts_.update(home, other.starts_);
    }

    const Tasks& getTasks() const
    {
        return tasks_;
    }

    static void post(
        Gecode::Home home,
        const Tasks& tasks,
        Gecode::Int::IntView cmax,
        Gecode::ViewArray<Gecode::Int::IntView> order,
        Gecode::ViewArray<Gecode::Int::IntView> starts)
    {
        (void) new (home) BranchOnOrderAndStarts(home, tasks, cmax, order, starts);
    }

    bool status(const Gecode::Space& home) const override
    {
        return !std::all_of(order_.begin(), order_.end(), [](const auto& view){ return view.assigned(); });
    }

    Gecode::Brancher* copy(Gecode::Space& home) override
    {
        return new (home) BranchOnOrderAndStarts(home, *this);
    }

    class OrderAndStartTimesChoice : public Gecode::Choice
    {
    public:
        int task_index;
        int order_value;
        int perceived_cmax_min;
        std::vector<int> start_times;

        OrderAndStartTimesChoice(const BranchOnOrderAndStarts& b, int task_index, int order_value, int perceived_cmax_min, std::vector<int>&& start_times)
            : Gecode::Choice(b, 2)
            , task_index(task_index)
            , order_value(order_value)
            , perceived_cmax_min(perceived_cmax_min)
            , start_times(start_times)
        {
            assert(start_times.size() == b.getTasks().machine_no);
        }

        void archive(Gecode::Archive& e) const override
        {
            Gecode::Choice::archive(e);
            e << task_index << order_value << perceived_cmax_min;
            for (int i : start_times)
            {
                e << i;
            }
        }
    };

    Gecode::Choice* choice(Gecode::Space& home) override
    {
        using namespace boost::adaptors;
        auto notAssigned = [](const auto& view){ return !view.assigned(); };
        auto isAssigned  = [](const auto& view){ return  view.assigned(); };
        auto minComp = [](const auto& lhs, const auto& rhs){ return lhs.min() < rhs.min(); };
        auto valComp = [](const auto& lhs, const auto& rhs){ return lhs.val() < rhs.val(); };

        auto hasInDomain = [](const int i){
            return [i](const auto& view){
                return view.in(i);
            };
        };

        // 1. order value
        auto var_val_max = boost::range::max_element(order_ | filtered(isAssigned), valComp);
        int order_value;
        if (var_val_max.base() != order_.end())
        {
            order_value = var_val_max->val() + 1;
        }
        else
        {
            order_value = 0;
        }

        // 2. task to be assigned
        auto var_min_min = boost::range::min_element(order_ | filtered(notAssigned) | filtered(hasInDomain(order_value)), minComp);
        if (var_min_min.base().base() == order_.end())
        {
            return new OrderAndStartTimesChoice(*this, 0, -1, 0, std::vector<int>(tasks_.machine_no, 0));
        }
        auto var_min_mins = order_
            | filtered(notAssigned)
            | filtered(hasInDomain(order_value))
            | filtered([&var_min_min](const auto& view){ return view.min() == var_min_min->min(); });
        auto var_min_mins_size = boost::size(var_min_mins);

        int task_index = std::next(var_min_mins.begin(), std::rand() % var_min_mins_size).base().base().base() - order_.begin();
        assert(task_index >= 0);


        // 3. start times
        auto tasks_matrix = tasks_.matrix();
        std::vector<int> start_times(tasks_.machine_no, 0);
        if (order_value == 0)
        {
            start_times[0] = 0;
            for (int machine = 1; machine < tasks_.machine_no; ++machine)
            {
                start_times[machine] = start_times[machine - 1] + tasks_matrix(machine - 1, task_index);
            }
        }
        else
        {
            auto before_task = boost::range::find_if(order_, [order_value](const auto& i){ return i.assigned() && i.val() == order_value - 1; });
            assert(before_task != order_.end());
            int before_task_index = before_task - order_.begin();
            assert(before_task_index >= 0);

            start_times[0] = starts_[0 + tasks_.machine_no * before_task_index].val() + tasks_matrix(0, before_task_index);
            for (int machine = 1; machine < tasks_.machine_no; ++machine)
            {
                start_times[machine] = std::max(
                    start_times[machine - 1] + tasks_matrix(machine - 1, task_index),
                    starts_[machine + tasks_.machine_no * before_task_index].val() + tasks_matrix(machine, before_task_index));
            }
        }

        // 4. cmax
        int sum_of_not_assigned_durations = 0;
        for (int task = 0; task < tasks_.tasks_no; ++task)
        {
            if (!order_[task].assigned())
            {
                sum_of_not_assigned_durations += tasks_matrix(tasks_.machine_no - 1, task);
            }
        }

        int perceived_min_cmax = sum_of_not_assigned_durations + start_times[tasks_.machine_no - 1];

        return new OrderAndStartTimesChoice(*this, task_index, order_value, perceived_min_cmax, std::move(start_times));
    }

    Gecode::Choice* choice(const Gecode::Space&, Gecode::Archive& e) override
    {
        int task_index, order_value, perceived_min_cmax;
        e >> task_index >> order_value >> perceived_min_cmax;

        std::vector<int> start_times(tasks_.machine_no, 0);
        for (int i = 0; i < tasks_.machine_no; ++i)
        {
            e >> start_times[i];
        }

        return new OrderAndStartTimesChoice(*this, task_index, order_value, perceived_min_cmax, std::move(start_times));
    }

    Gecode::ExecStatus commit(Gecode::Space& home, const Gecode::Choice& c, unsigned a) override
    {
        const auto& choice = static_cast<const OrderAndStartTimesChoice&>(c);

        if (a == 0)
        {
            GECODE_ME_CHECK(order_[choice.task_index].eq(home, choice.order_value));
            GECODE_ME_CHECK(cmax_.gq(home, choice.perceived_cmax_min));

            for (int machine = 0; machine < tasks_.machine_no; ++machine)
            {
                GECODE_ME_CHECK(starts_[machine + tasks_.machine_no * choice.task_index].eq(home, choice.start_times[machine]));
            }
        }
        else if (choice.order_value == -1)
        {
            return Gecode::ES_FAILED;
        }
        else
        {
            GECODE_ME_CHECK(order_[choice.task_index].nq(home, choice.order_value));
        }

        return Gecode::ES_OK;
    }

    void print(const Gecode::Space& home, const Gecode::Choice& c, unsigned a, std::ostream& os) const override
    {
        const auto& choice = static_cast<const OrderAndStartTimesChoice&>(c);

        if (a == 0)
        {
            os << "order[" << choice.task_index << "] = " << choice.order_value;
        }
        else
        {
            os << "order[" << choice.task_index << "] != " << choice.order_value;
        }
    }

private:
    Gecode::Int::IntView cmax_;
    Gecode::ViewArray<Gecode::Int::IntView> order_;
    Gecode::ViewArray<Gecode::Int::IntView> starts_;
    const Tasks& tasks_;
};

void branchOnOrderAndStarts(
    Gecode::Home home,
    const Tasks& tasks,
    Gecode::IntVar cmax,
    Gecode::IntVarArgs order,
    Gecode::IntVarArgs starts)
{
    if (home.failed())
        return;

    Gecode::Int::IntView cmax_view(cmax);
    Gecode::ViewArray<Gecode::Int::IntView> order_view(home, order);
    Gecode::ViewArray<Gecode::Int::IntView> starts_view(home, starts);

    BranchOnOrderAndStarts::post(home, tasks, cmax_view, order_view, starts_view);
}
