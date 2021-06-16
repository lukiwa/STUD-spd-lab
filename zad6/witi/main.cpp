#include <iostream>
#include <numeric>

#include <gecode/int.hh>
#include <gecode/minimodel.hh>
#include <gecode/gist.hh>

#include "tasks.hpp"

int get_cost(const std::vector<int>& order, const Tasks& tasks)
{
    int cost = 0;

    int time = 0;
    for (int i : order)
    {
        time += tasks.p[i];

        if (time > tasks.d[i])
        {
            cost += tasks.w[i] * (time - tasks.d[i]);
        }
    }

    return cost;
}

class WitiSpace : public Gecode::IntMinimizeSpace
{
public:
    WitiSpace(const Tasks& tasks)
        : tasks_(tasks)
    {
        auto est_cost = get_est_cost();
        cost_ = Gecode::IntVar(*this, 0, est_cost);

        auto time_sum = std::accumulate(tasks_.p.begin(), tasks_.p.end(), 0, [](auto sum, auto el){
            return sum + el;
        });
        starts_ = Gecode::IntVarArray(*this, tasks_.p.size(), 0, time_sum);
        t_ = Gecode::IntVarArray(*this, tasks_.p.size(), 0, Gecode::Int::Limits::max);

        //////////////////////////////////////////

        Gecode::unary(*this, starts_, tasks_.p);

        for (int task = 0; task < tasks_.p.size(); ++task)
        {
            Gecode::rel(*this, t_[task] == Gecode::max(starts_[task] + (tasks_.p[task] - tasks_.d[task]), 0));
        }

        Gecode::linear(*this, tasks_.w, t_, Gecode::IRT_EQ, cost_);

        ////////////////////////////////////////////

        Gecode::branch(*this, starts_, Gecode::INT_VAR_MIN_MIN(), Gecode::INT_VAL_MIN());
    }

    WitiSpace(WitiSpace& other)
        : Gecode::IntMinimizeSpace(other)
        , tasks_(other.tasks_)
    {
        cost_.update(*this, other.cost_);
        starts_.update(*this, other.starts_);
        t_.update(*this, other.t_);
    }

    Gecode::Space* copy() override
    {
        return new WitiSpace(*this);
    }

    Gecode::IntVar cost() const override
    {
        return cost_;
    }

    void print(std::ostream& os) const
    {
        os << "starts: " << starts_
            << "\ncost: " << cost_
            << std::endl;
    }

    int get_est_cost()
    {
        std::vector<int> order(tasks_.p.size(), 0);
        std::iota(order.begin(), order.end(), 0);
        return get_cost(order, tasks_);
    }

private:
    const Tasks& tasks_;

    Gecode::IntVar cost_;
    Gecode::IntVarArray starts_, t_;
};

int main()
{
    auto tasks = load_file("data.20");
    WitiSpace space(*tasks);

    Gecode::Gist::Print<WitiSpace> p("Print solution");
    Gecode::Gist::Options o;
    o.inspect.click(&p);
    Gecode::Gist::bab(&space, o);
}
