// Ceres Solver - A fast non-linear least squares minimizer
// Copyright 2015 Google Inc. All rights reserved.
// http://ceres-solver.org/
//
// Redistribution  and  use  in  source  and  binary  forms,  with  or  without
// modification, are permitted provided that the following conditions are met:
//
// * Redistributions of source code must retain the above copyright notice,
//   this list of conditions and the following disclaimer.
//
// * Redistributions in binary form must reproduce the above copyright notice,
//   this list of conditions and the following disclaimer in the documentation
//   and/or other materials provided with the distribution.
//
// * Neither the name of Google Inc. nor the names of its contributors may be
//   used to endorse or promote products derived from this software without
//   specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE  COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY  EXPRESS OR IMPLIED WARRANTIES,  INCLUDING, BUT NOT LIMITED  TO, THE
// IMPLIED WARRANTIES OF  MERCHANTABILITY AND FITNESS FOR  A PARTICULAR PURPOSE
// ARE  DISCLAIMED. IN  NO  EVENT  SHALL THE  COPYRIGHT  OWNER OR  CONTRIBUTORS
// BE  LIABLE FOR  ANY  DIRECT, INDIRECT,  INCIDENTAL,  SPECIAL, EXEMPLARY,  OR
// CONSEQUENTIAL  DAMAGES  (INCLUDING,  BUT  NOT  LIMITED  TO,  PROCUREMENT  OF
// SUBSTITUTE GOODS  OR SERVICES; LOSS  OF USE,  DATA, OR PROFITS;  OR BUSINESS
// INTERRUPTION)  HOWEVER CAUSED  AND ON  ANY THEORY  OF LIABILITY,  WHETHER IN
// CONTRACT,  STRICT LIABILITY,  OR  TORT (INCLUDING  NEGLIGENCE OR  OTHERWISE)
// ARISING IN ANY WAY  OUT OF THE USE OF THIS SOFTWARE, EVEN  IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.
//
// Author: keir@google.com (Keir Mierle)
//
// A  simple implementation  of N-dimensional  dual numbers,  for automatically
// computing exact derivatives of functions.
//
// While    a   complete    treatment   of    the   mechanics    of   automatic
// differentation    is    beyond   the    scope    of    this   header    (see
// http://en.wikipedia.org/wiki/Automatic_differentiation  for   details),  the
// basic idea is to extend normal  arithmetic with an extra element, "e," often
// denoted with the  greek symbol epsilon, such that  e != 0 but e^2  = 0. Dual
// numbers are  extensions of  the real numbers  analogous to  complex numbers:
// whereas complex numbers augment the reals by introducing an imaginary unit i
// such that  i^2 = -1, dual  numbers introduce an "infinitesimal"  unit e such
// that e^2 = 0. Dual numbers have two components: the "real" component and the
// "infinitesimal" component, generally written as  x + y*e. Surprisingly, this
// leads to a convenient method for computing exact derivatives without needing
// to manipulate complicated symbolic expressions.
//
// For example, consider the function
//
//   f(x) = x^2 ,
//
// evaluated at 10. Using normal arithmetic, f(10) = 100, and df/dx(10) = 20.
// Next, augument 10 with an infinitesimal to get:
//
//   f(10 + e) = (10 + e)^2
//             = 100 + 2 * 10 * e + e^2
//             = 100 + 20 * e       -+-
//                     --            |
//                     |             +--- This is zero, since e^2 = 0
//                     |
//                     +----------------- This is df/dx!
//
// Note that the derivative of f with  respect to x is simply the infinitesimal
// component of the value  of f(x + e). So, in order to  take the derivative of
// any function, it  is only necessary to replace the  numeric "object" used in
// the function with  one extended with infinitesimals. The  class Jet, defined
// in this header, is one such example of this, where substitution is done with
// templates.
//
// To  handle derivatives  of  functions taking  multiple arguments,  different
// infinitesimals are  used, one for each  variable to take the  derivative of.
// For example, consider a scalar function of two scalar parameters x and y:
//
//   f(x, y) = x^2 + x * y
//
// Following the  technique above, to  compute the derivatives df/dx  and df/dy
// for f(1, 3) involves doing two evaluations  of f, the first time replacing x
// with x + e, the second time replacing y with y + e.
//
// For df/dx:
//
//   f(1 + e, y) = (1 + e)^2 + (1 + e) * 3
//               = 1 + 2 * e + 3 + 3 * e
//               = 4 + 5 * e
//
//               --> df/dx = 5
//
// For df/dy:
//
//   f(1, 3 + e) = 1^2 + 1 * (3 + e)
//               = 1 + 3 + e
//               = 4 + e
//
//               --> df/dy = 1
//
// To take the  gradient of f with the implementation  of dual numbers ("jets")
// in  this file,  it  is necessary  to  create  a single  jet  type which  has
// components for the  derivative in x and  y, and passing them  to a templated
// version of f:
//
//   template<typename T>
//   T f(const T &x, const T &y) {
//     return x * x + x * y;
//   }
//
//   // The "2" means there should be 2 dual number components.
//   Jet<double, 2> x(1, 0);  // Pick the 0th dual number for x.
//   Jet<double, 2> y(3, 1);  // Pick the 1st dual number for y.
//   Jet<double, 2> z = f(x, y);
//
//   std::cout << z << std::endl;
//
// For  the  more mathematically  inclined,  this  file implements  first-order
// "jets". A 1st order jet is an element of the ring
//
//   T[N] = T[t_1, ..., t_N] / (t_1, ..., t_N)^2
//
// which essentially means that each jet  consists of a "scalar" value 'a' from
// T and a 1st order perturbation vector 'v' of length N:
//
//   x = a + \sum_i v[i] t_i
//
// A shorthand is to write an element as x = a + u, where u is the pertubation.
// Then, the  main point about  the arithmetic of jets  is that the  product of
// perturbations is zero:
//
//   (a + u) * (b + v) = ab + av + bu + uv
//                     = ab + (av + bu) + 0
//
// which is what operator* implements below. Addition is simpler:
//
//   (a + u) + (b + v) = (a + b) + (u + v).
//
// The only remaining  question is how to  evaluate the function of  a jet, for
// which we use the chain rule:
//
//   f(a + u) = f(a) + f'(a) u
//
// where f'(a) is the (scalar) derivative of f at a.

