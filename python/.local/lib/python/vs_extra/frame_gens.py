from collections import deque
import vapoursynth as vs
import numpy as np


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


class scenes(object):
    """Groups frames into camera shots."""

    class Scene(object):
        def __iter__(self): return self                            # noqa: E704

        def __init__(self, base_gen):
            self._max_length = int(1e15)
            self._base_gen = base_gen
            self._scene_length = 0
            self._start_guard = 1

        def _next_frame(self):
            base_gen = self._base_gen

            try:
                next_el = next(base_gen.iterable)
                base_gen.buffer.append(next_el)
            except StopIteration:
                pass

            return base_gen.buffer.popleft()

        def __next__(self):
            if self._base_gen.buffer:
                if self._start_guard:
                    self._start_guard -= 1
                    return self._next_frame()

            base_gen = self._base_gen

            def _has_scp(vsnode):
                if isinstance(vsnode, tuple):
                    vsnode = vsnode[0]

                scp_prop = '_SceneChangePrev'
                return vsnode.props[scp_prop]

            self._scene_length += 1

            ml = self._max_length
            if self._scene_length == ml:
                raise StopIteration

            if base_gen.buffer:
                nextnode = base_gen.buffer[0]

                if not _has_scp(nextnode):
                    return self._next_frame()
            raise StopIteration

        def lookahead_list(self):
            seq = list(self._base_gen.buffer)

            def _has_scp(vsnode):
                if isinstance(vsnode, tuple):
                    vsnode = vsnode[0]

                scp_prop = '_SceneChangePrev'
                return vsnode.props[scp_prop]

            v = self._start_guard

            if v >= len(seq): return seq                           # noqa: E701

            scpseq = [_has_scp(f) for f in seq]
            scpseq = np.asarray(scpseq)[v:]
            idx = scpseq.argmax()

            if not scpseq[idx]: return seq                        # noqa: E701

            return seq[:v + idx]

        def assert_min_length(self, v):
            self._start_guard = max(v, 1)
            return self

        def assert_max_length(self, v):
            self._max_length = v
            return self

    def __init__(self, frames, bs=1):
        self.iterable = frames
        self.buffer = deque()

        for _ in range(bs):
            try:
                f = next(self.iterable)
                self.buffer.append(f)
            except StopIteration:
                break

    def __next__(self):
        if len(self.buffer) == 0:
            raise StopIteration

        return scenes.Scene(self)

    def __iter__(self): return self                                # noqa: E704
