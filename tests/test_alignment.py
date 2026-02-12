import numpy as np
import pandas as pd
import pytest

from ppx.core.alignment import compute_similarity
from ppx.core.models import VisualTokens


@pytest.fixture
def vtokens():
    """A page with 4 words in distinct quadrants."""
    words = pd.DataFrame({
        'text': ['alpha', 'beta', 'gamma', 'delta'],
        'x0':   [10,  200, 10,  200],
        'y0':   [10,  10,  200, 200],
        'x1':   [80,  280, 80,  280],
        'y1':   [40,  40,  230, 230],
    })
    return VisualTokens(words=words, page_height=300, page_width=300)


class TestComputeSimilarity:
    def test_exact_match_scores_highest(self, vtokens):
        """A location near a word should score highest when queried with that word."""
        page_locs = np.array([[45, 25]])  # near 'alpha'
        scores = compute_similarity(vtokens, page_locs, 'alpha', kx=0.5, ky=0.5)
        assert scores[0] == 1.0

    def test_no_match_scores_zero(self, vtokens):
        """A location near one word should score 0 against a completely different string."""
        page_locs = np.array([[45, 25]])  # near 'alpha'
        scores = compute_similarity(vtokens, page_locs, 'zzzzz', kx=0.3, ky=0.3)
        assert scores[0] == 0.0

    def test_multiple_locations(self, vtokens):
        """Each location should score highest against the word in its quadrant."""
        page_locs = np.array([
            [45, 25],   # near 'alpha' (top-left)
            [240, 25],  # near 'beta'  (top-right)
            [45, 215],  # near 'gamma' (bottom-left)
            [240, 215], # near 'delta' (bottom-right)
        ])
        for i, word in enumerate(['alpha', 'beta', 'gamma', 'delta']):
            scores = compute_similarity(vtokens, page_locs, word, kx=0.3, ky=0.3)
            assert scores[i] == scores.max(), f'{word}: expected loc {i} to score highest'

    def test_output_shape(self, vtokens):
        """Output should be a 1D array with one score per page location."""
        page_locs = np.array([[10, 10], [100, 100], [200, 200]])
        scores = compute_similarity(vtokens, page_locs, 'alpha', kx=0.5, ky=0.5)
        assert scores.shape == (3,)

    def test_scores_between_zero_and_one(self, vtokens):
        """All Jaccard scores should be in [0, 1]."""
        page_locs = np.array([[45, 25], [240, 215]])
        scores = compute_similarity(vtokens, page_locs, 'alpha beta', kx=0.5, ky=0.5)
        assert np.all(scores >= 0.0)
        assert np.all(scores <= 1.0)

    def test_empty_text(self, vtokens):
        """Empty query text should give 0 scores everywhere."""
        page_locs = np.array([[45, 25]])
        scores = compute_similarity(vtokens, page_locs, '', kx=0.5, ky=0.5)
        assert scores[0] == 0.0

    def test_narrow_neighborhood_misses(self, vtokens):
        """A very small neighborhood that doesn't reach any word should score 0."""
        page_locs = np.array([[150, 150]])  # center, no words nearby
        scores = compute_similarity(vtokens, page_locs, 'alpha', kx=0.05, ky=0.05)
        assert scores[0] == 0.0
