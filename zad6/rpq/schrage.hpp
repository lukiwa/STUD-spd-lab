#pragma once

#include <algorithm>
#include <vector>

#include <boost/range/adaptors.hpp>
#include <boost/range/algorithm.hpp>
#include <gecode/int.hh>

#include "tasks.hpp"

std::tuple<Gecode::IntArgs, int> schrage(const Tasks& tasks)
{
    Gecode::IntArgs order;

    const auto ordered_tasks = tasks.object_view() | boost::adaptors::indexed(0);
    std::vector N(ordered_tasks.begin(), ordered_tasks.end());
    decltype(N) G;

    const auto r_comp = [](const auto& lhs, const auto& rhs){
        return lhs.value().r < rhs.value().r;
    };

    const auto q_comp = [](const auto& lhs, const auto& rhs){
        return lhs.value().q < rhs.value().q;
    };

    const auto min_el_1 = boost::range::min_element(N, r_comp);
    assert(min_el_1 != N.end());

    int t = min_el_1->value().r;
    int cmax = 0;

    while (!N.empty() || !G.empty())
    {
        while (!N.empty())
        {
            const auto min_el = boost::range::min_element(N, r_comp);
            if (min_el->value().r > t)
            {
                break;
            }
            G.push_back(*min_el);
            N.erase(min_el);
        }

        if (G.empty())
        {
            t = boost::range::min_element(N, r_comp)->value().r;
        }
        else
        {
            const auto task = boost::range::max_element(G, q_comp);
            order << task->index();
            t += task->value().p;

            cmax = std::max(cmax, t + task->value().q);

            G.erase(task);
        }
    }

    assert(order.size() == tasks.size());
    return {order, cmax};
}

template<class Iterable>
int get_cmax(const Tasks& tasks, const Iterable& args)
{
    int t = 0;
    int cmax = 0;

    for (const auto task_index : args)
    {
        if (t < tasks.r[task_index])
        {
            t = tasks.r[task_index];
        }

        t += tasks.p[task_index];

        if (cmax < t + tasks.q[task_index])
        {
            cmax = t + tasks.q[task_index];
        }
    }

    return cmax;
}
