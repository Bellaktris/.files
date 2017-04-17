#ifdef EIGEN_QUATERNION_H
#ifdef CEREAL_SERIALIZE_FUNCTION_NAME

friend class cereal::access;

template<class Archive>
void serialize(Archive& archive) {
  archive(cereal::make_nvp("x", this->x()));
  archive(cereal::make_nvp("y", this->y()));
  archive(cereal::make_nvp("z", this->z()));
  archive(cereal::make_nvp("w", this->w()));
}

#endif  // CEREAL_SERIALIZE_FUNCTION_NAME
#endif  // EIGEN_QUATERNION_H
