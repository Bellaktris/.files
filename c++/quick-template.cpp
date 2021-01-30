// {{{
// "Copyright 2017 Yury Gitman"
// vim: ft=cpp:foldmethod=marker

#include <memory.h>

#include <cstdint>
#include <algorithm>
#include <bitset>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <deque>
#include <functional>
#include <iomanip>
#include <iostream>
#include <list>
#include <map>
#include <numeric>
#include <queue>
#include <set>
#include <sstream>
#include <stack>
#include <array>
#include <string>
#include <utility>
#include <vector>
#include <valarray>
#include <iterator>
#include <unordered_set>
#include <unordered_map>

#ifdef /**/ __clang__
#  include <prettyprinters.hpp>
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
  std::cerr << "stderr logging: ";
  ((std::cerr << vs << ' '), ...);
  std::cerr << std::endl;
#endif   // __clang__
}

using namespace std; // NOLINT

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

template <typename Tp> std::vector<Tp>
static inline input_vector(int k)
  { std::vector<Tp> v(k); for (Tp& p : v) std::cin >> p; return v; }

template <typename Tp, int sz>
std::array<Tp, sz> static inline input()
  { std::array<Tp, sz> A; for (Tp& v : A) std::cin >> v; return A; }

template <typename Type> Type static inline input()
  { Type input_value; std::cin >> input_value; return input_value; }

template <typename Tp1, typename Tp2, typename... Ts>
static inline std::tuple<Tp1, Tp2, Ts...> input()
  { return make_tuple(input<Tp1>(), input<Tp2>(), input<Ts>()...); }

// }}}

int main() {
#ifdef /**/ RUN_MULTIPLE_TESTS
  int ntests = input<int>();
  for(int current_test = 0; current_test < ntests; ++current_test) {
  std::cout << "Running test #" << current_test << std::endl;
  std::cout << "---------------" << std::endl << std::endl;
#endif   // RUN_MULTIPLE_TESTS

  // put your code here...

#ifdef /**/ RUN_MULTIPLE_TESTS
  std::cout << std::endl;
  }
#endif   // RUN_MULTIPLE_TESTS

  return 0;
}
