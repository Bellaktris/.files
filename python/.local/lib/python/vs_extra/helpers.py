import vapoursynth as vs


VSClip = vs.VideoNode


def HScale(clip: VSClip, H: int) -> VSClip:
    """Scales input video to the given height."""
    other = (clip.width * H // clip.height) // 2 * 2
    return vs.core.resize.Bilinear(clip, other, H)


def WScale(clip: VSClip, W: int) -> VSClip:
    """Scales input video to the given width."""
    other = (clip.height * W // clip.width) // 2 * 2
    return vs.core.resize.Bilinear(clip, W, other)


def CenterCrop(clip_in: VSClip, margin: int) -> VSClip:
    """Applies center cropping with the given margin value."""
    return vs.core.std.Crop(clip_in, margin, margin, margin, margin)


def Any2Yuv(clip: VSClip) -> VSClip:
    kwargs = {'format': vs.YUV420P8, 'matrix_s': '709'}
    return vs.core.resize.Bilinear(clip, **kwargs)


def Variance(clip: VSClip, rad: int = 7) -> VSClip:
    """Compute spatial patch-local variance."""

    sqr_clip = vs.core.std.Expr([clip], "x x *")

    def box_filter(source):
        return vs.core.std.BoxBlur(source, hradius=rad, vradius=rad)

    assert clip.format.id in [vs.GRAYS, vs.RGBS], clip.format
    avg, sqr_avg = box_filter(clip), box_filter(sqr_clip)

    result = vs.core.std.Expr([sqr_avg, avg], "x y y * -")
    kwargs = {'format': vs.GRAYS, 'matrix_s': '709'}
    return vs.core.resize.Bilinear(result, **kwargs)
