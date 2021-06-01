#pragma once

#include <boost/range/irange.hpp>
#include <boost/range/adaptors.hpp>

#include <gecode/int.hh>

struct Tasks
{
    Gecode::IntArgs r, p, q;

    Tasks(Gecode::IntArgs r, Gecode::IntArgs p, Gecode::IntArgs q)
        : r(std::move(r))
        , p(std::move(p))
        , q(std::move(q))
    {
        assert(r.size() == p.size());
        assert(r.size() == q.size());
    }

    auto object_view() const
    {
        struct Task {
            int r, p, q;
        };

        return boost::irange(0, r.size()) | boost::adaptors::transformed([this](int idx){
            return Task{r[idx], p[idx], q[idx]};
        });
    }

    auto size() const
    {
        return r.size();
    }
};