#ifndef PUBLIC_JET_HPP_
#define PUBLIC_JET_HPP_

#include <Eigen/Core>
#include <cmath>

template <typename Tp, int N>
struct Jet {
  // Default-construct "a"  because otherwise  this can lead  to false
  // errors  about uninitialized  uses when  other classes  relying on
  // default constructed Tp  (where Tp is a Jet<Tp,  N>). This usually
  // only happens  in opt  mode. Note that  the C++  standard mandates
  // that e.g. default constructed doubles are initialized to 0.0; see
  // sections 8.5 of the C++03 standard.
  EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE Jet() : a() { v.setZero(); }

  // Constructor from scalar: a + [0, ...].
  EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE explicit
    Jet(const Tp& value) { a = value; v.setZero(); }

  // Constructor from scalar plus variable: a + [0, ..., 1, ... 0].
  EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
  Jet(const Tp& value, int k) { a = value; v.setZero(); v[k] = Tp(1.0); }

  // Constructor from scalar and vector part
  // ---------------------------------------
  // The use of Eigen::DenseBase allows Eigen expressions to be passed
  // in  without being  fully evaluated until  they are assigned  to v
  template<typename Derived> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
  Jet(const Tp& a, const Eigen::DenseBase<Derived> &v) : a(a), v(v) {}

  EIGEN_MAKE_ALIGNED_OPERATOR_NEW

  EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
  Jet<Tp, N>& operator+=(const Jet<Tp, N> &y)
    { *this = *this + y; return *this; }

  EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
  Jet<Tp, N>& operator-=(const Jet<Tp, N> &y)
    { *this = *this - y; return *this; }

  EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
  Jet<Tp, N>& operator*=(const Jet<Tp, N> &y)
    { *this = *this * y; return *this; }

  EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
  Jet<Tp, N>& operator/=(const Jet<Tp, N> &y)
    { *this = *this / y; return *this; }

#ifdef CEREAL_SERIALIZE_FUNCTION_NAME

  friend class cereal::access;

  template<class Archive>
  void serialize(Archive& archive) {
    archive(cereal::make_nvp("[real]", a));
    archive(cereal::make_nvp("[dual]", v));
  }

#endif  // CEREAL_SERIALIZE_FUNCTION_NAME

  // Jet dimensionality.
  enum { kDimensions = N };

  // The scalar part.
  Tp a;

  // The infinitesimal part.
  Eigen::Matrix<Tp, N, 1, Eigen::AutoAlign> v;
};

// Unary +
template<typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> const& operator+(const Jet<Tp, N>& f) { return f; }

// Unary -
template<typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> operator-(const Jet<Tp, N>&f) { return Jet<Tp, N>(-f.a, -f.v); }

