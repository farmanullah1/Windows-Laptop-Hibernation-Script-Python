"""
Generates a professional multi-resolution Windows icon (.ico) for Hibernate.
Contains sizes: 256x256, 128x128, 64x64, 48x48, 32x32, 16x16.
"""

from pathlib import Path
from PIL import Image, ImageDraw


def draw_hibernate_icon(size: int = 256) -> Image.Image:
    """
    Renders a high-resolution hibernate/power icon with supersampling (anti-aliasing).
    """
    scale = 4  # Render at 4x resolution for smooth antialiasing
    canvas_size = size * scale
    image = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Padding
    pad = int(canvas_size * 0.08)
    bbox = [pad, pad, canvas_size - pad, canvas_size - pad]

    # Background circle with deep midnight blue / obsidian gradient look
    # Main outer circle
    draw.ellipse(bbox, fill=(15, 23, 42, 255))  # Tailwind slate-900

    # Subtle glowing inner rim
    rim_pad = pad + int(canvas_size * 0.02)
    rim_bbox = [rim_pad, rim_pad, canvas_size - rim_pad, canvas_size - rim_pad]
    draw.ellipse(rim_bbox, outline=(56, 189, 248, 90), width=int(canvas_size * 0.015))  # Sky glow

    # Center coordinates
    cx = canvas_size / 2
    cy = canvas_size / 2

    # Power symbol geometry
    # Arc radius and center
    power_r = int(canvas_size * 0.26)
    power_bbox = [cx - power_r, cy - power_r + int(canvas_size * 0.03),
                  cx + power_r, cy + power_r + int(canvas_size * 0.03)]
    stroke_w = int(canvas_size * 0.055)

    # Arc (open at top: from 300 deg to 240 deg, i.e., start at -60 and end at 240)
    # PIL arc angles: 0 is 3 o'clock, 90 is 6 o'clock, etc.
    # Open at top means gap between ~220 and 320 degrees
    # So arc runs from -50 degrees (310) through 90 (bottom) to 230 degrees
    draw.arc(power_bbox, start=-55, end=235, fill=(56, 189, 248, 255), width=stroke_w)

    # Vertical bar at top of power symbol
    bar_w = stroke_w
    bar_top = int(cy - power_r * 1.05 + canvas_size * 0.03)
    bar_bottom = int(cy - power_r * 0.05 + canvas_size * 0.03)
    bar_x0 = int(cx - bar_w / 2)
    bar_x1 = int(cx + bar_w / 2)

    # Draw rounded vertical bar
    draw.rounded_rectangle([bar_x0, bar_top, bar_x1, bar_bottom],
                           radius=int(bar_w / 2),
                           fill=(56, 189, 248, 255))

    # Add a sleek crescent moon accent (symbolizing sleep / hibernation) inside top-right
    moon_cx = int(cx + power_r * 0.85)
    moon_cy = int(cy - power_r * 0.75)
    moon_r = int(canvas_size * 0.09)

    # Outer moon circle
    moon_bbox = [moon_cx - moon_r, moon_cy - moon_r, moon_cx + moon_r, moon_cy + moon_r]
    # Draw moon in soft amber/cyan
    temp_moon = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_moon)
    temp_draw.ellipse(moon_bbox, fill=(251, 191, 36, 240))  # Amber-400

    # Cutout circle to create crescent
    cut_offset_x = int(moon_r * 0.55)
    cut_offset_y = -int(moon_r * 0.25)
    cut_bbox = [moon_cx - moon_r + cut_offset_x, moon_cy - moon_r + cut_offset_y,
                moon_cx + moon_r + cut_offset_x, moon_cy + moon_r + cut_offset_y]
    temp_draw.ellipse(cut_bbox, fill=(0, 0, 0, 0))

    # Composite moon
    image = Image.alpha_composite(image, temp_moon)

    # Downsample with high-quality Lanczos filter
    final_img = image.resize((size, size), Image.Resampling.LANCZOS)
    return final_img


def create_ico_file(output_path: Path) -> Path:
    """Creates a multi-resolution .ico file."""
    sizes = [256, 128, 64, 48, 32, 16]
    images = [draw_hibernate_icon(s) for s in sizes]

    # Save as .ico containing all sizes
    output_path = Path(output_path)
    images[0].save(
        output_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    return output_path


if __name__ == "__main__":
    out = Path(__file__).parent / "hibernate.ico"
    create_ico_file(out)
    print(f"Generated icon: {out}")
