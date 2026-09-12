"""
One-time setup script: generates the two BC marker template images
needed for Bone Conduction extraction, cropped from a real sample report.

Usage:
    python make_bc_templates.py "path/to/sample_report.pdf"

Produces:
    assets/bc_template_right.png
    assets/bc_template_left.png

These are the actual "<" and ">" arrow shapes cropped from wherever they
happen to appear on this sample — the shape itself is reused for matching
on ALL future reports, regardless of where markers appear on those.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from extract import load_image, find_chart_boxes

path = sys.argv[1]
img = load_image(path)
right_box, left_box = find_chart_boxes(img)

if right_box is None or left_box is None:
    print("Could not find chart boxes on this sample. Try a different report.")
    sys.exit(1)

os.makedirs("assets", exist_ok=True)

import cv2

rx1, ry1, rx2, ry2 = right_box
right_crop = img[ry1:ry2, rx1:rx2]
right_template = right_crop[204:240, 198:247]
cv2.imwrite("assets/bc_template_right.png", right_template)

lx1, ly1, lx2, ly2 = left_box
left_crop = img[ly1:ly2, lx1:lx2]
left_template = left_crop[204:231, 210:242]
cv2.imwrite("assets/bc_template_left.png", left_template)

print("Saved assets/bc_template_right.png and assets/bc_template_left.png")
print("If either looks wrong when you open it, tell me and we'll adjust the crop coordinates.")