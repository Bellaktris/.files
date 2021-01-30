from ctypes.util import find_library
from vapoursynth import core
from types import ModuleType
from os.path import exists
import vapoursynth as vs
from sys import stderr


VSClip = vs.VideoNode


def check_plugin(name: str, ns: ModuleType) -> bool:
    return not hasattr(core, ns) and name


imwri_p = find_library('imwri')
ffms2_p = find_library('ffms2')


if check_plugin(ffms2_p, 'ffms2'):
    core.std.LoadPlugin(ffms2_p)

if check_plugin(imwri_p, 'imwri'):
    core.std.LoadPlugin(imwri_p)


def Yuv2RGB24(video: VSClip) -> VSClip:
    """Converts input video to RGB24."""
    kw = {'matrix_in_s': '709', 'format': vs.RGB24}
    assert video.format.color_family == vs.YUV
    assert video.format.bytes_per_sample == 1
    return core.resize.Bilinear(video, **kw)


def Yuv2GRAY8(video: VSClip) -> VSClip:
    """Converts input video to GRAY8."""
    assert video.format.color_family == vs.YUV
    assert video.format.bytes_per_sample == 1
    return core.std.ShufflePlanes(video, 0, vs.GRAY)


def Yuv2GRAYS(video: VSClip) -> VSClip:
    """Converts input video to GRAYS."""
    return core.std.Expr(Yuv2GRAY8(video), "x 255 /", vs.GRAYS)


def Yuv2BGR24(video: VSClip) -> VSClip:
    """Converts input video to BGR24."""
    video, idxs, fmt = Yuv2RGB24(video), [2, 1, 0], vs.RGB
    return core.std.ShufflePlanes(video, idxs, fmt)


def Yuv2RGBS(video: VSClip) -> VSClip:
    """Converts input video to RGBS."""
    return core.std.Expr(Yuv2RGB24(video), "x 255 /", vs.RGBS)


def Yuv2BGRS(video: VSClip) -> VSClip:
    """Converts input video to BGRS."""
    return core.std.Expr(Yuv2BGR24(video), "x 255 /", vs.RGBS)


def Yuv2COMPATBGR32(video: VSClip) -> VSClip:
    """Converts input video to interleaved BGR32."""
    kw = {'matrix_in_s': '709', 'format': vs.COMPATBGR32}

    assert video.format.color_family == vs.YUV
    return core.resize.Bilinear(video, **kw)


def ScaleFitSize(clip: VSClip, bboxshape) -> VSClip:
    """Ensure that input video fits into bbox."""

    hcoeff = clip.height / bboxshape[1]
    wcoeff = clip.width / bboxshape[0]
    coeff = max(hcoeff, wcoeff, 1.0)

    height = int(clip.height / coeff // 2 * 2)
    width = int(clip.width / coeff // 2 * 2)

    scaled_video = core.resize.Bilinear(clip, width, height)
    return clip if coeff == 1.0 else scaled_video


def ScalePadFitSize(clip: VSClip, bboxshape) -> VSClip:
    """Fit input video fits into bbox."""

    clip = ScaleFitSize(clip, bboxshape)
    dy = (bboxshape[1] - clip.height) // 2
    dx = (bboxshape[0] - clip.width) // 2

    A, B = dx // 2 * 2, (dx + 1) // 2 * 2
    C, D = dy // 2 * 2, (dy + 1) // 2 * 2

    return core.std.AddBorders(clip, A, B, C, D)


def VideoSource(filename: str, **kwargs) -> VSClip:
    """Provides generic video source function."""

    if filename.endswith(('.jpg', '.png')):
        if not exists(filename % 0):
            if 'firstnum' not in kwargs:
                kwargs['firstnum'] = 1

        iv = core.imwri.Read(filename, **kwargs)
        return core.std.SetFrameProp(iv, "_Primaries", intval=2)

    try:
        output = core.ffms2.Source(filename, **kwargs)
    except vs.Error as error:
        kwargs['seekmode'] = -1
        print("Resetting seekmode to -1", file=stderr)
        output = core.ffms2.Source(filename, **kwargs)

    # Sets _Primaries to default value as VS fails otherwise."""
    return core.std.SetFrameProp(output, "_Primaries", intval=2)


def DiskCache(expr: VSClip, filename: str) -> VSClip:
    """Either loads video from disk cache or computes as expr."""
    return VideoSource(filename) if exists(filename) else expr
