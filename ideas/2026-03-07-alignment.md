# Alignment using dynamic programming

We are going to solve an alignment problem as follows:

Consider a list of elements $X$
$$
X = \{x_0, x_1, \dots, x_{n-1}\}
$$
that will be mapped to intervals of another list $Y = \{y_0, y_1, \dots, y_{L-1}\}$.  An interval of $Y$ is simply a range $(a, b)$ where $0\leq a < L$ and $a \leq b < L$ where $a$ is the start of the interval (inclusive) and $b$ is the end (exclusive).  An empty interval would be $(a, a)$.

A similarity score function is given:
$$
\mathrm{sim}: X\times \mathrm{Interval}(Y)\to\mathbb{R}^+
$$
We can assume that the similarity score is zero for empty intervals: $\mathrm{sim}(x, \emptyset) = 0$.

We will use dynamic programming to find optimal alignment of $X$ to $\mathrm{Interval}(Y)$.

**Output** of algorithm is the alignment function:

$$
h : X \to \mathrm{Interval}(Y)
$$
satisfying the following condition:

1. all intervals must be contiguous.  Namely $\forall i$, $b(h(x_i)) = a(h(x_{i+1}))$.
2. the intervals cover $Y$ completely.  Namely $a(h(x_0)) = 0$ and $b(h(x_{n-1})) = L$.

We want to maximize the total cumulative similarity scores:
$$
J = \mathrm{max}\sum_{i=0}^{n-1}\mathrm{sim}(x_i, h(x_i))
$$
## Solution

We will formulate a dynamic program that computes partial alignment.
$$
h_{ij}:\{x_0, \dots x_i\}\to\mathrm{Interval}(\{y_0, \dots, y_j\})
$$
by computing two matrices:

(1): score matrix $J\in\mathbb{R}^{n\times L}$.  Each entry $J(i, j)$ will be the optimal score of aligning $\{x_0, \dots, x_{i-1}\}$ to intervals of $\{y_0, \dots, y_{j-1}\}$.

(2): beginning position matrix $A\in\mathbb{N}^{n\times L}$.  Each entry $A(i,j)$ is the start position of interval $h_{ij}(x_i)$.

Once these matrices are completely computed, we can obtain the alignment $h = h_{n,L}$.

## Hints on dynamic programming

### Initial case

$$
J(0, j) = \mathrm{sim}(x_0, Y[0:j-1])
$$

$$
A(0, j) = 0
$$
### Recursive case

To compute $(i+1, j)$, we have the following:
$$
J(i+1, j) = \max\{J(i,a)+\mathrm{sim}(x_{i+1}, Y[a,j]): 0\leq a \leq j\}
$$
$$
A(i+1, j) = \mathrm{argmax}\{J(i,a)+\mathrm{sim}(x_{i+1}, Y[a,j]): 0\leq a \leq j\}
$$
The final $h$ can be computed by looking up $A$ matrix, starting with $x_{n-1}$, and then $x_{n-2}$, etc.

# Python implementation
```python
def dp_align(X: list, Y:list, sim) -> list[tuple[int,int]]:
	...
```