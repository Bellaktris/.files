#ifdef EIGEN_DENSEBASE_H

#ifdef CEREAL_SERIALIZE_FUNCTION_NAME

friend class cereal::access;

template <class Archive> void serialize(Archive& archive) {
  Index rows = this->rows(), cols = this->cols();

  if (RowsAtCompileTime == Dynamic)
    archive(cereal::make_nvp("rows", rows));

  if (ColsAtCompileTime == Dynamic)
    archive(cereal::make_nvp("cols", cols));

  this->derived().resize(rows, cols);

  const Scalar* _data = this->derived().eval().data();
  Scalar* data = const_cast<Scalar*>(_data);

  for (Index i = 0; i < this->size(); ++i) {
    char label[20];

#if defined(_MSC_VER) && _MSC_VER <= 1900
# define SNPRINTF _snprintf_s
#else
# define SNPRINTF std::snprintf
#endif  // defined(_MSC_VER) && _MSC_VER >= 1900

    if (rows == 1 || cols == 1)
      SNPRINTF(label, sizeof(label), "[%ld]", i);

    if (rows != 1 && cols != 1) {
      if constexpr(IsRowMajor)
        SNPRINTF(label, sizeof(label), "[%ld, %ld]", i / cols, i % cols);
      else
        SNPRINTF(label, sizeof(label), "[%ld, %ld]", i % rows, i / rows);
    }

#undef SNPRINTF  // if defined(_MSC_VER) && _MSC_VER <= 1900

    archive(cereal::make_nvp(label, data[i]));
  }
}

/*! Read Eigen objects */
friend EIGEN_STRONG_INLINE std::istream& operator >>
(std::istream& input_stream, const DenseBase& mat) {
	for (size_t row = 0; row < mat.rows(); row++)
		for (size_t col = 0; col < mat.cols(); col++)
			input_stream >> mat(row, col);

	return static_cast<std::istream&>(input);
}

/*! Begin function for compatibility with stl functions */
EIGEN_STRONG_INLINE EIGEN_DEVICE_FUNC
const Scalar* begin() const { return &this->coeff(0, 0); }

/*! End function for compatibility with stl functions */
EIGEN_STRONG_INLINE EIGEN_DEVICE_FUNC
const Scalar* end() const { return &this->coeff(0, 0) + this->size(); }

/*! Evaluate Eigen expression into the given location */
template<int MapOptions = Eigen::Aligned> EIGEN_STRONG_INLINE
EIGEN_DEVICE_FUNC void copyTo(Scalar* data) const {
  typedef typename internal::eval<Derived>::type _MatrixType;
  typedef typename internal::remove_all<_MatrixType>::type MatrixType;
  Eigen::Map<MatrixType, MapOptions>(data, rows(), cols()) = derived();
}

#endif  // CEREAL_SERIALIZE_FUNCTION_NAME
#endif  // EIGEN_DENSEBASE_H
