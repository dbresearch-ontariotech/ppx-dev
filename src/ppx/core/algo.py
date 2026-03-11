from typing import Any, Callable


def greedy_align_nodes(X: list, Y: list, sim: Callable[[Any, Any], float], a: int = 0, b: int = None) -> list[tuple[int, int]]:
    """Greedy O(n·L) alignment: commit to the locally best split point for each element.

    For each X[i], scan all possible end positions k in [pos, b] and pick the k that
    maximises sim(X[i], Y[pos:k]). The last element always gets the remainder.
    """
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
    L = b - a  # length of the sublist Y[a:b]

    # J[i][k] = optimal score for aligning X[0..i] to Y[a..a+k]  (k is relative offset)
    # A[i][k] = relative start of interval assigned to X[i] in that optimal alignment
    J = [[float("-inf")] * (L + 1) for _ in range(n)]
    A = [[0] * (L + 1) for _ in range(n)]

    # Initial case: X[0] always starts at a, covers Y[a:a+k]
    for k in range(L + 1):
        J[0][k] = sim(X[0], Y[a:a + k])
        A[0][k] = 0

    # Recursive case (all indices relative to a)
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

    # Traceback starting from (n-1, L); convert relative offsets to absolute indices
    intervals = [None] * n
    k = L
    for i in range(n - 1, -1, -1):
        r = A[i][k]
        intervals[i] = (a + r, a + k)
        k = r

    return intervals

def hybrid_align_nodes(X: list, Y: list, sim: Callable[[Any, Any], float], a: int = 0, b: int = None) -> list[tuple[int, int]]:
    """
    if Y is long, use greedy, otherwise use dp
    """
    if len(Y) > 100:
        return greedy_align_nodes(X, Y, sim, a, b)
    else:
        return dp_align_nodes(X, Y, sim, a, b)
    