"""Vapoursynth helper functions."""

import os, sys, ast, itertools
import vapoursynth as vs
import numpy as np, cv2

from ctypes.util import find_library
from functools import partial

try:
    no_optflow = False
    import cv2.optflow
except ImportError:
    no_optflow = True

try:
    no_ximgproc = False
    import cv2.ximgproc
except ImportError:
    no_ximgproc = True

try:
    no_videostab = False
    import cv2.videostab
except ImportError:
    no_videostab = True

core = vs.get_core()

mvtools2_p, sub_p = \
    find_library('mvtools'), \
    find_library('subtext')

imwri_p, ffms2_p = \
    find_library('imwri'),   \
    find_library('ffms2')


def check_plugin(name, ns):
    return not hasattr(core, ns) \
        and name is not None


if check_plugin(mvtools2_p, 'mv'):
    core.std.LoadPlugin(mvtools2_p)

if check_plugin(ffms2_p, 'ffms2'):
    core.std.LoadPlugin(ffms2_p)

if check_plugin(imwri_p, 'imwri'):
    core.std.LoadPlugin(imwri_p)

if check_plugin(sub_p, 'sub'):
    core.std.LoadPlugin(sub_p)


class v(ast.NodeVisitor):
    """Simple expression parser."""

    def __init__(self):
        self.tokens = []

    def visit(self, expr):
        super(v, self).visit(expr)
        return self.tokens

    def visit_BoolOp(self, node):
        for val in node.values:
            self.visit(val)
        self.visit(node.op)

    def visit_IfExp(self, node):
        self.visit(node.test)
        self.visit(node.body)
        self.visit(node.orelse)
        self.tokens.append('?')

    def visit_Call(self, node):
        for arg in node.args:
            self.visit(arg)
        self.visit(node.func)

    def visit_UnaryOp(self, node):
        self.visit(node.operand)
        self.visit(node.op)

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)
        self.visit(node.op)

    def visit_Compare(self, node):
        self.visit(node.left)
        self.visit(node.comparators[0])
        self.visit(node.ops[0])

        args, ops =           \
            node.comparators, \
            node.ops[1:]

        args = zip(args[:-1], args[1:])

        for O, (A, B) in zip(ops, args):
            self.visit(A)
            self.visit(B)
            self.visit(O)
            self.tokens.append('and')

    def visit_Add(self, node):
        self.tokens.append('+')
        super(v, self).generic_visit(node)

    def visit_UAdd(self, node):
        self.tokens.append('+')
        super(v, self).generic_visit(node)

    def visit_Sub(self, node):
        self.tokens.append('-')
        super(v, self).generic_visit(node)

    def visit_USub(self, node):
        self.tokens.append('-')
        super(v, self).generic_visit(node)

    def visit_Div(self, node):
        self.tokens.append('/')
        super(v, self).generic_visit(node)

    def visit_Mult(self, node):
        self.tokens.append('*')
        super(v, self).generic_visit(node)

    def visit_Eq(self, node):
        self.tokens.append("=")
        super(v, self).generic_visit(node)

    def visit_Lt(self, node):
        self.tokens.append("<")
        super(v, self).generic_visit(node)

    def visit_Gt(self, node):
        self.tokens.append(">")
        super(v, self).generic_visit(node)

    def visit_LtE(self, node):
        self.tokens.append("<=")
        super(v, self).generic_visit(node)

    def visit_GtE(self, node):
        self.tokens.append(">=")
        super(v, self).generic_visit(node)

    def visit_Or(self, node):
        self.tokens.append('or')
        super(v, self).generic_visit(node)

    def visit_And(self, node):
        self.tokens.append('and')
        super(v, self).generic_visit(node)

    def visit_BitXor(self, node):
        self.tokens.append('xor')
        super(v, self).generic_visit(node)

    def visit_Not(self, node):
        self.tokens.append('not')
        super(v, self).generic_visit(node)

    def visit_Name(self, node):
        self.tokens.append(node.id)
        super(v, self).generic_visit(node)

    def visit_Num(self, node):
        self.tokens.append(str(node.n))
        super(v, self).generic_visit(node)

    def visit_Expr(self, node):
        super(v, self).generic_visit(node)


def input_array(vsnode, frame_num=None):
    """Wraps video frame into read-only numpy array."""

    frame = vsnode.get_frame(frame_num) \
        if hasattr(vsnode, 'get_frame') else vsnode

    possible_formats = [vs.RGB, vs.GRAY]
    assert frame.format.color_family in possible_formats

    if frame.format.color_family == vs.GRAY:
        return np.asarray(frame.get_read_array(0))

    f2np = lambda i: np.asarray(frame.get_read_array(i))
    return cv2.merge([f2np(i) for i in (0, 1, 2)])


