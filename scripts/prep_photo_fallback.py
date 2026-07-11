"""
Fallback for prep_photo.py when `rembg`/`onnxruntime` aren't available.
Uses OpenCV's GrabCut (seeded by a Haar face detection) instead of an AI
background remover, then applies the same CLAHE local-contrast + white
composite as the original script.

    python scripts/prep_photo_fallback.py <input.jpg> [output.png]
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.jpg")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

bgr = cv2.imread(INP)
h, w = bgr.shape[:2]

# 1. find the face to seed a person-shaped rectangle for GrabCut
cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
gray0 = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
faces = cascade.detectMultiScale(gray0, scaleFactor=1.08, minNeighbors=5, minSize=(60, 60))

if len(faces) > 0:
    fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
    cx = fx + fw / 2
    # expand from the face box down to shoulders/torso and out to the sides
    rx0 = max(0, int(cx - fw * 1.8))
    rx1 = min(w, int(cx + fw * 1.8))
    ry0 = max(0, int(fy - fh * 0.9))
    ry1 = min(h, int(fy + fh * 5.0))
else:
    rx0, ry0, rx1, ry1 = int(w * 0.12), int(h * 0.03), int(w * 0.88), h

rect = (rx0, ry0, rx1 - rx0, ry1 - ry0)

mask = np.zeros((h, w), np.uint8)
bgdModel = np.zeros((1, 65), np.float64)
fgdModel = np.zeros((1, 65), np.float64)
cv2.grabCut(bgr, mask, rect, bgdModel, fgdModel, 8, cv2.GC_INIT_WITH_RECT)
alpha = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)

# clean up the mask a little
alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
alpha = cv2.morphologyEx(alpha, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

# 2. local-contrast the luminance (CLAHE) -- same as original
gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
clahe = cv2.createCLAHE(clipLimit=2.6, tileGridSize=(8, 8))
gray = clahe.apply(gray)
gray = cv2.convertScaleAbs(gray, alpha=1.05, beta=18)

# 3. paste onto white using the alpha mask (feathered a hair to avoid a halo)
mask_f = (alpha.astype(np.float32) / 255.0)
mask_f = cv2.GaussianBlur(mask_f, (0, 0), 1.5)
out = gray.astype(np.float32) * mask_f + 255.0 * (1.0 - mask_f)
out = np.clip(out, 0, 255).astype(np.uint8)

Image.fromarray(out, mode="L").save(OUT)
print("wrote", OUT, out.shape, "rect=", rect)
