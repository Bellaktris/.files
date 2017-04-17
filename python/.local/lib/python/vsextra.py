#!/usr/bin/env python3
# -*- coding: <utf-8> -*-

"""Vapoursynth helper functions."""

import vapoursynth as vs
core = vs.get_core()


def AvsSubtitle(video, text, position=7):
    """Add simple subtitles."""
    scale = str(int(100*video.width/1920))
    style = r"""{\fnFontin,""" +\
            r"""\b,""" +\
            r"""\bord1,""" +\
            r"""\fs52,""" +\
            r"""\fscx""" + scale + r""",""" +\
            r"""\fscy""" + scale + r""",""" +\
            r"""\1c&H00FFFF,""" +\
            r"""\3c&H000000,""" +\
            r"""\an""" + str(position) + r"""}"""

    subs = core.assvapour.Subtitle(clip=video, text=style + text)

    kwargs = {'clip': subs[0], 'format': video.format.id}
    if kwargs['format'] == vs.YUV420P8:
        kwargs['matrix_s'] = '470bg'

    if subs[0].format.id != video.format.id:
        subs[0] = core.resize.Bicubic(**kwargs)

    return core.std.MaskedMerge(clipa=video, clipb=subs[0], mask=subs[1])


def AvsScale(video, width):
    """Scale to a new width."""
    kwargs = {'width': width, 'height': video.height*width//video.width}
    return core.resize.Bicubic(video, **kwargs)
