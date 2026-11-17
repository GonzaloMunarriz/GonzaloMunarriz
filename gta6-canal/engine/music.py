"""Generador de música synthwave original (sin samples, sin copyright de terceros).

Produce un loop de fondo instrumental a partir de osciladores básicos.
"""
import numpy as np
import wave

SR = 44100


def _note(n):
    # n = número MIDI
    return 440.0 * 2 ** ((n - 69) / 12)


def _env(length, a=0.01, r=0.2):
    t = np.arange(length) / SR
    e = np.ones(length)
    ai = int(a * SR)
    if ai > 0:
        e[:ai] = np.linspace(0, 1, ai)
    ri = min(int(r * SR), length)
    e[-ri:] *= np.linspace(1, 0, ri)
    return e


def _saw(freq, length, detune=0.0):
    t = np.arange(length) / SR
    out = np.zeros(length)
    for d in (-detune, 0, detune):
        f = freq * (1 + d)
        out += 2 * ((t * f) % 1.0) - 1
    return out / 3


def _lowpass(x, alpha):
    # filtro one-pole sencillo (vectorizado por bloques no hace falta: usamos lfilter manual)
    y = np.empty_like(x)
    acc = 0.0
    a = alpha
    for i in range(0, len(x), 4096):
        blk = x[i:i + 4096]
        out = np.empty_like(blk)
        for j, v in enumerate(blk):
            acc += a * (v - acc)
            out[j] = acc
        y[i:i + 4096] = out
    return y


def _lp_fast(x, k=12):
    # media móvil como paso bajo barato
    kern = np.ones(k) / k
    return np.convolve(x, kern, mode="same")


PROGS = {
    # (raíz MIDI, acordes como intervalos sobre la escala menor)
    "a": [(57, [0, 3, 7]), (53, [0, 4, 7]), (48, [0, 4, 7]), (55, [0, 4, 7])],   # Am F C G
    "d": [(50, [0, 3, 7]), (58, [0, 4, 7]), (53, [0, 4, 7]), (57, [0, 4, 7])],   # Dm Bb F A
    "e": [(52, [0, 3, 7]), (48, [0, 4, 7]), (55, [0, 4, 7]), (50, [0, 4, 7])],   # Em C G D
    "f": [(53, [0, 3, 7]), (49, [0, 4, 7]), (56, [0, 4, 7]), (51, [0, 4, 7])],   # Fm Db Ab Eb
}


def make_loop(key="a", bpm=96, bars=16, seed=1):
    rng = np.random.default_rng(seed)
    beat = 60.0 / bpm
    bar_len = int(4 * beat * SR)
    total = bar_len * bars
    mix = np.zeros(total)
    prog = PROGS[key]
    for b in range(bars):
        root, ints = prog[b % 4]
        start = b * bar_len
        # pad
        pad = np.zeros(bar_len)
        for iv in ints:
            pad += _saw(_note(root + iv), bar_len, detune=0.004)
        pad = _lp_fast(pad, 24) * _env(bar_len, a=0.25, r=0.4) * 0.16
        mix[start:start + bar_len] += pad
        # bajo en corcheas
        eighth = bar_len // 8
        for k in range(8):
            f = _note(root - 12)
            s = start + k * eighth
            tone = _saw(f, eighth, 0.0)
            tone = _lp_fast(tone, 40) * _env(eighth, a=0.005, r=0.08) * 0.22
            mix[s:s + eighth] += tone
        # arpegio suave en semicorcheas (solo en la segunda mitad del loop)
        if b >= bars // 2:
            six = bar_len // 16
            seq = [0, 1, 2, 1] * 4
            for k in range(16):
                iv = ints[seq[k]] + 12
                s = start + k * six
                t = np.arange(six) / SR
                tone = np.sin(2 * np.pi * _note(root + iv) * t)
                tone *= _env(six, a=0.003, r=0.12) * 0.05
                mix[s:s + six] += tone
        # batería
        q = bar_len // 4
        for k in range(4):
            s = start + k * q
            # kick
            n = int(0.25 * SR)
            t = np.arange(n) / SR
            kick = np.sin(2 * np.pi * (50 + 90 * np.exp(-t * 30)) * t) * np.exp(-t * 9) * 0.55
            mix[s:s + n] += kick[: max(0, min(n, total - s))]
            # snare en 2 y 4
            if k in (1, 3):
                n2 = int(0.18 * SR)
                t2 = np.arange(n2) / SR
                sn = rng.standard_normal(n2) * np.exp(-t2 * 22) * 0.18
                sn += np.sin(2 * np.pi * 190 * t2) * np.exp(-t2 * 30) * 0.15
                mix[s:s + n2] += sn
            # hats en corcheas
            for h in (0, q // 2):
                n3 = int(0.04 * SR)
                hs = s + h
                hat = np.diff(rng.standard_normal(n3 + 1)) * np.exp(-np.arange(n3) / SR * 90) * 0.05
                mix[hs:hs + n3] += hat[: max(0, min(n3, total - hs))]
    mix /= max(1e-6, np.abs(mix).max()) * 1.1
    return mix


def write_music(path, seconds, key="a", bpm=96, seed=1):
    loop = make_loop(key=key, bpm=bpm, seed=seed)
    reps = int(np.ceil(seconds * SR / len(loop))) + 1
    full = np.tile(loop, reps)[: int(seconds * SR)]
    # fade in/out
    fi = int(2 * SR)
    fo = int(4 * SR)
    full[:fi] *= np.linspace(0, 1, fi)
    full[-fo:] *= np.linspace(1, 0, fo)
    stereo = np.stack([full, np.roll(full, 220)], axis=1)
    data = (stereo * 32767 * 0.9).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