def assign_frame(lhs, rhs_planes, **props):
    """Assigns data to VapourSynth video frame."""

    split = lambda x: [x] if len(x.shape) == 2 \
        else np.squeeze(np.dsplit(x, x.shape[2]))

    if type(rhs_planes) is np.ndarray:
        rhs_planes = [rhs_planes]

    lhs.props.update(props)

    rhs_planes = [x for l in rhs_planes for x in split(l)]

    for i, f in enumerate(rhs_planes):
        np.asarray(lhs.get_write_array(i)).__iadd__(f)

    return lhs  # Not conventional in Py, but useful


def scenes(video_clip, *compl_clips, ml=11):
    """Groups frames by _SceneChangePrev prop."""

    clips = [video_clip, *compl_clips]
    frames = zip(*[v.frames() for v in clips])

    def has_scp(fs):
        return fs[0].props['_SceneChangePrev']

    def sfn(sum, element):
        return sum[0] + element[0], element[1]

    frames = ((has_scp(f), f) for f in frames)

    def contract_dissolves(frames):
        pv, pf = next(frames)

        for v, f in frames:
            if v == 1:
                pv == 0

            yield (pv, pf)
            pv, pf = v, f

        yield (pv, pf)

    def clean(frames):
        j = -ml
        for i, (v, f) in enumerate(frames):
            if v == 0 or i - j <= ml:
                yield (0, f)
            else:
                yield (1, f)
                j = i

    frames = clean(contract_dissolves(frames))
    frames = itertools.accumulate(frames, sfn)

    scenes = itertools.groupby(frames, lambda x: x[0])
    return (map(lambda f: f[1], s) for _, s in scenes)


def VideoSource(filename, **kwargs):
    """Wraps ffms2 source fn with some metadata."""
    if filename.endswith(('.jpg', '.png')):
        if not os.path.exists(filename % 0):
            if 'firstnum' not in kwargs:
                kwargs['firstnum'] = 1

        return core.imwri.Read(filename, **kwargs)

    return core.ffms2.Source(filename, **kwargs)


def Yuv2GRAY8(video):
    """Converts input video to GRAY8."""
    kw = {'matrix_in_s': '709', 'format': vs.GRAY8}
    return core.resize.Bilinear(video, **kw)


def Yuv2GRAYS(video):
    """Converts input video to GRAY8."""
    kw = {'matrix_in_s': '709', 'format': vs.GRAYS}
    return core.resize.Bilinear(video, **kw)


def Yuv2RGB24(video):
    """Converts input video to RGB24."""
    kw = {'matrix_in_s': '709', 'format': vs.RGB24}
    return core.resize.Bilinear(video, **kw)


def Yuv2RGBS(video):
    """Converts input video to RGBS."""
    kw = {'matrix_in_s': '709', 'format': vs.RGBS}
    return core.resize.Bilinear(video, **kw)


def Yuv2BGR24(video):
    """Converts input video to BGR24."""
    video, idxs, fmt = Yuv2RGB24(video), [2, 1, 0], vs.RGB
    return core.std.ShufflePlanes(video, idxs, fmt)


def Yuv2BGRS(video):
    """Converts input video to BGRS."""
    video, idxs, fmt = Yuv2RGBS(video), [2, 1, 0], vs.RGB
    return core.std.ShufflePlanes(video, idxs, fmt)


def MakeGRAY8(video):
    """Converts input video [YUV or RGB] to vs.GRAY8."""
    if not video.format.color_family == vs.YUV:
        return core.resize.Bilinear(video, format=vs.GRAY8)
    else:
        fnkwargs = dict(matrix_in_s='709', format=vs.GRAY8)
        return core.resize.Bilinear(video, **fnkwargs)


def AvsSubtitle(video, text, position=2):
    """Add simple subtitles."""
    scale1 = str(int(100 * video.width  / 1920))
    scale2 = str(int(100 * video.height / 1080))

    scale = max(scale1, scale2)

    style = r"""{\fn(Fontin),""" +\
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


