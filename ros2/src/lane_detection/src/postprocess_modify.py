import numpy as np
import torch
import cv2
from sklearn.cluster import DBSCAN

def postprocess_mask(
    seg_pred,
    threshold=0.5,
    min_area=300,
    eps=50,
    min_samples=1,
    samples=200
):
    """
    SCNN 로짓 출력을 후처리하여 차선 중심선을 계산합니다.
    Returns:
        lane_state: 0 (실패) 또는 1 (성공)
        center_x: 중심선 x 좌표 리스트
        center_y: 중심선 y 좌표 리스트
        merged: 병합된 차선 조각 리스트 (좌/우)
    """
    # 1. Sigmoid + NumPy 변환
    if isinstance(seg_pred, torch.Tensor):
        seg_pred = torch.sigmoid(seg_pred).squeeze().detach().cpu().numpy()

    # 2. Binarization + Morphology (강화된 close + dilate)
    binary_mask = (seg_pred > threshold).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_DILATE, kernel, iterations=2)

    # 3. Connected components → lane midpoints
    num_labels, labels = cv2.connectedComponents(binary_mask)
    lane_coords = []
    for lbl in range(1, num_labels):
        part = (labels == lbl).astype(np.uint8)
        coords = extract_lane_midpoints(part, min_area)
        if coords:
            lane_coords.append(coords)

    if not lane_coords:
        return 0, [], [], []

    # 4. Centroid clustering (DBSCAN)
    centroids = [np.mean(np.array(c), axis=0) for c in lane_coords]
    h, w = binary_mask.shape
    adaptive_eps = max(eps, int(0.025 * w))
    clustering = DBSCAN(eps=adaptive_eps, min_samples=min_samples).fit(np.array(centroids))

    merged = []
    for label in set(clustering.labels_):
        if label == -1:
            continue
        group = []
        for idx, pt_list in enumerate(lane_coords):
            if clustering.labels_[idx] == label:
                group.extend(pt_list)
        merged.append(group)

    # 5. 상위 2개 조각 선택 후 좌/우 정렬
    if len(merged) < 2:
        return 0, [], [], merged
    if len(merged) > 2:
        merged.sort(key=len, reverse=True)
        merged = sorted(merged[:2], key=lambda pts: np.mean([p[0] for p in pts]))

    # 6. Centerline 계산 (polyfit 방식)
    centerline = compute_centerline(merged[0], merged[1], samples)
    if not centerline:
        return 0, [], [], merged

    center_x, center_y = zip(*centerline)
    return 1, list(center_x), list(center_y), merged


def extract_lane_midpoints(mask, min_area=300, x_eps=None):
    """한 조각 마스크에서 y별로 x DBSCAN 클러스터링하여 중심점 추출"""
    if np.sum(mask) < min_area:
        return []

    h, w = mask.shape
    if x_eps is None:
        x_eps = max(1, int(0.005 * w))  # 0.5% of image width

    coords = []
    for y in range(h - 1, -1, -1):
        xs = np.where(mask[y] > 0)[0]
        if xs.size == 0:
            continue
        clustering = DBSCAN(eps=x_eps, min_samples=1).fit(xs.reshape(-1, 1))
        for label in set(clustering.labels_):
            cluster = xs[clustering.labels_ == label]
            coords.append((float(cluster.mean()), float(y)))
    return coords


def fit_polynomial(lane, degree=3):
    """x = f(y) 형태 다항식 피팅. 포인트 부족 시 2차 fallback."""
    pts = np.array(lane)
    if pts.shape[0] < 3:
        return None, None, None

    y = pts[:, 1]
    x = pts[:, 0]
    sorted_indices = np.argsort(y)
    y_sorted = y[sorted_indices]
    x_sorted = x[sorted_indices]

    y_unique, indices = np.unique(y_sorted, return_index=True)
    x_unique = x_sorted[indices]

    deg = degree if len(y_unique) > degree else 2
    if len(y_unique) <= deg:
        return None, None, None

    poly = np.poly1d(np.polyfit(y_unique, x_unique, deg))
    return poly, float(y_unique.min()), float(y_unique.max())


def compute_centerline(lane_left, lane_right, samples=200):
    """좌/우 차선 다항식을 통해 중심선 좌표 생성"""
    poly1, y1_min, y1_max = fit_polynomial(lane_left)
    poly2, y2_min, y2_max = fit_polynomial(lane_right)

    if poly1 is None or poly2 is None:
        return []

    y_start = max(y1_min, y2_min)
    y_end = min(y1_max, y2_max)
    if y_end <= y_start:
        return []

    ys = np.linspace(y_start, y_end, samples)
    centerline = [(float((poly1(y) + poly2(y)) / 2), float(y)) for y in ys]
    return centerline
