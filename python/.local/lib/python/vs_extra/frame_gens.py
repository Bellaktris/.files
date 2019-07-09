from itertools import accumulate
from itertools import groupby
import vapoursynth as vs


VSClip = vs.VideoNode


def async_frames(clip, buf_sz=48):
    # type: (VSClip, int) -> vs.VideoNode
    """Provides asyncronous .frames()."""

    N = clip.num_frames
    buf = [None] * min(buf_sz, N)

    for i in range(0, len(buf)):
        buf[i] = clip.get_frame_async(i)

    for i in range(len(buf), N):
        yield buf[i % len(buf)].result()
        j = i % len(buf)

        buf[j] = clip.get_frame_async(i)

    for i in range(N, N + len(buf)):
        yield buf[i % len(buf)].result()


def scenes(*vframes, ml=11, k=0):
    """Groups frames by _SceneChangePrev prop."""

    frames = zip(*vframes)

    def has_scp(fs):
        return fs[k].props['_SceneChangePrev']

    def accumulate_fn(sum, element):
        return sum[0] + element[0], element[1]

    frames = ((has_scp(f), f) for f in frames)

    def contract_dissolves(vdata):
        pv, pf = next(vdata)

        for v, f in vdata:
            x = v

            if pv == 1:
                x = 0

            yield pv, pf
            pv, pf = x, f

        yield pv, pf

    def clean(vdata):
        j = -ml - 1
        for i, (v, f) in enumerate(vdata):
            if v == 0 or i - j <= ml:
                yield (0, f)
            else:
                yield (1, f)
                j = i

    frames = clean(contract_dissolves(frames))
    frames = accumulate(frames, accumulate_fn)

    scenes = groupby(frames, lambda el: el[0])
    return (map(lambda f: f[1], s) for _, s in scenes)
