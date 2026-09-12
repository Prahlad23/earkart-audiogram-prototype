"""
Extracts Air Conduction (AC) threshold readings from an earKART-format
Pure Tone Audiogram report image or PDF.

CURRENT SCOPE:
- Right ear AC (red circles): validated against report's own PTA table (exact match)
- Left ear AC (blue X marks): validated against report's own PTA table (~1.5dB)
- Bone Conduction (dashed arrows, both ears): NOT implemented yet — returns {}
  (caller should prompt the user to enter these manually)

Calibration approach: rather than assuming the chart grid is evenly spaced
from box edge to box edge, this detects the REAL gridline pixel positions
(both frequency columns and dB rows) and snaps markers to the nearest real
gridline. This avoids drift/misassignment near column boundaries.

Only works on earKART's standard report template (fixed grid layout).
"""

import cv2
import numpy as np

FREQ_LABELS = [125, 250, 500, 1000, 2000, 4000, 8000]


def load_image(path: str):
    """Loads a report as an image. If given a PDF, extracts the embedded page image."""
    if path.lower().endswith(".pdf"):
        import fitz  # PyMuPDF
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
    """Locates the right-ear and left-ear chart grid boxes on the standard template."""
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
    return two[0], two[1]  # right_box, left_box


def _cluster_line_positions(counts, min_fraction, total_span):
    """Finds gridline pixel positions from a per-row/column dark-pixel count array."""
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
    """
    Returns (v_centers, db_top_y, db_bottom_y):
      v_centers: 7 real x-positions for the frequency columns (125Hz..8000Hz)
      db_top_y: real y-position of the -10 dB gridline
      db_bottom_y: real y-position of the 120 dB gridline
    Returns None if detection fails (e.g. non-standard image).
    """
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    dark_mask = gray < 230
    h, w = gray.shape

    col_counts = dark_mask.sum(axis=0)
    v_all = _cluster_line_positions(col_counts, 0.7, h)
    v_centers = v_all[1:-1] if len(v_all) >= 9 else None  # drop outer box border
    if v_centers is None or len(v_centers) != 7:
        return None

    row_counts = dark_mask.sum(axis=1)
    h_all = _cluster_line_positions(row_counts, 0.7, w)
    # h_all[0] = top border, h_all[1] = -10dB line, ..., h_all[14] = 120dB line (13 steps of 10dB)
    if len(h_all) < 15:
        return None
    db_top_y = h_all[1]
    db_bottom_y = h_all[14]

    return v_centers, db_top_y, db_bottom_y


def _nearest_freq(x, v_centers):
    diffs = [abs(x - gx) for gx in v_centers]
    return FREQ_LABELS[diffs.index(min(diffs))]


def _pixel_to_db(y, db_top_y, db_bottom_y):
    frac = (y - db_top_y) / (db_bottom_y - db_top_y)
    return -10 + frac * 130


def _get_color_mask(crop, color):
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    if color == "red":
        m1 = cv2.inRange(hsv, (0, 50, 50), (15, 255, 255))
        m2 = cv2.inRange(hsv, (150, 50, 50), (180, 255, 255))
        return m1 | m2
    else:  # blue
        return cv2.inRange(hsv, (90, 50, 50), (140, 255, 255))


def _extract_circles(mask, v_centers, db_top_y, db_bottom_y, box_w):
    r_min, r_max = int(box_w * 0.017), int(box_w * 0.033)
    min_dist = int(box_w * 0.045)
    circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, dp=1, minDist=min_dist,
                                 param1=50, param2=20, minRadius=r_min, maxRadius=r_max)
    results = {}
    if circles is not None:
        for (cx, cy, r) in circles[0]:
            freq = _nearest_freq(cx, v_centers)
            db = round(_pixel_to_db(cy, db_top_y, db_bottom_y) / 5) * 5
            results[freq] = int(db)
    return results


def _extract_x_marks(mask, v_centers, db_top_y, db_bottom_y):
    size = 45
    template = np.zeros((size, size), dtype=np.uint8)
    cv2.line(template, (5, 5), (size - 5, size - 5), 255, 6)
    cv2.line(template, (5, size - 5), (size - 5, 5), 255, 6)
    result = cv2.matchTemplate(mask, template, cv2.TM_CCOEFF_NORMED)

    loc = np.where(result >= 0.3)
    candidates = [(px + size // 2, py + size // 2, result[py, px]) for px, py in zip(*loc[::-1])]
    candidates.sort(key=lambda c: c[0])

    clusters = []
    for (cx, cy, score) in candidates:
        placed = False
        for cluster in clusters:
            if abs(cluster[-1][0] - cx) < 60:
                cluster.append((cx, cy, score))
                placed = True
                break
        if not placed:
            clusters.append([(cx, cy, score)])

    best = [max(c, key=lambda p: p[2]) for c in clusters]
    results = {}
    for (cx, cy, score) in best:
        freq = _nearest_freq(cx, v_centers)
        db = round(_pixel_to_db(cy, db_top_y, db_bottom_y) / 5) * 5
        results[freq] = int(db)
    return results


def extract_ear_ac(img, box, color, marker_shape) -> dict:
    """
    Extracts AC thresholds for one ear.
    marker_shape: "circle" (right ear) or "x" (left ear)
    Returns dict like {500: 20, 1000: 25, 2000: 25, 4000: 25} (PTA-relevant frequencies only),
    or {} if detection fails.
    """
    x1, y1, x2, y2 = box
    crop = img[y1:y2, x1:x2]

    grid = find_gridlines(crop)
    if grid is None:
        return {}
    v_centers, db_top_y, db_bottom_y = grid

    mask = _get_color_mask(crop, color)
    box_w = x2 - x1

    if marker_shape == "circle":
        results = _extract_circles(mask, v_centers, db_top_y, db_bottom_y, box_w)
    else:
        results = _extract_x_marks(mask, v_centers, db_top_y, db_bottom_y)

    return {f: results[f] for f in [500, 1000, 2000, 4000] if f in results}


def extract_from_report(path: str) -> dict:
    """
    Main entry point. Takes a report file path (image or PDF).
    Returns:
        {
            "right_ac": {500: 20, ...} or {},
            "left_ac": {500: 24, ...} or {},
            "right_bc": {},  # not implemented yet
            "left_bc": {},   # not implemented yet
            "warnings": [...]
        }
    """
    img = load_image(path)
    right_box, left_box = find_chart_boxes(img)

    warnings = []
    right_ac, left_ac = {}, {}

    if right_box is None or left_box is None:
        warnings.append("Could not locate chart grids — all values need manual entry.")
    else:
        right_ac = extract_ear_ac(img, right_box, "red", "circle")
        left_ac = extract_ear_ac(img, left_box, "blue", "x")
        if len(right_ac) < 4:
            warnings.append("Right ear AC extraction incomplete — please verify.")
        if len(left_ac) < 4:
            warnings.append("Left ear AC extraction incomplete — please verify.")

    warnings.append("Bone Conduction (both ears) not yet auto-extracted — please enter manually.")

    return {
        "right_ac": right_ac,
        "left_ac": left_ac,
        "right_bc": {},
        "left_bc": {},
        "warnings": warnings,
    }


if __name__ == "__main__":
    import sys
    path = sys.argv[1]
    result = extract_from_report(path)
    print("Right AC:", result["right_ac"])
    print("Left AC:", result["left_ac"])
    print("Warnings:")
    for w in result["warnings"]:
        print(" -", w)