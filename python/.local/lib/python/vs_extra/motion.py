from inspect import getfullargspec as argspec
from ctypes.util import find_library
from vapoursynth import core
import vapoursynth as vs


mvtools_p = find_library('mvtools')


if not hasattr(core, 'mv') and mvtools_p:
    core.std.LoadPlugin(mvtools_p)


def MotionMVTools(yuv_in, *args, dst=None, **kwargs):
    """Attach motion data to the clip."""

    kwargs.setdefault('badsad', 1500)
    kwargs.setdefault('thscd1', 400)
    kwargs.setdefault('blksizev', 8)
    kwargs.setdefault('blksize', 8)
    kwargs.setdefault('thscd2', 90)
    kwargs.setdefault('zerow', 1.0)
    kwargs.setdefault('pel', 2)

    output = dst or yuv_in

    def subdict(darg, knames):
        return {k: v for k, v in darg.items() if k in knames}

    def slice_args_and_call(fn, *args):
        return fn(*args, **subdict(kwargs, argspec(fn).args))

    super_clip = slice_args_and_call(core.mv.Super, yuv_in)
    vecs = slice_args_and_call(core.mv.Analyse, super_clip)

    thscd1, thscd2 = kwargs['thscd1'], kwargs['thscd2']
    kw = {'thscd1': thscd1, 'thscd2': thscd2}

    pads = {
        'bottom': 4 * kwargs['blksizev'],
        'right': 4 * kwargs['blksize'],
        'top': 4 * kwargs['blksizev'],
        'left': 4 * kwargs['blksize'],
    }

    AddBorders = core.std.AddBorders

    if 'global_motion' in kwargs:
        y_in = core.std.ShufflePlanes(yuv_in, 0, vs.GRAY)
        darkmask = core.std.Expr(y_in, "x 40 > 255 *")

        darkmask = core.std.Crop(darkmask, **pads)
        darkmask = AddBorders(darkmask, **pads)
        kwargs['mask'] = darkmask

    hvecs = core.mv.Mask(yuv_in, vecs, kind=3, ysc=128, **kw)
    vvecs = core.mv.Mask(yuv_in, vecs, kind=4, ysc=128, **kw)

    output = core.mv.SCDetection(output, vecs, **kw)

    AD = core.mv.Mask(yuv_in, vecs, kind=1, **kw)

    ShufflePlanes = core.std.ShufflePlanes

    dx = ShufflePlanes(hvecs, 0, vs.GRAY)
    dy = ShufflePlanes(vvecs, 0, vs.GRAY)

    if 'global_motion' in kwargs:
        output = slice_args_and_call(core.mv.DepanAnalyse, output, vecs)

    dx = core.std.Expr(dx, "x 128 - %d /" % kwargs['pel'], vs.GRAYS)
    dy = core.std.Expr(dy, "x 128 - %d /" % kwargs['pel'], vs.GRAYS)

    return output, [dx, dy, ShufflePlanes(AD, 0, vs.GRAY)]
