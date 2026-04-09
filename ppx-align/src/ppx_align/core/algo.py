from typing import Any, Callable


def greedy_align_nodes(X: list, Y: list, sim: Callable[[Any, Any], float], a: int = 0, b: int = None) -> list[tuple[int, int]]:
    n = len(X)
    if b is None:
        b = len(Y)

    intervals = []
    pos = a
    for i in range(n):
        if i == n - 1:
            intervals.append((pos, b))
            break
        best_score = float("-inf")
        best_k = pos
        for k in range(pos, b + 1):
            score = sim(X[i], Y[pos:k])
            if score > best_score:
                best_score = score
                best_k = k
        intervals.append((pos, best_k))
        pos = best_k

    return intervals


def dp_align_nodes(X: list, Y: list, sim: Callable[[Any, Any], float], a: int = 0, b: int = None) -> list[tuple[int, int]]:
    n = len(X)
    if b is None:
        b = len(Y)
    L = b - a

    J = [[float("-inf")] * (L + 1) for _ in range(n)]
    A = [[0] * (L + 1) for _ in range(n)]

    for k in range(L + 1):
        J[0][k] = sim(X[0], Y[a:a + k])
        A[0][k] = 0

    for i in range(1, n):
        for k in range(L + 1):
            best_score = float("-inf")
            best_r = 0
            for r in range(k + 1):
                score = J[i - 1][r] + sim(X[i], Y[a + r:a + k])
                if score > best_score:
                    best_score = score
                    best_r = r
            J[i][k] = best_score
            A[i][k] = best_r

    intervals = [None] * n
    k = L
    for i in range(n - 1, -1, -1):
        r = A[i][k]
        intervals[i] = (a + r, a + k)
        k = r

    return intervals

def hybrid_align_nodes(X: list, Y: list, sim: Callable[[Any, Any], float], a: int = 0, b: int = None) -> list[tuple[int, int]]:
    if len(Y) > 100:
        return greedy_align_nodes(X, Y, sim, a, b)
    else:
        return dp_align_nodes(X, Y, sim, a, b)


def DP_align_strings(
    patterns: list[str],
    text: str,
    sim: Callable[[str, str], float],
) -> list[tuple[int, int]]:
    N = len(patterns)
    T = len(text)

    J = [[0.0] * (T + 1) for _ in range(N + 1)]
    l_star: list[list[int | None]] = [[None] * (T + 1) for _ in range(N + 1)]

    for n in range(1, N + 1):
        p = patterns[n - 1]
        for r in range(1, T + 1):
            best_score = J[n][r - 1]
            best_l = None

            for l in range(r + 1):
                score = J[n - 1][l] + sim(p, text[l:r])
                if score > best_score:
                    best_score = score
                    best_l = l

            J[n][r] = best_score
            l_star[n][r] = best_l

    alignment: list[tuple[int, int] | None] = [None] * N
    r = T
    for n in range(N, 0, -1):
        while r >= 0 and l_star[n][r] is None:
            r -= 1
        if r < 0:
            break
        l = l_star[n][r]
        alignment[n - 1] = (l, r)
        r = l

    return alignment
