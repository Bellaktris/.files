from inspect import getfullargspec as argspec
from colorsys import hsv_to_rgb

from ctypes.util import find_library
from vapoursynth import core
import vapoursynth as vs
import os.path, math                                               # noqa: E401


DIR = os.path.dirname(__file__) + '/'


mvtools2_p = find_library('mvtools')
imwri_p = find_library('imwri')


if not hasattr(core, 'mv') and mvtools2_p:
    core.std.LoadPlugin(mvtools2_p)

if not hasattr(core, 'imwri') and imwri_p:
    core.std.LoadPlugin(imwri_p)


def AddMotionLegend(flow_vis):
    main, mask = core.imwri.Read(DIR + "motion-legend.png", alpha=True)
    conv_args = {'format': flow_vis.format.id, 'matrix_s': '709'}
    y, x, z = main.height, main.width, flow_vis.height
    W, H = x * z // (8 * y) * 2, z // 8 * 2

    main = core.std.Loop(core.resize.Bilinear(main, W, H, **conv_args))
    left_incr, top_incr = flow_vis.width - W, flow_vis.height - H
    mask = core.std.Loop(core.resize.Bilinear(mask, W, H))
    M = min((left_incr // 20) * 2, (top_incr // 20) * 2)

    main = core.std.AddBorders(main, left_incr - M, M, top_incr - M, M)
    main = core.std.AssumeFPS(main, flow_vis)

    mask = core.std.AddBorders(mask, left_incr - M, M, top_incr - M, M)
    mask = core.std.AssumeFPS(mask, flow_vis)

    return core.std.MaskedMerge(flow_vis, main, mask)


def MotionMVTools(yuv_in, *args, dst=None, **kwargs):
    """Attach motion data to the clip."""

    kwargs.setdefault('badsad', 1500)
    kwargs.setdefault('zerow', 10.0)

    kwargs.setdefault('thscd1', 400)
    kwargs.setdefault('thscd2', 150)

    kwargs.setdefault('blksizev', 8)
    kwargs.setdefault('blksize', 8)
    kwargs.setdefault('pel', 2)

    output = dst or yuv_in

    def subdict(darg, knames):
        return {k: v for k, v in darg.items() if k in knames}

    def slice_args_and_call(fn, *args):
        return fn(*args, **subdict(kwargs, argspec(fn).args))

    def Rgb2Yuv(clip):
        kwargs = {
            'matrix_in_s': "rgb", 'matrix_s': "709",
            'format': vs.YUV420P8,
        }

        return core.resize.Bilinear(clip, **kwargs)

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
        if 'mask' not in kwargs:
            y_in = core.std.ShufflePlanes(yuv_in, 0, vs.GRAY)
            darkmask = core.std.Expr(y_in, "x 40 > 255 *")

            darkmask = core.std.Crop(darkmask, **pads)
            darkmask = AddBorders(darkmask, **pads)
            kwargs['mask'] = darkmask

    hvecs = core.mv.Mask(yuv_in, vecs, kind=3, ysc=128, **kw)
    vvecs = core.mv.Mask(yuv_in, vecs, kind=4, ysc=128, **kw)

    if 'scd_delta' in kwargs:
        # TODO(ygitman): This is ugly, change
        kwargs['delta'] = kwargs['scd_delta']

    V = slice_args_and_call(core.mv.Analyse, super_clip) \
        if 'scd_delta' in kwargs else vecs

    # TODO(ygitman): do better job here
    output = core.mv.SCDetection(output, V, **kw)

    AD = core.mv.Mask(yuv_in, vecs, kind=1, **kw)

    ShufflePlanes = core.std.ShufflePlanes

    dx = ShufflePlanes(hvecs, 0, vs.GRAY)
    dy = ShufflePlanes(vvecs, 0, vs.GRAY)

    def xy2rgb(x, y):
        y = (y - 128.0) / kwargs['pel']
        x = (x - 128.0) / kwargs['pel']

        H = math.atan2(y, x) / (2.0 * math.pi) + 0.5
        V = min(math.sqrt(x * x + y * y) / 16, 1)
        return hsv_to_rgb(H, 1, V)

    def xy2r(x, y):
        return int(255 * xy2rgb(x, y)[0])

    def xy2g(x, y):
        return int(255 * xy2rgb(x, y)[1])

    def xy2b(x, y):
        return int(255 * xy2rgb(x, y)[2])

    R = core.std.Lut2(dx, dy, function=xy2r)
    G = core.std.Lut2(dx, dy, function=xy2g)
    B = core.std.Lut2(dx, dy, function=xy2b)

    if 'global_motion' in kwargs:
        output = slice_args_and_call(core.mv.DepanAnalyse, output, vecs)

    dx = core.std.Expr(dx, "x 128 - %d /" % kwargs['pel'], vs.GRAYS)
    dy = core.std.Expr(dy, "x 128 - %d /" % kwargs['pel'], vs.GRAYS)

    vis = core.std.ShufflePlanes([R, G, B], [0, 0, 0], vs.RGB)

    return output, [dx, dy, Rgb2Yuv(vis), ShufflePlanes(AD, 0, vs.GRAY)]
