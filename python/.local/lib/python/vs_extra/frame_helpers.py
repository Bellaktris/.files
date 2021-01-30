from vapoursynth import COMPATBGR32
from vapoursynth import YUV420P8

from vapoursynth import VideoFrame
from numpy import asarray
import numpy as np


def get_planes(frame: VideoFrame) -> np.ndarray:
    """Wraps video frame into read-only numpy array."""

    if frame.format.id == COMPATBGR32:
        dt = np.dtype(('i4', [('bytes', 'u1', 4)]))
        A = asarray(frame.get_read_array(0))
        return A.view(dtype=dt)['bytes']

    if frame.format.num_planes == 1:
        return asarray(frame.get_read_array(0))

    return [asarray(frame.get_read_array(k))
            for k in range(frame.format.num_planes)]


def get_i420(frame: VideoFrame) -> np.ndarray:
    """Wraps video frame into read-only numpy array."""

    assert frame.format.id == YUV420P8
    planes = get_planes(frame)
    width = planes[0].shape[1]

    for p in range(len(planes)):
        planes[p] = np.ascontiguousarray(planes[p])

    concat = np.concatenate(planes, axis=None)
    return np.reshape(concat, (-1, width))


def assign_planes(lhs, rhs, **props):
    """Assigns data to VapourSynth video frame."""

    lhs.props.update(props)

    for i, p in enumerate(map(np.squeeze, rhs)):
        np.copyto(asarray(lhs.get_write_array(i)), p)

    return lhs  # Not conventional in Py, but useful
