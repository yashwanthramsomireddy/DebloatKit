"""Generate installer bitmap assets for DebloatKit Inno Setup"""
import struct, zlib, os

def write_bmp(path, width, height, pixels_rgb):
    """Write a 24-bit BMP file."""
    row_size = (width * 3 + 3) & ~3  # 4-byte aligned
    pixel_data = bytearray()
    for y in range(height - 1, -1, -1):  # BMP is bottom-up
        row = bytearray()
        for x in range(width):
            r, g, b = pixels_rgb[y * width + x]
            row += bytes([b, g, r])  # BMP is BGR
        row += bytes(row_size - len(row))  # padding
        pixel_data += row

    file_size = 54 + len(pixel_data)
    header = struct.pack('<2sIHHI', b'BM', file_size, 0, 0, 54)
    dib = struct.pack('<IiiHHIIiiII', 40, width, height, 1, 24, 0,
                      len(pixel_data), 2835, 2835, 0, 0)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(header + dib + pixel_data)
    print(f"  Created: {path} ({width}x{height})")

# Colors
BG       = (10, 10, 10)       # #0a0a0a
ACCENT   = (0, 230, 118)      # #00e676
DK_GREEN = (0, 179, 89)       # #00b359
WHITE    = (240, 240, 240)
GRAY     = (40, 40, 40)

# ── Side image: 164x314 (left panel of installer wizard) ─────────────────────
W, H = 164, 314
pixels = []
for y in range(H):
    for x in range(W):
        # Dark gradient background
        g = int(10 + (y / H) * 20)
        px = (g, g, g)

        # Accent stripe on right edge
        if x >= W - 3:
            px = ACCENT

        # Hexagon logo area (centered, top third)
        cx, cy = W // 2, H // 4
        dx, dy = x - cx, y - cy
        # Simple hex approximation using diamond
        if abs(dx) + abs(dy * 0.6) < 28:
            if abs(dx) + abs(dy * 0.6) < 24:
                px = ACCENT
            else:
                px = DK_GREEN

        # "DK" text area — simple pixel blocks
        # D
        if 62 <= y <= 82:
            ty = y - 62
            if x == 64 or (x == 74 and 2 <= ty <= 18) or (x in (65,66,67,68,69,70,71,72,73) and ty in (0,1,19,20)):
                px = WHITE
        # K
        if 62 <= y <= 82:
            ty = y - 62
            if x == 80 or (x in (81,82,83,84,85,86,87,88,89) and ty == 10) or (81 <= x <= 90 and abs(ty - 10) == x - 80):
                px = WHITE

        # Bottom text strip
        if y >= H - 30:
            px = (15, 15, 15)
        if H - 20 <= y <= H - 14 and 20 <= x <= W - 20:
            px = ACCENT if (x - 20) % 4 < 2 else DK_GREEN

        pixels.append(px)

write_bmp("assets/installer_side_164x314.bmp", W, H, pixels)

# ── Small image: 55x58 (top-right of wizard pages) ───────────────────────────
W2, H2 = 55, 58
pixels2 = []
for y in range(H2):
    for x in range(W2):
        g = int(10 + (y / H2) * 15)
        px = (g, g, g)

        # Mini hex
        cx2, cy2 = W2 // 2, H2 // 2
        dx2, dy2 = x - cx2, y - cy2
        if abs(dx2) + abs(dy2 * 0.6) < 18:
            if abs(dx2) + abs(dy2 * 0.6) < 14:
                px = ACCENT
            else:
                px = DK_GREEN

        pixels2.append(px)

write_bmp("assets/installer_icon_55x58.bmp", W2, H2, pixels2)
print("Assets generated successfully.")
