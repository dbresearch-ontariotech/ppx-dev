import numpy as np
import pandas as pd

def compute_pairwise_bbox_distances(bboxes: np.ndarray) -> np.ndarray:
    """
    Computes the pairwise custom bounding box distance matrix using N x N broadcasting.
    The distance between two boxes is defined as the minimum of their x-distance and y-distance.
    
    Args:
        bboxes: 2D NumPy array of shape (N, 4) containing bounding box coordinates.
        
    Returns:
        A 2D NumPy array of shape (N, N) representing the pairwise distances.
    """
    x0, y0, x1, y1 = bboxes[:, 0], bboxes[:, 1], bboxes[:, 2], bboxes[:, 3]

    # Calculate pairwise x-distances: max(0, max(x0_i, x0_j) - min(x1_i, x1_j))
    max_x0 = np.maximum(x0[:, None], x0[None, :])
    min_x1 = np.minimum(x1[:, None], x1[None, :])
    dx = np.maximum(0, max_x0 - min_x1)
    
    # Calculate pairwise y-distances: max(0, max(y0_i, y0_j) - min(y1_i, y1_j))
    max_y0 = np.maximum(y0[:, None], y0[None, :])
    min_y1 = np.minimum(y1[:, None], y1[None, :])
    dy = np.maximum(0, max_y0 - min_y1)
    
    # Layout distance is zero only when boxes overlap in both axes
    return np.maximum(dx, dy)

def build_layout_knn_graph(df: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """
    Constructs an undirected k-Nearest Neighbor graph for visual tokens.
    
    Args:
        df: DataFrame with index as token ID and columns ['x0', 'y0', 'x1', 'y1'].
        k: Number of nearest neighbors to compute per token.
        
    Returns:
        DataFrame with columns ['source', 'target', 'distance'].
    """

    # validate input: make sure df has the right columns
    required_columns = ['x0', 'y0', 'x1', 'y1']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"DataFrame must have columns {required_columns}")
    
    # validate input: all df.index must be unique
    if len(df.index) != len(set(df.index)):
        raise ValueError("DataFrame index must be unique")

    n_tokens = len(df)
    if n_tokens <= 1 or k <= 0:
        return pd.DataFrame(columns=["source", "target", "distance"])
        
    k = min(k, n_tokens - 1)
    
    # 1. Compute the N x N pairwise distance matrix using the refactored function
    bboxes: np.ndarray = df[['x0', 'y0', 'x1', 'y1']].values.astype(np.float32)
    dist_matrix = compute_pairwise_bbox_distances(bboxes)
    
    # 2. Prevent nodes from connecting to themselves
    np.fill_diagonal(dist_matrix, np.inf)
    
    # 3. Find k-nearest neighbors (partitioning is faster than sorting)
    knn_indices = np.argpartition(dist_matrix, k - 1, axis=1)[:, :k]
    
    # 4. Map back to edges
    sources = np.repeat(np.arange(n_tokens), k)
    targets = knn_indices.flatten()
    
    edges_df = pd.DataFrame({'src_pos': sources, 'tgt_pos': targets})
    
    # 5. Convert to an undirected graph by sorting the source/target positional indices
    edges_df['min_pos'] = np.minimum(edges_df['src_pos'], edges_df['tgt_pos'])
    edges_df['max_pos'] = np.maximum(edges_df['src_pos'], edges_df['tgt_pos'])
    unique_edges = edges_df.drop_duplicates(subset=['min_pos', 'max_pos']).copy()
    
    # 6. Assign the calculated distances and map back to the original DataFrame index IDs
    unique_edges['distance'] = dist_matrix[unique_edges['min_pos'], unique_edges['max_pos']]
    
    idx_array = df.index.values
    result_df = pd.DataFrame({
        'source': idx_array[unique_edges['min_pos'].values],
        'target': idx_array[unique_edges['max_pos'].values],
        'distance': unique_edges['distance'].values
    })
    
    return result_df

def get_graph_coordinates(
    bboxes: pd.DataFrame,
    graph: pd.DataFrame,
) -> pd.DataFrame:
    centers = pd.DataFrame({
        'x': ((bboxes['x0'] + bboxes['x1']) // 2).astype(int),
        'y': ((bboxes['y0'] + bboxes['y1']) // 2).astype(int),
    }, index=bboxes.index)

    result = graph[['source', 'target']].copy()
    result['x_s'] = centers.loc[graph['source'].values, 'x'].values
    result['y_s'] = centers.loc[graph['source'].values, 'y'].values
    result['x_t'] = centers.loc[graph['target'].values, 'x'].values
    result['y_t'] = centers.loc[graph['target'].values, 'y'].values
    return result
