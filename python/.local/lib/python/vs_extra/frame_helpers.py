from vapoursynth import VideoFrame
from numpy import asarray
import numpy as np


def get_planes(frame: VideoFrame) -> np.ndarray:
    """Wraps video frame into read-only numpy array."""

    if frame.format.num_planes == 1:
        return asarray(frame.get_read_array(0))

    assert frame.format.subsampling_h == 0
    assert frame.format.subsampling_w == 0

    return [asarray(frame.get_read_array(k))
            for k in range(frame.format.num_planes)]


def assign_planes(lhs, rhs, **props):
    """Assigns data to VapourSynth video frame."""

    lhs.props.update(props)

    for i, p in enumerate(map(np.squeeze, rhs)):
        np.copyto(asarray(lhs.get_write_array(i)), p)

    return lhs  # Not conventional in Py, but useful