// Binary +
template<typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> operator+(const Jet<Tp, N>& f, const Jet<Tp, N>& g)
 { return Jet<Tp, N>(f.a + g.a, f.v + g.v); }

// Binary + with a scalar: x + s
template<typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> operator+(const Jet<Tp, N>& f, Tp s)
  { return Jet<Tp, N>(f.a + s, f.v); }

// Binary + with a scalar: s + x
template<typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> operator+(Tp s, const Jet<Tp, N>& f)
  { return Jet<Tp, N>(f.a + s, f.v); }

// Binary -
template<typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> operator-(const Jet<Tp, N>& f, const Jet<Tp, N>& g)
  { return Jet<Tp, N>(f.a - g.a, f.v - g.v); }

// Binary - with a scalar: x - s
template<typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> operator-(const Jet<Tp, N>& f, Tp s)
  { return Jet<Tp, N>(f.a - s, f.v); }

// Binary - with a scalar: s - x
template<typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> operator-(Tp s, const Jet<Tp, N>& f)
  { return Jet<Tp, N>(s - f.a, -f.v); }

// Binary *
template<typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> operator*(const Jet<Tp, N>& f, const Jet<Tp, N>& g)
 { return Jet<Tp, N>(f.a * g.a, f.a * g.v + f.v * g.a); }

// Binary * with a scalar: x * s
template<typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> operator*(const Jet<Tp, N>& f, Tp s)
  { return Jet<Tp, N>(f.a * s, f.v * s); }

// Binary * with a scalar: s * x
template<typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> operator*(Tp s, const Jet<Tp, N>& f)
  { return Jet<Tp, N>(f.a * s, f.v * s); }

// Binary /
template<typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> operator/(const Jet<Tp, N>& f, const Jet<Tp, N>& g) {
  //   a + u   (a + u)(b - v)   (a + u)(b - v)
  //   ----- = -------------- = --------------
  //   b + v   (b + v)(b - v)        b^2
  return Jet<Tp, N>(f.a / g.a, (f.v - f.a / g.a * g.v) / g.a);
}

// Binary / with a scalar: s / x
template<typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> operator/(Tp s, const Jet<Tp, N>& g)
  { return Jet<Tp, N>(s / g.a, -s * g.v / (g.a * g.a)); }

// Binary / with a scalar: x / s
template<typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> operator/(const Jet<Tp, N>& f, Tp s)
  { return Jet<Tp, N>(f.a / s, f.v / s); }

// Binary comparison operators for both scalars and jets.
#define CERES_DEFINE_JET_COMPARISON_OPERATOR(op)                                    \
  template<typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE                \
  bool operator op(const Tp& s, const Jet<Tp, N>& g) { return s op g.a; }           \
                                                                                    \
  template<typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE                \
  bool operator op(const Jet<Tp, N>& f, const Tp& s) { return f.a op s; }           \
                                                                                    \
  template<typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE                \
  bool operator op(const Jet<Tp, N>& f, const Jet<Tp, N>& g) { return f.a op g.a; } \

CERES_DEFINE_JET_COMPARISON_OPERATOR(< )
CERES_DEFINE_JET_COMPARISON_OPERATOR(<=)
CERES_DEFINE_JET_COMPARISON_OPERATOR(> )
CERES_DEFINE_JET_COMPARISON_OPERATOR(>=)
CERES_DEFINE_JET_COMPARISON_OPERATOR(==)
CERES_DEFINE_JET_COMPARISON_OPERATOR(!=)

#undef CERES_DEFINE_JET_COMPARISON_OPERATOR

// In general, f(a + h) ~= f(a) + f'(a) h, via the chain rule.

using std::abs;  // abs(x + h) ~= x + h or -(x + h)
template <typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> abs(const Jet<Tp, N>& f) { return f.a < Tp(0.0) ? -f : f; }

using std::log;  // log(a + h) ~= log(a) + h / a
template <typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> log(const Jet<Tp, N>& f) { return Jet<Tp, N>(log(f.a), f.v / f.a); }

using std::exp;  // exp(a + h) ~= exp(a) + exp(a) h
template <typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> exp(const Jet<Tp, N>& f) { return Jet<Tp, N>(exp(f.a), exp(f.a) * f.v); }

using std::sqrt;  // sqrt(a + h) ~= sqrt(a) + h / (2 sqrt(a))
template <typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> sqrt(const Jet<Tp, N>& f)
  { return Jet<Tp, N>(sqrt(f.a), f.v / (Tp(2.0) * sqrt(f.a))); }

