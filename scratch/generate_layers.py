import os
import math
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

# Paths
img_path = 'd:/paytm hack/agentx-ai-teammates/frontend/public/gothic_gate.jpg'
output_dir = 'd:/paytm hack/agentx-ai-teammates/frontend/public'

img = Image.open(img_path).convert('RGBA')
w, h = img.size # 1024, 576

# 1. Create BACKGROUND LAYER (gothic_bg.jpg)
# We fill the central gate opening (between stone pillars X: 245 to 779, Y: 25 to 500)
# with a glowing crimson portal (gradient + red haze) so NO static gate exists behind!

bg = img.copy()
draw = ImageDraw.Draw(bg)

# Gate doorway bounding box
gate_left = 245
gate_right = 779
gate_top = 25
gate_bottom = 495
cx = (gate_left + gate_right) // 2
cy = (gate_top + gate_bottom) // 2

# Create glowing portal canvas
portal = Image.new('RGBA', (w, h), (0, 0, 0, 0))
p_draw = ImageDraw.Draw(portal)

# Radial crimson glow inside doorway
for r in range(350, 0, -5):
    alpha = int(255 * (1.0 - (r / 350.0) ** 1.5))
    # Crimson red gradient: center bright red (#ef4444) -> dark maroon (#450a0a) -> black
    if r < 100:
        color = (239, 68, 68, min(255, alpha))
    elif r < 220:
        color = (185, 28, 28, min(255, alpha))
    elif r < 300:
        color = (127, 29, 29, min(255, alpha))
    else:
        color = (30, 5, 10, min(255, alpha))
    
    p_draw.ellipse([cx - r*1.2, cy - r*0.9, cx + r*1.2, cy + r*0.9], fill=color)

# Blur the portal glow for smooth light dispersion
portal = portal.filter(ImageFilter.GaussianBlur(15))

# Create arch mask for background hole
mask = Image.new('L', (w, h), 0)
m_draw = ImageDraw.Draw(mask)

# Arch shape in the center
arch_points = []
# Top arch curve
for angle_deg in range(180, 361, 5):
    rad = math.radians(angle_deg)
    rx = (gate_right - gate_left) / 2.0
    ry = (cy - gate_top)
    x = cx + rx * math.cos(rad)
    y = gate_top + ry * (1.0 + math.sin(rad)) # smooth arch top
    arch_points.append((x, y))

# Rectangular sides down to bottom
arch_points.append((gate_right, gate_bottom))
arch_points.append((gate_left, gate_bottom))

# Draw arch on mask with feathering
m_draw.polygon(arch_points, fill=255)
mask_blurred = mask.filter(ImageFilter.GaussianBlur(8))

# Composite portal glow onto background inside arch area
bg.paste(portal, (0, 0), mask_blurred)
bg_rgb = bg.convert('RGB')
bg_rgb.save(os.path.join(output_dir, 'gothic_bg.jpg'), quality=95)
print("Saved gothic_bg.jpg")

# 2. Create LEFT GATE (gothic_left_gate.png)
# Left door spans from X: 245 to 512, Y: 20 to 500
left_gate = Image.new('RGBA', (w, h), (0, 0, 0, 0))

# Mask for Left Gate
left_mask = Image.new('L', (w, h), 0)
l_draw = ImageDraw.Draw(left_mask)

left_points = [
    (gate_left, gate_bottom),
    (gate_left, gate_top + 40),
    (cx, gate_top),
    (cx, gate_bottom)
]
l_draw.polygon(left_points, fill=255)
left_mask_feathered = left_mask.filter(ImageFilter.GaussianBlur(2))

left_gate.paste(img, (0, 0), left_mask_feathered)
left_gate.save(os.path.join(output_dir, 'gothic_left_gate.png'))
print("Saved gothic_left_gate.png")

# 3. Create RIGHT GATE (gothic_right_gate.png)
# Right door spans from X: 512 to 779, Y: 20 to 500
right_gate = Image.new('RGBA', (w, h), (0, 0, 0, 0))

# Mask for Right Gate
right_mask = Image.new('L', (w, h), 0)
r_draw = ImageDraw.Draw(right_mask)

right_points = [
    (cx, gate_bottom),
    (cx, gate_top),
    (gate_right, gate_top + 40),
    (gate_right, gate_bottom)
]
r_draw.polygon(right_points, fill=255)
right_mask_feathered = right_mask.filter(ImageFilter.GaussianBlur(2))

right_gate.paste(img, (0, 0), right_mask_feathered)
right_gate.save(os.path.join(output_dir, 'gothic_right_gate.png'))
print("Saved gothic_right_gate.png")