def AddFCounter(video):
    scale = str(100 * video.height // 1080)

    style = r"""{\fn(Fontin),""" +\
            r"""\bord(2.4),""" +\
            r"""\b900,""" +\
            r"""\fsp(1.0),""" +\
            r"""\fs70,""" +\
            r"""\fscx""" + scale + r""",""" +\
            r"""\fscy""" + scale + r""",""" +\
            r"""\1c&H00FFFF,""" +\
            r"""\3c&H000000,""" +\
            r"""\an""" + str(9) + r"""}"""

    def evalf(n, clip):
        return core.sub.Subtitle(clip=clip, text=style + str(n))

    return core.std.FrameEval(video, partial(evalf, clip=video))


def CenterCrop(clip, margin):
    """Applies center cropping with the given margin value."""
    return core.std.Crop(clip, margin, margin, margin, margin)


def AddHBorders(clip, target_height):
    """Add top/bottom borders to match target height."""
    assert target_height >= clip.height

    diff = target_height - clip.height
    return core.std.AddBorders(clip, 0, 0, diff // 2, diff - diff / 2)


def AddWBorders(clip, target_width):
    """Add left/right borders to match target width."""
    assert target_width >= clip.width

    diff = target_width - clip.width
    return core.std.AddBorders(clip, diff // 2, diff - diff / 2, 0, 0)


def HScale(clip, H):
    """Scale input video to the given height."""
    width= (clip.width * H / clip.height) // 2 * 2
    return core.resize.Bilinear(clip, height=H, width=width)


def SmartStack(clips):
    """Stack videos along best dimension."""

    heights = [clip.height for clip in clips]
    widths = [clip.width for clip in clips]

    for i in range(len(clips)):
        if clips[i].format.color_family == vs.YUV:
            kw = {'format': vs.YUV420P8, 'matrix_in_s': '709'}

        if clips[i].format.color_family != vs.YUV:
            kw = {'format': vs.YUV420P8, 'matrix_s': '709'}

        clips[i] = core.resize.Bilinear(clips[i], **kw)

    stack_clips = [None] * (3 * len(clips) - 2)

    diff_heights = max(heights) - min(heights)
    diff_widths = max(widths) - min(widths)

    if diff_heights < diff_widths + 10:
        separators = [
            core.std.BlankClip(clip=clips[0], width=2,  color=[0,   128, 128]),
            core.std.BlankClip(clip=clips[0], width=2,  color=[255, 128, 128]),
        ]

        for i in range(1, len(stack_clips), 3):
            stack_clips[i + 0], stack_clips[i + 1] = separators

        stack_clips[::3] = [AddHBorders(clip, max(heights)) for clip in clips]
        return core.std.StackHorizontal(stack_clips)
    else:
        separators = [
            core.std.BlankClip(clip=clips[0], height=2, color=[0,   128, 128]),
            core.std.BlankClip(clip=clips[0], height=2, color=[255, 128, 128]),
        ]

        for i in range(1, len(stack_clips), 3):
            stack_clips[i + 0], stack_clips[i + 1] = separators

        stack_clips[::3] = [AddWBorders(clip, max(widths)) for clip in clips]
        return core.std.StackVertical(stack_clips)


def ComputeMotion(clip, alg, *args, **kwargs):
    """Attach motion data to the clip."""

    assert alg in ['mvtools2', 'farneback'], alg

    if alg == 'mvtools2':
        return MotionMVTools(clip, *args, **kwargs)

    if alg == 'farneback':
        return FarnebackOF(clip, *args, **kwargs)


def FarnebackOF(clip, *args, **kwargs):
    """Attach motion data to the clip."""

    output = core.std.BlankClip(clip, format=vs.RGBS)
    assert clip.format.color_family == vs.GRAY, clip

    def fn(n, f):
        frame_x = input_array(clip, max(n + 0, 0))
        scn_chng_prop_name = '_SceneChangePrev'

        isb = 'isb' in kwargs and kwargs['isb']

        if not isb:
            frame_y = input_array(clip, max(n - 1, 0))

        if isb:
            scn_chng_prop_name = '_SceneChangeNext'
            N = min(n + 1, clip.num_frames - 1)
            frame_y = input_array(clip, N)

        fnargs = {
            'prev': frame_x,
            'next': frame_y,
            'flow': None,
            'flags': 0,
            'poly_sigma': kwargs.get('poly_sigma', 2.4),
            'pyr_scale': kwargs.get('pyr_scale', 0.5),
            'iterations': kwargs.get('iterations', 1),
            'winsize': kwargs.get('winsize', 15),
            'levels': kwargs.get('levels', 3),
            'poly_n': kwargs.get('poly_n', 11),
        }

        flow = cv2.calcOpticalFlowFarneback(**fnargs)

        xv = np.linspace(0, flow.shape[1], flow.shape[1],
                         False, dtype=np.float32)

        yv = np.linspace(0, flow.shape[0], flow.shape[0],
                         False, dtype=np.float32)

        frame_x = frame_x.astype(np.float32) / 255.0
        frame_y = frame_y.astype(np.float32) / 255.0

        xv = np.tile(np.expand_dims(xv, 0), [flow.shape[0], 1])
        yv = np.tile(np.expand_dims(yv, 1), [1, flow.shape[1]])

        mt, mode = flow + np.dstack([xv, yv]), cv2.INTER_LINEAR
        diff_map = frame_x - cv2.remap(frame_y, mt, None, mode)

        sads, props = np.abs(diff_map), {scn_chng_prop_name: 0}
        change_map = (sads > 800 / 64 / 255).astype(np.float32)

        if np.mean(change_map) > 90 / 255:
            sads = np.zeros(sads.shape)
            flow = np.zeros(flow.shape)
            props[scn_chng_prop_name] = 1

        return assign_frame(f.copy(), [flow, sads], **props)

    output = core.std.ModifyFrame(output, output, fn)

    take_plane = lambda chnl: \
        core.std.ShufflePlanes(output, chnl, vs.GRAY)

    return clip,  (take_plane(0), take_plane(1), take_plane(2))


def MotionMVTools(clip, *args, **kwargs):
    """Attach motion data to the clip."""

    if 'pel' not in kwargs:
        kwargs['pel'] = 2

    pel = kwargs['pel']

    thscd1, thscd2 = 400, 90

    if 'thscd1' in kwargs:
        thscd1 = kwargs['thscd1']
        del kwargs['thscd1']

    if 'thscd2' in kwargs:
        thscd2 = kwargs['thscd2']
        del kwargs['thscd2']

    if 'badsad' not in kwargs:
        kwargs['badsad'] = 1500

    super_opts = ['hpad', 'vpad', 'pel', 'levels',
                  'chroma', 'sharp', 'rfilter']

    kwargs1 = {k: v for k, v in kwargs.items()
               if k in super_opts}

    kwargs2 = {k: v for k, v in kwargs.items()
               if k not in super_opts}

    kw = {'thscd1': thscd1, 'thscd2': thscd2}

    super_clip = core.mv.Super(clip, **kwargs1)
    vecs = core.mv.Analyse(super_clip, **kwargs2)

    clip = core.mv.SCDetection(clip, vecs, **kw)

    hvecs = core.mv.Mask(clip, vecs, kind=3, ysc=128, **kw)
    vvecs = core.mv.Mask(clip, vecs, kind=4, ysc=128, **kw)

    ShufflePlanes = core.std.ShufflePlanes

    dx = ShufflePlanes(hvecs, 0, vs.GRAY)
    dy = ShufflePlanes(vvecs, 0, vs.GRAY)

    sads = core.mv.Mask(clip, vecs, kind=1, **kw)

    dx = core.std.Expr(dx, "x 128 - %d /" % pel, vs.GRAYS)
    dy = core.std.Expr(dy, "x 128 - %d /" % pel, vs.GRAYS)

    return clip, [dx, dy, ShufflePlanes(sads, 0, vs.GRAY)]


def AvsScale(video, width):
    """Scale to a new width."""
    height = video.height * width // video.width
    kwargs = {'width': width, 'height': height}
    return core.resize.Bicubic(video, **kwargs)


def Expr(expr, clips, **kwargs):
    """Wrapper for VapourSynth Expr function."""
    expr = ' '.join(v().visit(ast.parse(expr)))
    return core.std.Expr(clips, expr, **kwargs)


def Variance(clip, rad=7):
    """Compute spatial patch-local variance."""

    sqr_clip = core.std.Expr([clip], "x x *")

    def box_filter(source):
        return core.std.BoxBlur(source, hradius=rad, vradius=rad)

    assert clip.format.id in [vs.GRAYS, vs.RGBS], clip.format
    avg, sqr_avg = box_filter(clip), box_filter(sqr_clip)

    result = core.std.Expr([sqr_avg, avg], "x y y * -")
    kwargs = {'format': vs.GRAYS, 'matrix_s': '709'}
    return core.resize.Bilinear(result, **kwargs)


def ShowMotion(hvecs, vvecs, maxv=16):
    """Visualize motion using HSV notation."""

    assert hvecs.format.id == vs.GRAYS
    assert vvecs.format.id == vs.GRAYS
    output = core.std.BlankClip(hvecs, format=vs.RGB24)

    def fn(n, f):
        x, y = input_array(f[1]), input_array(f[2])

        H = np.arctan2(y, x) / (2 * np.pi) + 0.5
        V = np.sqrt(np.square(x) + np.square(y))

        V = np.minimum(V / maxv, 1.0)
        S = np.ones(H.shape, H.dtype)

        hsv = cv2.merge([360.0 * H, S, V])

        rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        return assign_frame(f[0].copy(), (255 * rgb).astype('uint8'))

    output = core.std.ModifyFrame(output, [output, hvecs, vvecs], fn)

    return core.resize.Bilinear(output,
                                format=vs.YUV420P8, matrix_s="709")