using std::cos;  // cos(a + h) ~= cos(a) - sin(a) h
template <typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> cos(const Jet<Tp, N>& f)
  { return Jet<Tp, N>(cos(f.a), - sin(f.a) * f.v); }

using std::acos;  // acos(a + h) ~= acos(a) - 1 / sqrt(1 - a^2) h
template <typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> acos(const Jet<Tp, N>& f)
  { return Jet<Tp, N>(acos(f.a), f.v / sqrt(Tp(1.0) - f.a * f.a)); }

using std::sin;  // sin(a + h) ~= sin(a) + cos(a) h
template <typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> sin(const Jet<Tp, N>& f) { return Jet<Tp, N>(sin(f.a), cos(f.a) * f.v); }

using std::asin;  // asin(a + h) ~= asin(a) + 1 / sqrt(1 - a^2) h
template <typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> asin(const Jet<Tp, N>& f)
  { return Jet<Tp, N>(asin(f.a), f.v / sqrt(Tp(1.0) - f.a * f.a)); }

using std::tan;  // tan(a + h) ~= tan(a) + (1 + tan(a)^2) h
template <typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> tan(const Jet<Tp, N>& f)
  { return Jet<Tp, N>(tan(f.a), Tp(1.0) + tan(f.a) * tan(f.a) * f.v); }

using std::atan;  // atan(a + h) ~= atan(a) + 1 / (1 + a^2) h
template <typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> atan(const Jet<Tp, N>& f)
  { return Jet<Tp, N>(atan(f.a), f.v / (Tp(1.0) + f.a * f.a)); }

using std::sinh;  // sinh(a + h) ~= sinh(a) + cosh(a) h
template <typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> sinh(const Jet<Tp, N>& f)
  { return Jet<Tp, N>(sinh(f.a), cosh(f.a) * f.v); }

using std::cosh;  // cosh(a + h) ~= cosh(a) + sinh(a) h
template <typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> cosh(const Jet<Tp, N>& f)
  { return Jet<Tp, N>(cosh(f.a), sinh(f.a) * f.v); }

using std::tanh;  // tanh(a + h) ~= tanh(a) + (1 - tanh(a)^2) h
template <typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> tanh(const Jet<Tp, N>& f)
  { return Jet<Tp, N>(tan(f.a), (Tp(1.0) - tan(f.a) * tan(f.a)) * f.v); }

using std::atan2;

// atan2(b + db, a + da) ~= atan2(b, a) + (- b da + a db) / (a^2 + b^2)
//
// In words: the rate of change of theta is 1/r times the rate of
// change of (x, y) in the positive angular direction.
template <typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> atan2(const Jet<Tp, N>& g, const Jet<Tp, N>& f) {
  // Note order of arguments:
  //
  //   f = a + da
  //   g = b + db

  Tp const tmp = Tp(1.0) / (f.a * f.a + g.a * g.a);
  return Jet<Tp, N>(atan2(g.a, f.a), tmp * (- g.a * f.v + f.a * g.v));
}

using std::pow;

// pow -- base is a differentiable function, exponent is a constant.
// (a+da)^p ~= a^p + p*a^(p-1) da
template <typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> pow(const Jet<Tp, N>& f, double g) {
  Tp const tmp = g * pow(f.a, g - Tp(1.0));
  return Jet<Tp, N>(pow(f.a, g), tmp * f.v);
}

// pow -- base is a constant, exponent is a differentiable function.
// We have various special cases, see the comment for pow(Jet, Jet) for
// analysis:
//
// 1. For f > 0 we have: (f)^(g + dg) ~= f^g + f^g log(f) dg
//
// 2. For f == 0 and g > 0 we have: (f)^(g + dg) ~= f^g
//
// 3. For f < 0 and integer g we have: (f)^(g + dg) ~= f^g but if dg
// != 0, the derivatives are not defined and we return NaN.

template <typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> pow(double f, const Jet<Tp, N>& g) {
  if (f == 0 && g.a > 0) {
    // Handle case 2.
    return Jet<Tp, N>(Tp(0.0));
  }
  if (f < 0 && g.a == floor(g.a)) {
    // Handle case 3.
    Jet<Tp, N> ret(pow(f, g.a));
    for (int i = 0; i < N; i++) {
      if (g.v[i] != Tp(0.0)) {
        // Return a NaN when g.v != 0.
        ret.v[i] = std::numeric_limits<Tp>::quiet_NaN();
      }
    }
    return ret;
  }
  // Handle case 1.
  Tp const tmp = pow(f, g.a);
  return Jet<Tp, N>(tmp, log(f) * tmp * g.v);
}

