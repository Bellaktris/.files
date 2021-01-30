from .source_funcs import ScalePadFitSize
from .helpers import Any2Yuv

from ctypes.util import find_library
from functools import partial
from vapoursynth import core
import vapoursynth as vs
from typing import List
from math import sqrt
from math import ceil


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

    style1 = r"""{\fn(Asul),""" +\
             r"""\bord(2.4),""" +\
             r"""\b900,""" +\
             r"""\fsp(1.0),""" +\
             r"""\fs70,""" +\
             r"""\fscx""" + scale + r""",""" +\
             r"""\fscy""" + scale + r""",""" +\
             r"""\1c&H00FFFF,""" +\
             r"""\3c&H000000,""" +\
             r"""\an9}"""

    style2 = r"""{\fn(Asul),""" +\
             r"""\bord(2.4),""" +\
             r"""\b900,""" +\
             r"""\fsp(1.0),""" +\
             r"""\fs70,""" +\
             r"""\fscx""" + scale + r""",""" +\
             r"""\fscy""" + scale + r""",""" +\
             r"""\1c&H0000FF,""" +\
             r"""\3c&H000000,""" +\
             r"""\an9}"""

    def evalf(n, clip):
        if clip.get_frame(n).props.get('_SceneChangePrev', 0):
            return core.sub.Subtitle(clip=clip, text=style2 + str(n))
        else:
            return core.sub.Subtitle(clip=clip, text=style1 + str(n))

    return core.std.FrameEval(video, partial(evalf, clip=video))


def AddHBorders(clip: VSClip, target_height: int) -> VSClip:
    """Adds top/bottom borders to match target height."""
    assert target_height >= clip.height
    assert target_height % 2 == 0

    diff1 = (target_height - clip.height) // 4 * 2
    diff2 = (target_height - clip.height) - diff1
    return core.std.AddBorders(clip, 0, 0, diff1, diff2)


def AddWBorders(clip: VSClip, target_width: int) -> VSClip:
    """Adds top/bottom borders to match target height."""
    assert target_width >= clip.width
    assert target_width % 2 == 0

    diff1 = (target_width - clip.width) // 4 * 2
    diff2 = (target_width - clip.width) - diff1
    return core.std.AddBorders(clip, diff1, diff2, 0, 0)


def Normalize(clip: VSClip) -> VSClip:
    """Convert video to standard settings."""

    clip = core.std.AssumeFPS(clip, fpsnum=24, fpsden=1)
    clip = ScalePadFitSize(clip, (720, 480))
    return Any2Yuv(clip)


def JoinSegments(clips, sep=None):
    """Joins array of clips together."""

    clips = iter(clips)
    fclip = next(clips)

    if sep is not None:
        clips = (sep + v for v in clips)
    return sum(clips, fclip)


def HStack(clips: VSClips) -> VSClip:
    """Stacks videos along horizontal dimension."""

    assert len(set(v.format.id for v in clips)) == 1
    assert len(set(v.fps for v in clips)) == 1

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


def VStack(clips: VSClips) -> VSClip:
    """Stacks videos along horizontal dimension."""

    assert len(set(v.format.id for v in clips)) == 1
    assert len(set(v.fps for v in clips)) == 1

    stack_clips = [None] * (3 * len(clips) - 2)

    widths = [clip.width for clip in clips]

    if clips[0].format.color_family == vs.YUV:
        separators = [
            core.std.BlankClip(clip=clips[0], height=2, color=[0.0, 128, 128]),
            core.std.BlankClip(clip=clips[0], height=2, color=[255, 128, 128]),
        ]

    if clips[0].format.color_family == vs.RGB:
        separators = [
            core.std.BlankClip(clip=clips[0], height=2, color=[0.0, 0.0, 0.0]),
            core.std.BlankClip(clip=clips[0], height=2, color=[255, 255, 255]),
        ]

    if clips[0].format.color_family == vs.GRAY:
        separators = [
            core.std.BlankClip(clip=clips[0], height=2, color=0.0),
            core.std.BlankClip(clip=clips[0], height=2, color=255),
        ]

    for i in range(1, len(stack_clips), 3):
        stack_clips[i + 0], stack_clips[i + 1] = separators

    stack_clips[::3] = [AddWBorders(clip, max(widths)) for clip in clips]
    return core.std.StackVertical(stack_clips)


def Mesh(clips: VSClips) -> VSClip:
    """Pack videos into squre mesh."""

    blank_clip = core.std.BlankClip(clips[0], keep=True)

    assert len(set(v.format.id for v in clips)) == 1
    assert len(set(v.height for v in clips)) == 1
    assert len(set(v.width for v in clips)) == 1
    assert len(set(v.fps for v in clips)) == 1

    mesh_side = ceil(sqrt(len(clips)))

    def getHStack(idx):
        if (idx + 1) * mesh_side > len(clips):
            return HStack(clips[idx * mesh_side:] + [blank_clip] * ((idx + 1) * mesh_side - len(clips)))  # noqa: E501
        else:
            return HStack(clips[idx * mesh_side:(idx + 1) * mesh_side])

    return VStack([getHStack(k) for k in range(ceil(len(clips) / mesh_side))])
