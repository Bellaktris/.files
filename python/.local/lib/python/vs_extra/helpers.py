import vapoursynth as vs


VSClip = vs.VideoNode


def CenterCrop(clip_in: VSClip, margin: int) -> vs.VideoNode:
    """Applies center cropping with the given margin value."""
    return vs.core.std.Crop(clip_in, margin, margin, margin, margin)


def Subsample(clip: VSClip, step: int):
    """Decrease effective temporal resolution of vsnode."""
    return vs.core.std.Interleave([clip[::step]] * step) \
        if step > 1 else clip


def ResizeTo(clip: VSClip, *args, **kwargs) -> VSClip:
    """Provides wrapper for bilinear resizing."""
    return vs.core.resize.Bilinear(clip, *args, **kwargs)


def Any2Yuv(clip: VSClip) -> VSClip:
    kwargs1 = {'format': vs.YUV420P8, 'matrix_s': '709'}
    kwargs2 = {'prop': '_ColorRange', 'intval': 1}
    if clip.format.id == vs.YUV420P8: return clip

    if clip.format.color_family == vs.YUV:
        del kwargs1['matrix_s']

    clip = vs.core.resize.Bilinear(clip,  **kwargs1)
    return vs.core.std.SetFrameProp(clip, **kwargs2)


def HScale(clip: VSClip, H: int) -> VSClip:
    """Scales input video to the given height."""
    other = (clip.width * H // clip.height) // 2 * 2
    return vs.core.resize.Bilinear(clip, other, H)


def WScale(clip: VSClip, W: int) -> VSClip:
    """Scales input video to the given width."""
    other = (clip.height * W // clip.width) // 2 * 2
    return vs.core.resize.Bilinear(clip, W, other)
