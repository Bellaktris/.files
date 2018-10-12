"""Vapoursynth helper functions."""

import os, ast, itertools
import vapoursynth as vs
import numpy as np, cv2
from functools \
    import partial

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

YUV_IDS = \
    [
        vs.YUV420P8,
        vs.YUV422P8,
        vs.YUV444P8,
        vs.YUV410P8,
        vs.YUV411P8,
        vs.YUV440P8,
        vs.YUV420P9,
        vs.YUV422P9,
        vs.YUV444P9,
        vs.YUV444PH,
        vs.YUV444PS,
        vs.YUV420P10,
        vs.YUV422P10,
        vs.YUV444P10,
        vs.YUV420P12,
        vs.YUV422P12,
        vs.YUV444P12,
        vs.YUV420P14,
        vs.YUV422P14,
        vs.YUV444P14,
        vs.YUV420P16,
        vs.YUV422P16,
        vs.YUV444P16,
    ]

cv2optflows = []

matrices = {
    'matrix_in_s': '709',
    'matrix_s': '709',
}


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


def input_array(frame):
    """Wraps frame into read-only numpy array."""
    possible_formats = [vs.RGBS, vs.RGB24, vs.GRAYS]
    assert frame.format.id in possible_formats

    if frame.format.id == vs.GRAYS:
        return np.asarray(frame.get_read_array(0))

    f2np = lambda i: np.asarray(frame.get_read_array(i))
    return cv2.merge([f2np(i) for i in (0, 1, 2)])


def Yuv2RGBS(video):
    """Converts input video to RGBS."""
    kw = {'matrix_in_s': '709', 'format': vs.RGBS}
    return core.resize.Bilinear(video, **kw)


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
    scale1 = str(int(100 * video.width  / 1920))
    scale2 = str(int(100 * video.height / 1080))

    scale = max(scale1, scale2)

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


def SmartStack(clips):
    """Stack videos along best dimension."""

    heights = [clip.height for clip in clips]
    widths = [clip.width for clip in clips]

    for i in range(len(clips)):
        kw = {'format': vs.YUV420P8, **matrices}
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

    assert not no_optflow and alg in cv2optflows \
        or alg in ['mvtools2', 'farneback'], alg

    if alg == 'mvtools2':
        return MotionMVTools(clip, *args, **kwargs)

    if alg == 'farneback':
        return FarnebackOF(clip, *args, **kwargs)


def MotionMVTools(clip, *args, **kwargs):
    """Attach motion data to the clip."""

    if 'pel' not in kwargs:
        kwargs['pel'] = 2

    pel = kwargs['pel']

    if 'thscd1' in kwargs:
        thscd1 = kwargs['thscd1']
        del kwargs['thscd1']

    if 'thscd2' in kwargs:
        thscd2 = kwargs['thscd2']
        del kwargs['thscd2']

    thscd1, thscd2 = 400, 90

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


def FarnebackOF(clip, *args, **kwargs):
    """Attach motion data to the clip."""
    assert False, "Not implemented yet"


def AvsScale(video, width):
    """Scale to a new width."""
    height = video.height * width // video.width
    kwargs = {'width': width, 'height': height}
    return core.resize.Bicubic(video, **kwargs)


def Expr(clips, expr, **kwargs):
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
        x = np.asarray(f[1].get_read_array(0))
        y = np.asarray(f[2].get_read_array(0))

        H = np.arctan2(y, x) / (2 * np.pi) + 0.5
        V = np.sqrt(np.square(x) + np.square(y))

        V = np.minimum(V / maxv, 1.0)
        S = np.ones(H.shape, H.dtype)

        output_frame = f[0].copy()
        hsv = cv2.merge([360.0 * H, S, V])

        rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        rgb = cv2.split((255 * rgb).astype(np.uint8))

        for i in range(output_frame.format.num_planes):
            output_plane = np.asarray(output_frame.get_write_array(i))
            output_plane += rgb[i]

        return output_frame

    output = core.std.ModifyFrame(output, [output, hvecs, vvecs], fn)

    return core.resize.Bilinear(output,
                                format=vs.YUV420P8, matrix_s="709")
