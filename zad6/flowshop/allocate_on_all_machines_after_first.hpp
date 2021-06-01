#pragma once

#include <gecode/int.hh>
#include <gecode/kernel.hh>

#include <boost/range/adaptors.hpp>
#include <boost/range/algorithm.hpp>

template<class MySpace>
class AllocateOnAllMachinesAfterFirst : public Gecode::Propagator
{
public:
    AllocateOnAllMachinesAfterFirst(Gecode::Space& home, Gecode::ViewArray<Gecode::Int::IntView> machine_start_times)
        : Gecode::Propagator(home)
        , machine_start_times(machine_start_times)
    {
        machine_start_times[0].subscribe(home, *this, Gecode::Int::PC_INT_VAL);
    }

    AllocateOnAllMachinesAfterFirst(Gecode::Space& home, AllocateOnAllMachinesAfterFirst& p)
        : Gecode::Propagator(home, p)
    {
        machine_start_times.update(home, p.machine_start_times);
    }

    static Gecode::ExecStatus post(Gecode::Space& home, Gecode::ViewArray<Gecode::Int::IntView> machine_start_times)
    {
        (void) new (home) AllocateOnAllMachinesAfterFirst(home, machine_start_times);
        return Gecode::ES_OK;
    }

    std::size_t dispose(Gecode::Space& home) override
    {
        machine_start_times[0].cancel(home, *this, Gecode::Int::PC_INT_VAL);
        (void) Propagator::dispose(home);
        return sizeof(*this);
    }

    Gecode::Propagator* copy(Gecode::Space& home) override
    {
        return new (home) AllocateOnAllMachinesAfterFirst(home, *this);
    }

    Gecode::PropCost cost(const Gecode::Space&, const Gecode::ModEventDelta&) const override
    {
        return Gecode::PropCost::cubic(Gecode::PropCost::HI, machine_start_times.size());
    }

    void reschedule(Gecode::Space& home) override
    {
        throw std::runtime_error("AllocateOnAllMachinesAfterFirst::reschedule called");
    }

    Gecode::ExecStatus propagate(Gecode::Space& home, const Gecode::ModEventDelta&)
    {
        using namespace boost::adaptors;

        if (!machine_start_times[0].assigned())
            //return Gecode::ES_FAILED;
            throw std::runtime_error("master_ not assigned, please check");

        auto& home_ = dynamic_cast<MySpace&>(home);
        const auto& tasks = home_.getTasks();
        auto tasks_matrix = tasks.matrix();
        const auto& starts = home_.getStarts();

        Gecode::Matrix<Gecode::IntVarArgs> starts_matrix(starts, tasks.machine_no, tasks.tasks_no);

        auto starts_on_machine_1 = static_cast<Gecode::IntVarArgs>(starts_matrix.col(0));
        int this_task_index = (starts_on_machine_1 | indexed() | filtered([this](const auto& el){ return el.value().assigned() && el.value().val() == machine_start_times[0].val(); })).begin()->index();
        auto tasks_before = starts_on_machine_1 | indexed() | filtered([this](const auto& el){ return el.value().assigned() && el.value().val() != machine_start_times[0].val(); });

        std::cout << "-------------------------------------------------------------------------------------" << std::endl;

        std::cout << "tasks_before.size: " << boost::size(tasks_before) << std::endl;
        for (const auto& task : tasks_before)
        {
            std::cout << "task: " << task.value() << " : " << task.index() << std::endl;
        }

        auto max_task_before = boost::range::max_element(tasks_before, [](const auto& lhs, const auto& rhs){ return lhs.value().val() < rhs.value().val(); });

        if (max_task_before == tasks_before.end())
        {
            for (int machine = 1; machine < tasks.machine_no; ++machine)
            {
                if (machine_start_times[machine].eq(home, machine_start_times[machine].min()) == Gecode::Int::ME_INT_FAILED)
                    return Gecode::ES_FAILED;
            }

            return home.ES_SUBSUMED(*this);
        }
        else
        {
            auto max_task_index = max_task_before->index();

            for (int machine = 1; machine < tasks.machine_no; ++machine)
            {
                std::cout << "hello, max task index: " << max_task_index << std::endl;
                if (machine_start_times[machine].eq(home, std::max(
                    machine_start_times[machine - 1].val() + tasks_matrix(machine - 1, this_task_index),
                    starts_matrix(machine, max_task_index).val() + tasks_matrix(machine, max_task_index)
                )) == Gecode::Int::ME_INT_FAILED)
                    return Gecode::ES_FAILED;
            }

            return home.ES_SUBSUMED(*this);
        }
    }

private:
    Gecode::ViewArray<Gecode::Int::IntView> machine_start_times;
};

template<class MySpace>
void allocateOnAllMachinesAfterFirst(MySpace& home, Gecode::IntVarArgs machine_start_times)
{
    Gecode::ViewArray<Gecode::Int::IntView> machine_start_times_view(home, machine_start_times);

    if (AllocateOnAllMachinesAfterFirst<MySpace>::post(home, machine_start_times_view) != Gecode::ES_OK)
    {
        home.fail();
    }
}