// pow -- both base and exponent are differentiable functions. This has a
// variety of special cases that require careful handling.
//
// 1. For f > 0:
//    (f + df)^(g + dg) ~= f^g + f^(g - 1) * (g * df + f * log(f) * dg)
//    The numerical evaluation of f * log(f) for f > 0 is well behaved, even for
//    extremely small values (e.g. 1e-99).
//
// 2. For f == 0 and g > 1: (f + df)^(g + dg) ~= 0
//    This cases is needed because log(0) can not be evaluated in the f > 0
//    expression. However the function f*log(f) is well behaved around f == 0
//    and its limit as f-->0 is zero.
//
// 3. For f == 0 and g == 1: (f + df)^(g + dg) ~= 0 + df
//
// 4. For f == 0 and 0 < g < 1: The value is finite but the derivatives are not.
//
// 5. For f == 0 and g < 0: The value and derivatives of f^g are not finite.
//
// 6. For f == 0 and g == 0: The C standard incorrectly defines 0^0 to be 1
//    "because there are applications that can exploit this definition". We
//    (arbitrarily) decree that derivatives here will be nonfinite, since that
//    is consistent with the behavior for f == 0, g < 0 and 0 < g < 1.
//    Practically any definition could have been justified because mathematical
//    consistency has been lost at this point.
//
// 7. For f < 0, g integer, dg == 0: (f + df)^(g + dg) ~= f^g + g * f^(g - 1) df
//    This is equivalent to the case where f is a differentiable function and g
//    is a constant (to first order).
//
// 8. For f < 0, g integer, dg != 0: The value is finite but the derivatives are
//    not, because any change in the value of g moves us away from the point
//    with a real-valued answer into the region with complex-valued answers.
//
// 9. For f < 0, g noninteger: The value and derivatives of f^g are not finite.

template <typename Tp, int N> EIGEN_DEVICE_FUNC EIGEN_STRONG_INLINE
Jet<Tp, N> pow(const Jet<Tp, N>& f, const Jet<Tp, N>& g) {
  if (f.a == 0 && g.a >= 1) {
    // Handle cases 2 and 3.
    if (g.a > 1) {
      return Jet<Tp, N>(Tp(0.0));
    }
    return f;
  }
  if (f.a < 0 && g.a == floor(g.a)) {
    // Handle cases 7 and 8.
    Tp const tmp = g.a * pow(f.a, g.a - Tp(1.0));
    Jet<Tp, N> ret(pow(f.a, g.a), tmp * f.v);
    for (int i = 0; i < N; i++) {
      if (g.v[i] != Tp(0.0)) {
        // Return a NaN when g.v != 0.
        ret.v[i] = std::numeric_limits<Tp>::quiet_NaN();
      }
    }
    return ret;
  }
  // Handle the remaining cases. For cases 4,5,6,9 we allow the log() function
  // to generate -HUGE_VAL or NaN, since those cases result in a nonfinite
  // derivative.
  Tp const tmp1 = pow(f.a, g.a);
  Tp const tmp2 = g.a * pow(f.a, g.a - Tp(1.0));
  Tp const tmp3 = tmp1 * log(f.a);
  return Jet<Tp, N>(tmp1, tmp2 * f.v + tmp3 * g.v);
}

template <typename Tp, int N>
std::ostream &operator<<(std::ostream &s, const Jet<Tp, N>& z)
  { return s << "[" << z.a << "; " << z.v.transpose() << "]"; }

namespace Eigen {

// Creating  a  specialization of  NumTraits  enables
// placing Jet  objects inside Eigen  arrays, getting
// all the goodness of Eigen combined with autodiff.
template<typename Tp, int N>
struct NumTraits<Jet<Tp, N> > {
  typedef Jet<Tp, N> Real;
  typedef Jet<Tp, N> NonInteger;
  typedef Jet<Tp, N> Nested;
  typedef Jet<Tp, N> Literal;

  // For Jet types, multiplication is more expensive than addition.
  enum { IsComplex = 0, IsInteger = 0, IsSigned, ReadCost = 1, AddCost = 1,
         MulCost = 3, HasFloatingPoint = 1, RequireInitialization = 1 };

  // Assuming that for Jets, division is as expensive as multiplication.
  template<bool Vectorized> struct Div { enum { Cost = 3 }; };

  static Jet<Tp, N> dummy_precision()
    { return Jet<Tp, N>(1e-12); }

  static inline Real epsilon()
    { return Real(std::numeric_limits<Tp>::epsilon()); }

  static inline int digits10() { return 0; }
};

}  // namespace Eigen

#endif  // PUBLIC_JET_HPP_
