import sys
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

path = sys.argv[1] if len(sys.argv) > 1 else "sample_report.png"
img = mpimg.imread(path)

fig, ax = plt.subplots(figsize=(10, 12))
ax.imshow(img)
ax.set_title("Click: (1) top-left corner of grid (125Hz,-10dB), (2) bottom-right corner (8000Hz,120dB)")

points = plt.ginput(2, timeout=0)
plt.close()

print("\nCalibration points captured:")
print(f"Top-left (125Hz, -10dB)   -> pixel {points[0]}")
print(f"Bottom-right (8000Hz,120dB) -> pixel {points[1]}")
print("\nUse these two pixel coordinates to build your pixel-to-value conversion formula.")