#include <algorithm>
#include <numeric>
#include <iomanip>
#include <chrono>

#include <boost/range/algorithm.hpp>

#include <gecode/int.hh>
#include <gecode/gist.hh>
#include <gecode/minimodel.hh>

#include "tasks.hpp"
#include "load_file.hpp"
#include "schrage.hpp"


class RPQSpace : public Gecode::IntMinimizeSpace
{
public:
    RPQSpace(const Tasks& info)
        : info(info)
    {
        int est_cmax = estimateWithDefaultOrder();
        c_max = Gecode::IntVar(*this, 0, est_cmax);
        S = Gecode::IntVarArray(*this, info.size(), 0, est_cmax);
        C = Gecode::IntVarArray(*this, info.size(), 0, est_cmax);

        ////////////////////////////////////////////////

        Gecode::IntVarArgs c_plus_q;
        for (int i = 0; i < info.size(); i++)
        {
            Gecode::rel(*this, S[i] >= info.r[i]);
            Gecode::rel(*this, C[i] == S[i] + info.p[i]);

            c_plus_q << Gecode::expr(*this, C[i] + info.q[i]);
        }
        Gecode::rel(*this, c_max == Gecode::max(c_plus_q));

        Gecode::unary(*this, S, info.p);

        /////////////////////////////////////////

        Gecode::branch(*this, S, Gecode::INT_VAR_MIN_MIN(), Gecode::INT_VAL_MIN());
    }

    RPQSpace(RPQSpace& other)
        : Gecode::IntMinimizeSpace(other)
        , info(other.info)
    {
        C.update(*this, other.C);
        S.update(*this, other.S);
        c_max.update(*this, other.c_max);
    }

    Gecode::Space* copy() override
    {
        return new RPQSpace(*this);
    }

    Gecode::IntVar cost() const override
    {
        return c_max;
    }

    void print(std::ostream& os) const
    {
        os << "S: " << S
            << "\nC:" << C
            << "\ncmax: " << c_max
            << std::endl;
    }

    std::vector<int> getOrder()
    {
        assert(std::all_of(S.begin(), S.end(), [](const auto& el){ return el.assigned(); }));

        std::vector<std::pair<int, int>> partial_result;
        for (int i = 0; i < S.size(); ++i)
        {
            partial_result.push_back({i, S[i].val()});
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

private:
    int estimateWithDefaultOrder()
    {
        auto [order, cmax] = schrage(info);
        return cmax;
    }

    const Tasks& info;
    Gecode::IntVarArray S, C;
    Gecode::IntVar c_max;
};

int main(int argc, char* argv[])
{
    if (argc != 2)
    {
        std::cout << "usage: ???" << std::endl;
        return -1;
    }

    constexpr bool USE_GIST = false;

    const auto tasks = load_file(argv[1]);
    RPQSpace space(tasks);

    if (USE_GIST)
    {
        Gecode::Gist::Print<RPQSpace> p("Print solution");
        Gecode::Gist::Options o;
        o.inspect.click(&p);
        Gecode::Gist::bab(&space, o);
    }
    else
    {
        const auto now = std::chrono::high_resolution_clock::now();

        Gecode::Search::Options o;
        Gecode::Search::TimeStop stop(15 * 1000);
        o.stop = &stop;
        Gecode::BAB<RPQSpace> engine(&space, o);

        while (auto* solution = engine.next())
        {
            std::cout << "cmax: " << solution->cost() << ", other cmax: " << get_cmax(tasks, solution->getOrder()) << std::endl;
            delete solution;
        }

        const auto stop_time = std::chrono::high_resolution_clock::now();
        std::cout << "time: " << std::chrono::duration_cast<std::chrono::microseconds>(stop_time - now).count() / 1000.0 << std::endl;
    }
}
