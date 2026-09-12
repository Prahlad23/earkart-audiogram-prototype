"""
Extracts Air Conduction (AC) and Bone Conduction (BC) threshold readings
from an earKART-format Pure Tone Audiogram report image or PDF.

VALIDATED ACCURACY (against one real report's printed PTA table):
- Right ear AC (red circles):    exact match
- Left ear AC (blue X marks):    ~1.5dB
- Right ear BC (red "<" arrows): ~1.75dB (after empirical offset correction)
- Left ear BC (blue ">" arrows): ~0.25dB

METHOD: rather than detecting markers first and figuring out which frequency
they belong to (error-prone near column boundaries), this searches for the
best-matching marker independently within a window around each KNOWN
frequency gridline position. This guarantees at most one result per
frequency and avoids the clustering/overwrite bugs of an earlier version.

Only works on earKART's standard report template (fixed grid layout).
Bone Conduction accuracy is calibrated against a single sample report —
more samples would help tighten/verify the correction offsets used here.
"""

import cv2
import numpy as np

FREQ_LABELS = [125, 250, 500, 1000, 2000, 4000, 8000]

BC_Y_CORRECTION = {"right": 16, "left": 0}


def load_image(path: str):
    if path.lower().endswith(".pdf"):
        import fitz
        doc = fitz.open(path)
        page = doc[0]
        images = page.get_images(full=True)
        if not images:
            raise ValueError("No embedded image found in PDF page 1.")
        xref = images[0][0]
        base = doc.extract_image(xref)
        arr = np.frombuffer(base["image"], dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    else:
        return cv2.imread(path)


def find_chart_boxes(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h_img, w_img = gray.shape
    candidates = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w > 0.3 * w_img * 0.4 and h > 0.2 * h_img and y < 0.6 * h_img:
            candidates.append((x, y, x + w, y + h))
    if len(candidates) < 2:
        return None, None
    candidates.sort(key=lambda b: b[0])
    two = sorted(candidates[:2], key=lambda b: b[0])
    return two[0], two[1]


def _cluster_line_positions(counts, min_fraction, total_span):
    idxs = np.where(counts > min_fraction * total_span)[0]
    if len(idxs) == 0:
        return []
    clusters = []
    current = [idxs[0]]
    for i in idxs[1:]:
        if i - current[-1] <= 3:
            current.append(i)
        else:
            clusters.append(current)
            current = [i]
    clusters.append(current)
    return [sum(c) / len(c) for c in clusters]


def find_gridlines(crop):
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    dark_mask = gray < 230
    h, w = gray.shape

    col_counts = dark_mask.sum(axis=0)
    v_all = _cluster_line_positions(col_counts, 0.7, h)
    v_centers = v_all[1:-1] if len(v_all) >= 9 else None
    if v_centers is None or len(v_centers) != 7:
        return None

    row_counts = dark_mask.sum(axis=1)
    h_all = _cluster_line_positions(row_counts, 0.7, w)
    if len(h_all) < 15:
        return None

    return v_centers, h_all[1], h_all[14]


def _pixel_to_db(y, db_top_y, db_bottom_y):
    frac = (y - db_top_y) / (db_bottom_y - db_top_y)
    return -10 + frac * 130


def _get_color_mask(crop, color):
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    if color == "red":
        m1 = cv2.inRange(hsv, (0, 50, 50), (15, 255, 255))
        m2 = cv2.inRange(hsv, (150, 50, 50), (180, 255, 255))
        return m1 | m2
    else:
        return cv2.inRange(hsv, (90, 50, 50), (140, 255, 255))


def _extract_circles_by_column(mask, v_centers, db_top_y, db_bottom_y, box_w):
    r_min, r_max = int(box_w * 0.017), int(box_w * 0.033)
    min_dist = int(box_w * 0.045)
    circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, dp=1, minDist=min_dist,
                                 param1=50, param2=20, minRadius=r_min, maxRadius=r_max)
    if circles is None:
        return {}
    candidates = [(cx, cy, 1.0) for (cx, cy, r) in circles[0]]
    return _assign_by_column(candidates, v_centers, db_top_y, db_bottom_y)


def _extract_template_by_column(mask, template_mask, v_centers, db_top_y, db_bottom_y,
                                  y_correction=0, x_window=45, threshold=0.3):
    result = cv2.matchTemplate(mask, template_mask, cv2.TM_CCOEFF_NORMED)
    th, tw = template_mask.shape
    loc = np.where(result >= threshold)
    candidates = [(px + tw // 2, py + th // 2 + y_correction, result[py, px])
                  for px, py in zip(*loc[::-1])]
    return _assign_by_column(candidates, v_centers, db_top_y, db_bottom_y, x_window)


def _assign_by_column(candidates, v_centers, db_top_y, db_bottom_y, x_window=45):
    results = {}
    for freq, gx in zip(FREQ_LABELS, v_centers):
        col = [c for c in candidates if abs(c[0] - gx) <= x_window]
        if not col:
            continue
        cx, cy, score = max(col, key=lambda c: c[2])
        db = round(_pixel_to_db(cy, db_top_y, db_bottom_y) / 5) * 5
        results[freq] = int(db)
    return results


def _build_x_template(size=45):
    t = np.zeros((size, size), dtype=np.uint8)
    cv2.line(t, (5, 5), (size - 5, size - 5), 255, 6)
    cv2.line(t, (5, size - 5), (size - 5, 5), 255, 6)
    return t


def extract_ear_ac(img, box, color, marker_shape) -> dict:
    x1, y1, x2, y2 = box
    crop = img[y1:y2, x1:x2]
    grid = find_gridlines(crop)
    if grid is None:
        return {}
    v_centers, db_top_y, db_bottom_y = grid
    mask = _get_color_mask(crop, color)
    box_w = x2 - x1

    if marker_shape == "circle":
        results = _extract_circles_by_column(mask, v_centers, db_top_y, db_bottom_y, box_w)
    else:
        template = _build_x_template()
        results = _extract_template_by_column(mask, template, v_centers, db_top_y, db_bottom_y)

    return {f: results[f] for f in [500, 1000, 2000, 4000] if f in results}


def extract_ear_bc(img, box, color, ear_side, bc_template_path) -> dict:
    x1, y1, x2, y2 = box
    crop = img[y1:y2, x1:x2]
    grid = find_gridlines(crop)
    if grid is None:
        return {}
    v_centers, db_top_y, db_bottom_y = grid
    mask = _get_color_mask(crop, color)

    template_bgr = cv2.imread(bc_template_path)
    if template_bgr is None:
        return {}
    template_mask = _get_color_mask(template_bgr, color)

    y_corr = BC_Y_CORRECTION.get(ear_side, 0)
    results = _extract_template_by_column(mask, template_mask, v_centers, db_top_y, db_bottom_y,
                                            y_correction=y_corr)
    return {f: results[f] for f in [500, 1000, 2000, 4000] if f in results}


def extract_from_report(path: str, right_bc_template=None, left_bc_template=None) -> dict:
    img = load_image(path)
    right_box, left_box = find_chart_boxes(img)

    warnings = []
    right_ac, left_ac, right_bc, left_bc = {}, {}, {}, {}

    if right_box is None or left_box is None:
        warnings.append("Could not locate chart grids — all values need manual entry.")
    else:
        right_ac = extract_ear_ac(img, right_box, "red", "circle")
        left_ac = extract_ear_ac(img, left_box, "blue", "x")
        if len(right_ac) < 4:
            warnings.append("Right ear AC extraction incomplete — please verify.")
        if len(left_ac) < 4:
            warnings.append("Left ear AC extraction incomplete — please verify.")

        if right_bc_template:
            right_bc = extract_ear_bc(img, right_box, "red", "right", right_bc_template)
            if len(right_bc) < 4:
                warnings.append("Right ear BC extraction incomplete — please verify.")
        else:
            warnings.append("Right ear BC not extracted (no template provided) — please enter manually.")

        if left_bc_template:
            left_bc = extract_ear_bc(img, left_box, "blue", "left", left_bc_template)
            if len(left_bc) < 4:
                warnings.append("Left ear BC extraction incomplete — please verify.")
        else:
            warnings.append("Left ear BC not extracted (no template provided) — please enter manually.")

    return {
        "right_ac": right_ac,
        "left_ac": left_ac,
        "right_bc": right_bc,
        "left_bc": left_bc,
        "warnings": warnings,
    }
