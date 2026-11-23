"""Damped double pendulum for the ID badge: the strap swings from the top ring, the badge from the clasp.

Why simulate instead of hand-keying: real coupled motion (the badge lags the strap and the two drift in and out
of phase) is what makes the swing read as physical. The result is sampled into SMIL keyTimes.
"""
from __future__ import annotations

import math


def _accel(y, l1, l2, m1, m2, g, c1, c2):
    t1, t2, w1, w2 = y
    d = t1 - t2
    den = 2 * m1 + m2 - m2 * math.cos(2 * d)
    a1 = (-g * (2 * m1 + m2) * math.sin(t1) - m2 * g * math.sin(t1 - 2 * t2)
          - 2 * math.sin(d) * m2 * (w2 * w2 * l2 + w1 * w1 * l1 * math.cos(d))) / (l1 * den)
    a2 = (2 * math.sin(d) * (w1 * w1 * l1 * (m1 + m2) + g * (m1 + m2) * math.cos(t1)
                             + w2 * w2 * l2 * m2 * math.cos(d))) / (l2 * den)
    return a1 - c1 * w1, a2 - c2 * w2


def swing(l1=144.0, l2=148.0, m1=0.16, m2=1.0, g=2180.0, damping=(0.8, 1.0), kick=0.4,
          seconds=9.0, out_hz=25, peak_deg=5.4):
    """Returns [(t, strap_deg, badge_deg)] sampled at out_hz, scaled so the first big swing peaks at peak_deg."""
    dt, steps_per_out = 1 / 480, 480 // out_hz
    y = [0.0, 0.0, kick, kick]
    rows = []
    for i in range(int(seconds * out_hz) + 1):
        rows.append((i / out_hz, y[0], y[1]))
        for _ in range(steps_per_out):
            def f(s):
                a1, a2 = _accel(s, l1, l2, m1, m2, g, *damping)
                return [s[2], s[3], a1, a2]
            k1 = f(y)
            k2 = f([a + dt / 2 * b for a, b in zip(y, k1)])
            k3 = f([a + dt / 2 * b for a, b in zip(y, k2)])
            k4 = f([a + dt * b for a, b in zip(y, k3)])
            y = [a + dt / 6 * (p + 2 * q + 2 * r + s) for a, p, q, r, s in zip(y, k1, k2, k3, k4)]
    peak = max(abs(r[2]) for r in rows)
    k = math.radians(peak_deg) / peak
    return [(t, math.degrees(a * k), math.degrees(b * k)) for t, a, b in rows]


def drop(t: float, fall: float = 0.55, height: float = 540.0) -> float:
    """Vertical offset while the lanyard falls (gravity ease-in) and the strap stretches and recovers."""
    if t < fall:
        return -height * (1 - (t / fall) ** 2)
    u = t - fall
    return 17 * math.exp(-4.6 * u) * math.sin(2 * math.pi * u / 0.6)


def retract(t: float, start: float, height: float = 540.0) -> float:
    """Small dip, then the assembly is pulled up out of frame."""
    u = t - start
    if u < 0.3:
        return 7 * math.sin(math.pi * u / 0.3)
    if u < 1.1:
        return -height * ((u - 0.3) / 0.8) ** 3
    return -height


if __name__ == "__main__":
    rows = swing()
    for t in (0.5, 1, 2, 3, 4, 6, 8, 9):
        r = min(rows, key=lambda x: abs(x[0] - t))
        print(f"t={t:3.1f}s strap {r[1]:6.2f} deg  badge {r[2]:6.2f} deg")
