// {{{
// "Copyright 2017 Yury Gitman"
// vim: ft=cpp:foldmethod=marker
//
#pragma clang diagnostic ignored "-Wdeprecated-declarations"

#include <unordered_set>
#include <unordered_map>
#include <functional>
#include <algorithm>
#include <iostream>
#include <valarray>
#include <iterator>
#include <iomanip>
#include <sstream>
#include <utility>
#include <cstdint>
#include <numeric>
#include <cstdlib>
#include <memory>
#include <vector>
#include <bitset>
#include <cstdio>
#include <string>
#include <stack>
#include <array>
#include <cmath>
#include <queue>
#include <ctime>
#include <deque>
#include <list>
#include <map>
#include <set>

using vec4u = std::array<uint8_t, 4>;
using vec4d = std::array<double, 4>;
using vec4f = std::array<float, 4>;
using vec4i = std::array<int, 4>;

using vec3u = std::array<uint8_t, 3>;
using vec3d = std::array<double, 3>;
using vec3f = std::array<float, 3>;
using vec3i = std::array<int, 3>;

using vec2u = std::array<uint8_t, 2>;
using vec2d = std::array<double, 2>;
using vec2f = std::array<float, 2>;
using vec2i = std::array<int, 2>;

#ifdef /**/ __clang__
#  include <prettyprinters.hpp>
#endif   // __clang__

#ifdef /**/ __clang__
#  include <folly/Format.h>
#endif   // __clang__

#ifdef /**/ __clang__
#  define dbg_assert(statement) \
    assert(statement)
#else    // __clang__
#  define dbg_assert(statement)
#endif   // __clang__

template<typename ...Ts>
void log(Ts&&... vs) {
#ifdef /**/ __clang__
  std::cerr << folly::format(vs, ...) << ' ';
  std::cerr << std::endl;
#endif   // __clang__
}

using namespace std; // NOLINT

template <typename Tp> std::vector<Tp>
static inline input_vector(int k)
  { std::vector<Tp> v(k); for (Tp& p : v) std::cin >> p; return v; }

template <typename Type> Type static inline input()
  { Type input_value; std::cin >> input_value; return input_value; }

template <typename Tp1, typename Tp2, typename... Ts>
static inline std::tuple<Tp1, Tp2, Ts...> input()
  { return make_tuple(input<Tp1>(), input<Tp2>(), input<Ts>()...); }

// }}}

// #define RUN_MULTIPLE_TESTS

int main() {
#ifdef /**/ RUN_MULTIPLE_TESTS
  int ntests = input<int>();
  for(int test = 0; test < ntests; ++test) {
    log("Running test #{}", test);
    log("----------------------");
#endif   // RUN_MULTIPLE_TESTS

    // ...

#ifdef /**/ RUN_MULTIPLE_TESTS
    log("----------------------");
  }
#endif   // RUN_MULTIPLE_TESTS

  return 0;
}
