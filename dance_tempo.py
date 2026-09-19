"""
Estimate the tempo of the dancing in a video clip (no audio involved).

Per-frame mean optical-flow magnitude over a region of interest gives a motion
envelope; its dominant periodicity is the step rate. Optical flow rather than
raw frame differencing because haze and flickering light also change pixels,
but they don't produce the coherent large-magnitude motion that limbs do.

Usage:
    python dance_tempo.py shuffle.mp4 [--roi lower|full] [--min 60] [--max 180]
    python dance_tempo.py --selftest
"""
import sys
import numpy as np


def motion_envelope(path, roi="lower", width=320):
    """Mean optical-flow magnitude per frame pair. Returns (envelope, fps)."""
    import cv2
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"cannot open {path}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        raise RuntimeError(f"no usable fps in {path}")

    def prep(frame):
        h, w = frame.shape[:2]
        g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        g = cv2.resize(g, (width, max(1, int(h * width / w))))
        if roi == "lower":
            g = g[int(g.shape[0] * 2 / 3):, :]   # feet live in the bottom third
        return g

    ok, frame = cap.read()
    if not ok:
        raise RuntimeError(f"no frames in {path}")
    prev, env = prep(frame), []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        cur = prep(frame)
        flow = cv2.calcOpticalFlowFarneback(prev, cur, None,
                                            0.5, 3, 15, 3, 5, 1.2, 0)
        env.append(float(np.hypot(flow[..., 0], flow[..., 1]).mean()))
        prev = cur
    cap.release()
    return np.asarray(env), fps


def estimate_bpm(env, fps, bpm_min=60.0, bpm_max=180.0):
    """Dominant periodicity of a motion envelope, in beats per minute.

    Returns (bpm, confidence, autocorrelation). Confidence is the peak's height
    above the local baseline, 0..1; below ~0.15 the signal is not periodic.
    """
    x = np.asarray(env, dtype=float)
    if x.size < 16:
        raise ValueError("envelope too short to estimate tempo")
    # detrend: remove slow drift (camera move, light ramp) so autocorrelation
    # measures the step rhythm and not the overall energy curve
    k = max(3, int(round(fps)) | 1)
    pad = np.pad(x, k // 2, mode="edge")
    x = x - np.convolve(pad, np.ones(k) / k, mode="valid")[:x.size]
    x -= x.mean()
    if not np.any(x):
        raise ValueError("envelope is constant; no motion detected")

    n = 1 << (2 * x.size - 1).bit_length()
    spec = np.fft.rfft(x, n)
    ac = np.fft.irfft(spec * np.conj(spec), n)[:x.size]
    ac /= ac[0]

    lo = max(1, int(np.floor(fps * 60.0 / bpm_max)))
    hi = min(x.size - 2, int(np.ceil(fps * 60.0 / bpm_min)))
    if hi <= lo:
        raise ValueError("bpm range not resolvable at this fps/duration")
    band = ac[lo:hi + 1]
    # A periodic signal peaks at every multiple of its period, so a bare argmax
    # lands on an arbitrary octave. Weight by a log-normal prior centred on
    # 120 BPM (one octave sigma) to break the tie the way a listener would.
    lags = np.arange(lo, hi + 1)
    prior = np.exp(-0.5 * (np.log2(60.0 * fps / lags / 120.0) / 1.0) ** 2)
    i = int(np.argmax(band * prior)) + lo

    # parabolic interpolation around the peak -> sub-frame lag precision
    y0, y1, y2 = ac[i - 1], ac[i], ac[i + 1]
    denom = y0 - 2 * y1 + y2
    lag = i + (0.5 * (y0 - y2) / denom if denom else 0.0)

    return 60.0 * fps / lag, float(max(0.0, y1 - band.mean())), ac


def _selftest():
    fps = 24.0
    for want in (96.0, 128.0, 150.0):
        t = np.arange(int(fps * 10)) / fps
        sig = (np.abs(np.sin(np.pi * want / 60.0 * t))          # footfalls
               + 0.3 * np.sin(2 * np.pi * 0.1 * t)              # slow drift
               + 0.05 * np.sin(2 * np.pi * 11.0 * t))           # flicker
        got, conf, _ = estimate_bpm(sig, fps)
        assert abs(got - want) < 2.0, f"{want} -> {got:.1f}"
        assert conf > 0.15, f"{want} conf {conf:.2f}"
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
        sys.exit(0)

    args = sys.argv[1:]
    def opt(name, default):
        return args[args.index(name) + 1] if name in args else default
    path = args[0]
    roi = opt("--roi", "lower")
    lo, hi = float(opt("--min", 60)), float(opt("--max", 180))

    env, fps = motion_envelope(path, roi=roi)
    bpm, conf, _ = estimate_bpm(env, fps, lo, hi)
    print(f"{path}  fps={fps:g}  frames={env.size + 1}  roi={roi}")
    print(f"tempo: {bpm:.1f} BPM   confidence {conf:.2f}")
    print(f"octaves: {bpm / 2:.1f} / {bpm:.1f} / {bpm * 2:.1f} BPM")
