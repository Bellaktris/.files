from .frame_helpers import assign_planes
from .frame_helpers import get_planes

from ctypes.util import find_library

from functools import partial
from vapoursynth import core
import vapoursynth as vs
import numpy as np, cv2                                            # noqa: E401
from typing import List


sub_p = find_library('subtext')


VSClips = List[vs.VideoNode]
VSClip = vs.VideoNode


if not hasattr(core, 'sub') and sub_p:
    core.std.LoadPlugin(sub_p)


def AvsSubtitle(video, text: str, position: int = 2):
    # type: (vs.VideoNode, str, int) -> vs.VideoNode
    """Adds quick-and-easy subtitling wrapper."""

    # Use FullHD as a reference resolution
    scale1 = 100 * video.height // 1080
    scale2 = 100 * video.width // 1920

    scale = str(max(scale1, scale2))

    style = r"""{\fn(Asul),""" +\
            r"""\bord(2.4),""" +\
            r"""\b900,""" +\
            r"""\fsp(1.0),""" +\
            r"""\fs82,""" +\
            r"""\fscx""" + scale + r""",""" +\
            r"""\fscy""" + scale + r""",""" +\
            r"""\1c&H00FFFF,""" +\
            r"""\3c&H000000,""" +\
            r"""\an""" + str(position) + r"""}"""

    return core.sub.Subtitle(clip=video, text=style + text)


def FrameNumber(video: VSClip) -> VSClip:
    """Adds frame number at the top-left pos."""

    scale = str(100 * video.height // 1080)

    style = r"""{\fn(Asul),""" +\
            r"""\bord(2.4),""" +\
            r"""\b900,""" +\
            r"""\fsp(1.0),""" +\
            r"""\fs70,""" +\
            r"""\fscx""" + scale + r""",""" +\
            r"""\fscy""" + scale + r""",""" +\
            r"""\1c&H00FFFF,""" +\
            r"""\3c&H000000,""" +\
            r"""\an9}"""

    def evalf(n, clip):
        return core.sub.Subtitle(clip=clip, text=style + str(n))

    return core.std.FrameEval(video, partial(evalf, clip=video))


def ShowMotion(vecs_x, vecs_y, maxv=16):
    # type: (VSClip, VSClip, int) -> vs.VideoNode
    """Visualize motion using HSV notation."""

    assert vecs_x.format.id == vs.GRAYS
    assert vecs_y.format.id == vs.GRAYS

    output = core.std.BlankClip(vecs_x, format=vs.RGB24)

    def fn(n, f):
        output, xf, yf = f[0].copy(), f[1], f[2]
        x, y = get_planes(xf), get_planes(yf)

        H = np.arctan2(y, x) / (2 * np.pi) + 0.5
        V = np.sqrt(np.square(x) + np.square(y))

        V = np.minimum(V / maxv, 1.0)
        S = np.ones(H.shape, H.dtype)

        hsv = cv2.merge([360.0 * H, S, V])

        mv = 255 * cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        mvplanes = np.dsplit(mv.astype('uint8'), 3)
        return assign_planes(output, mvplanes)

    farg_clips = [output, vecs_x, vecs_y]
    return core.std.ModifyFrame(output, farg_clips, fn)


def AddHBorders(clip: VSClip, target_height: int) -> VSClip:
    """Adds top/bottom borders to match target height."""
    assert target_height >= clip.height
    assert target_height % 2 == 0

    diff = target_height - clip.height
    return core.std.AddBorders(clip, 0, 0, diff // 2, diff // 2)


def HStack(clips: VSClips) -> VSClip:
    """Stacks videos along horizontal dimension."""

    assert len(set(v.format.id for v in clips)) == 1

    stack_clips = [None] * (3 * len(clips) - 2)

    heights = [clip.height for clip in clips]

    if clips[0].format.color_family == vs.YUV:
        separators = [
            core.std.BlankClip(clip=clips[0], width=2, color=[0.0, 128, 128]),
            core.std.BlankClip(clip=clips[0], width=2, color=[255, 128, 128]),
        ]

    if clips[0].format.color_family == vs.RGB:
        separators = [
            core.std.BlankClip(clip=clips[0], width=2, color=[0.0, 0.0, 0.0]),
            core.std.BlankClip(clip=clips[0], width=2, color=[255, 255, 255]),
        ]

    if clips[0].format.color_family == vs.GRAY:
        separators = [
            core.std.BlankClip(clip=clips[0], width=2, color=0.0),
            core.std.BlankClip(clip=clips[0], width=2, color=255),
        ]

    for i in range(1, len(stack_clips), 3):
        stack_clips[i + 0], stack_clips[i + 1] = separators

    stack_clips[::3] = [AddHBorders(clip, max(heights)) for clip in clips]
    return core.std.StackHorizontal(stack_clips)
