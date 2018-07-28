"""Vapoursynth helper functions."""

import ast, numpy as np, cv2
import vapoursynth as vs

core = vs.get_core()

matrices = {
    'matrix_in_s': '470bg',
    'matrix_s': '470bg',
}


class v(ast.NodeVisitor):
    """Simple expression parser."""

    def __init__(self):
        self.tokens = []

    def visit_BoolOp(self, node):
        for val in node.values:
            self.visit(val)
        self.visit(node.op)

    def visit_And(self, node):
        self.tokens.append('and')
        super(v, self).generic_visit(node)

    def visit_Or(self, node):
        self.tokens.append('or')
        super(v, self).generic_visit(node)

    def visit_Call(self, node):
        for arg in node.args:
            self.visit(arg)
        self.visit(node.func)

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)
        self.visit(node.op)

    def visit_Add(self, node):
        self.tokens.append('+')
        super(v, self).generic_visit(node)

    def visit_Div(self, node):
        self.tokens.append('/')
        super(v, self).generic_visit(node)

    def visit_Mult(self, node):
        self.tokens.append('*')
        super(v, self).generic_visit(node)

    def visit_CmpOp(self, node):
        self.visit(node.left)
        self.visit(node.right)
        self.visit(node.op)

    def visit_Eq(self, node):
        self.tokens.append('=')
        super(v, self).generic_visit(node)

    def visit_Lt(self, node):
        self.tokens.append('<')
        super(v, self).generic_visit(node)

    def visit_Gt(self, node):
        self.tokens.append('>')
        super(v, self).generic_visit(node)

    def visit_LtE(self, node):
        self.tokens.append('<=')
        super(v, self).generic_visit(node)

    def visit_GtE(self, node):
        self.tokens.append('>=')

    def visit_Expr(self, node):
        super(v, self).generic_visit(node)

    def visit_Name(self, node):
        self.tokens.append(node.id)
        super(v, self).generic_visit(node)

    def visit_Num(self, node):
        self.tokens.append(str(node.n))
        super(v, self).generic_visit(node)


def Yuv2RGB(video):
    """Converts input video to RGB24."""
    kw = {'matrix_in_s': '470bg', 'format': vs.RGB24}
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

    stack_clips = [None] * (3 * len(clips) - 2)

    diff_heights = max(heights) - min(heights)
    diff_widths = max(widths) - min(widths)

    for i in range(len(clips)):
        kw = {'format': vs.YUV420P8, 'matrix_in_s': '470bg'}
        clips[i] = core.resize.Bilinear(clips[i], **kw)

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


def ComputeMotion(clip, *args, **kwargs):
    """Attach motion data to the clip."""

    if 'pel' not in kwargs:
        kwargs['pel'] = 2

    pel = kwargs['pel']

    thscd1, thscd2 = 400, 130

    if 'thscd1' in kwargs:
        thscd1 = kwargs['thscd1']
        del kwargs['thscd1']

    if 'thscd2' in kwargs:
        thscd2 = kwargs['thscd2']
        del kwargs['thscd2']

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
    sads = core.mv.Mask(clip, vecs, kind=1, **kw)

    hvecs = core.std.ShufflePlanes(
        clips=hvecs, planes=0, colorfamily=vs.GRAY)

    vvecs = core.std.ShufflePlanes(
        clips=vvecs, planes=0, colorfamily=vs.GRAY)

    sads = core.std.ShufflePlanes(
        clips=sads, planes=0, colorfamily=vs.GRAY)

    hvecs = core.std.Expr(hvecs, "x 128 - %d /" % pel, vs.GRAYS)
    vvecs = core.std.Expr(vvecs, "x 128 - %d /" % pel, vs.GRAYS)

    return clip, (hvecs, vvecs, sads)


def ShowMotion(hvecs, vvecs, maxv=16):
    """Visualize motion using HSV notation."""
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
                                format=vs.YUV420P8, matrix_s="470bg")


def Expr(clips, expr, **kwargs):
    """Wraps Vapoursynth Expr function."""
    visitor = v()
    visitor.visit(ast.parse(expr))
    expr = ' '.join(visitor.tokens)
    return core.std.Expr(clips, expr, **kwargs)


def AvsScale(video, width):
    """Scale to a new width."""
    kwargs = {'width': width, 'height': video.height * width // video.width}
    return core.resize.Bicubic(video, **kwargs)
