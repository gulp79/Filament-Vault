"""Color engine for Filament Vault.

Provides RGB/Hex/HSV/Lab conversion, delta E color difference calculation,
13-family classification, color similarity discovery, and harmonic color generation.
"""

from __future__ import annotations
import colorsys
import math
from typing import Tuple, List, Dict, Any, Optional

# Supported Color Families as specified in prompt:
# red, orange, yellow, green, cyan, blue, purple, pink, brown, gray, white, black, transparent
COLOR_FAMILIES = [
    "red",
    "orange",
    "yellow",
    "green",
    "cyan",
    "blue",
    "purple",
    "pink",
    "brown",
    "gray",
    "white",
    "black",
    "transparent",
]

# Standard reference hex values for color families in UI
FAMILY_PREVIEW_COLORS = {
    "red": "#E63946",
    "orange": "#F77F00",
    "yellow": "#FCBF49",
    "green": "#00AE42",
    "cyan": "#00B4D8",
    "blue": "#0077B6",
    "purple": "#7209B7",
    "pink": "#F72585",
    "brown": "#7F4F24",
    "gray": "#8A8F98",
    "white": "#F8F9FA",
    "black": "#1A1A1A",
    "transparent": "#A0C4E2",
}


def parse_hex_color(hex_str: Optional[str]) -> Tuple[int, int, int, int]:
    """Parse color hex string like #RRGGBB or #RRGGBBAA into (r, g, b, a).
    
    Defaults to (128, 128, 128, 255) on parse error.
    """
    if not hex_str:
        return (128, 128, 128, 255)
    s = hex_str.strip().lstrip("#")
    try:
        if len(s) == 3:  # RGB
            r = int(s[0] * 2, 16)
            g = int(s[1] * 2, 16)
            b = int(s[2] * 2, 16)
            return (r, g, b, 255)
        elif len(s) == 4:  # RGBA
            r = int(s[0] * 2, 16)
            g = int(s[1] * 2, 16)
            b = int(s[2] * 2, 16)
            a = int(s[3] * 2, 16)
            return (r, g, b, a)
        elif len(s) == 6:  # RRGGBB
            r = int(s[0:2], 16)
            g = int(s[2:4], 16)
            b = int(s[4:6], 16)
            return (r, g, b, 255)
        elif len(s) >= 8:  # RRGGBBAA
            r = int(s[0:2], 16)
            g = int(s[2:4], 16)
            b = int(s[4:6], 16)
            a = int(s[6:8], 16)
            return (r, g, b, a)
    except ValueError:
        pass
    return (128, 128, 128, 255)


def rgba_to_hex(r: int, g: int, b: int, a: int = 255, include_alpha: bool = False) -> str:
    """Format RGB(A) integers to hex string (#RRGGBB or #RRGGBBAA)."""
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    a = max(0, min(255, int(a)))
    if include_alpha:
        return f"#{r:02X}{g:02X}{b:02X}{a:02X}"
    return f"#{r:02X}{g:02X}{b:02X}"


def rgb_to_lab(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """Convert sRGB (0-255) to CIE L*a*b* using D65 standard illuminant."""
    # Convert sRGB to linear RGB
    r_lin = r / 255.0
    g_lin = g / 255.0
    b_lin = b / 255.0

    r_lin = ((r_lin + 0.055) / 1.055) ** 2.4 if r_lin > 0.04045 else r_lin / 12.92
    g_lin = ((g_lin + 0.055) / 1.055) ** 2.4 if g_lin > 0.04045 else g_lin / 12.92
    b_lin = ((b_lin + 0.055) / 1.055) ** 2.4 if b_lin > 0.04045 else b_lin / 12.92

    # Linear RGB to XYZ (D65)
    x = r_lin * 0.4124564 + g_lin * 0.3575761 + b_lin * 0.1804375
    y = r_lin * 0.2126729 + g_lin * 0.7151522 + b_lin * 0.0721750
    z = r_lin * 0.0193339 + g_lin * 0.1191920 + b_lin * 0.9503041

    # D65 reference white points
    xn = 0.95047
    yn = 1.00000
    zn = 1.08883

    xr = x / xn
    yr = y / yn
    zr = z / zn

    def f(t: float) -> float:
        return t ** (1.0 / 3.0) if t > 0.008856 else (7.787 * t) + (16.0 / 116.0)

    fx = f(xr)
    fy = f(yr)
    fz = f(zr)

    l = max(0.0, min(100.0, (116.0 * fy) - 16.0))
    a_star = 500.0 * (fx - fy)
    b_star = 200.0 * (fy - fz)

    return (round(l, 2), round(a_star, 2), round(b_star, 2))


def delta_e_ciede2000(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]) -> float:
    """Calculate CIEDE2000 color difference between two Lab colors.
    
    Value < 1.0: Not perceptible by human eyes
    Value 1.0 - 2.0: Perceptible through close observation
    Value 2.0 - 10.0: Perceptible at a glance
    Value 11.0 - 49.0: Colors are more similar than opposite
    Value 100+: Colors are exact opposite
    """
    l1, a1, b1 = lab1
    l2, a2, b2 = lab2

    c1 = math.sqrt(a1 * a1 + b1 * b1)
    c2 = math.sqrt(a2 * a2 + b2 * b2)
    c_bar = (c1 + c2) / 2.0

    g = 0.5 * (1.0 - math.sqrt((c_bar ** 7) / ((c_bar ** 7) + (25.0 ** 7))))

    a1_prime = (1.0 + g) * a1
    a2_prime = (1.0 + g) * a2

    c1_prime = math.sqrt(a1_prime * a1_prime + b1 * b1)
    c2_prime = math.sqrt(a2_prime * a2_prime + b2 * b2)

    def compute_h_prime(a_p: float, b_p: float) -> float:
        if a_p == 0 and b_p == 0:
            return 0.0
        deg = math.degrees(math.atan2(b_p, a_p))
        return deg if deg >= 0 else deg + 360.0

    h1_prime = compute_h_prime(a1_prime, b1)
    h2_prime = compute_h_prime(a2_prime, b2)

    delta_l_prime = l2 - l1
    delta_c_prime = c2_prime - c1_prime

    if c1_prime * c2_prime == 0:
        delta_h_prime = 0.0
    elif abs(h2_prime - h1_prime) <= 180.0:
        delta_h_prime = h2_prime - h1_prime
    elif h2_prime - h1_prime > 180.0:
        delta_h_prime = h2_prime - h1_prime - 360.0
    else:
        delta_h_prime = h2_prime - h1_prime + 360.0

    delta_big_h_prime = 2.0 * math.sqrt(c1_prime * c2_prime) * math.sin(math.radians(delta_h_prime / 2.0))

    l_bar_prime = (l1 + l2) / 2.0
    c_bar_prime = (c1_prime + c2_prime) / 2.0

    if c1_prime * c2_prime == 0:
        h_bar_prime = h1_prime + h2_prime
    elif abs(h1_prime - h2_prime) <= 180.0:
        h_bar_prime = (h1_prime + h2_prime) / 2.0
    elif h1_prime + h2_prime < 360.0:
        h_bar_prime = (h1_prime + h2_prime + 360.0) / 2.0
    else:
        h_bar_prime = (h1_prime + h2_prime - 360.0) / 2.0

    t = (
        1.0
        - 0.17 * math.cos(math.radians(h_bar_prime - 30.0))
        + 0.24 * math.cos(math.radians(2.0 * h_bar_prime))
        + 0.32 * math.cos(math.radians(3.0 * h_bar_prime + 6.0))
        - 0.20 * math.cos(math.radians(4.0 * h_bar_prime - 63.0))
    )

    delta_theta = 30.0 * math.exp(-(((h_bar_prime - 275.0) / 25.0) ** 2))
    r_c = 2.0 * math.sqrt((c_bar_prime ** 7) / ((c_bar_prime ** 7) + (25.0 ** 7)))
    s_l = 1.0 + ((0.015 * ((l_bar_prime - 50.0) ** 2)) / math.sqrt(20.0 + ((l_bar_prime - 50.0) ** 2)))
    s_c = 1.0 + 0.045 * c_bar_prime
    s_h = 1.0 + 0.015 * c_bar_prime * t
    r_t = -math.sin(math.radians(2.0 * delta_theta)) * r_c

    term_l = delta_l_prime / (s_l * 1.0)
    term_c = delta_c_prime / (s_c * 1.0)
    term_h = delta_big_h_prime / (s_h * 1.0)

    delta_e = math.sqrt(
        (term_l ** 2) + (term_c ** 2) + (term_h ** 2) + (r_t * term_c * term_h)
    )
    return round(delta_e, 2)


def classify_color_family(hex_str: Optional[str], series_or_name: str = "") -> str:
    """Classify any hex color into one of 13 official families:
    red, orange, yellow, green, cyan, blue, purple, pink, brown, gray, white, black, transparent.
    """
    # Check if series or name indicates translucent/transparent
    name_lower = series_or_name.lower()
    if "translucent" in name_lower or "transparent" in name_lower or "clear" in name_lower:
        # Check alpha if provided
        r, g, b, a = parse_hex_color(hex_str)
        if a < 200 or "translucent" in name_lower or "clear" in name_lower:
            return "transparent"

    r, g, b, a = parse_hex_color(hex_str)
    if a < 120:
        return "transparent"

    # Normalize RGB to 0..1 for HSV
    r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
    h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
    hue_deg = h * 360.0

    # Luminance and saturation rules for achromatic shades
    # Black: very low value
    if v < 0.18:
        return "black"

    # White: very high value and very low saturation
    if v > 0.88 and s < 0.12:
        return "white"

    # Gray: low saturation
    if s < 0.15:
        if v < 0.35:
            return "black"
        elif v > 0.80:
            return "white"
        return "gray"

    # Brown: warm hue (orange/red-orange/yellow-orange) with low-to-medium brightness and medium saturation
    if 10.0 <= hue_deg <= 45.0 and s >= 0.30 and v < 0.55:
        return "brown"

    # Pink: light reds/purples with high brightness and low-moderate saturation or magenta hue
    if (320.0 <= hue_deg <= 355.0 or hue_deg < 10.0) and v >= 0.70 and s <= 0.65:
        return "pink"

    # Chromatic hue segments
    if (hue_deg >= 345.0) or (hue_deg < 15.0):
        return "red"
    elif 15.0 <= hue_deg < 45.0:
        return "orange"
    elif 45.0 <= hue_deg < 70.0:
        return "yellow"
    elif 70.0 <= hue_deg < 165.0:
        return "green"
    elif 165.0 <= hue_deg < 200.0:
        return "cyan"
    elif 200.0 <= hue_deg < 260.0:
        return "blue"
    elif 260.0 <= hue_deg < 315.0:
        return "purple"
    elif 315.0 <= hue_deg < 345.0:
        return "pink"

    return "gray"


def get_contrast_text_color(hex_str: Optional[str]) -> str:
    """Return '#FFFFFF' or '#000000' for best contrast against the given background hex."""
    r, g, b, _ = parse_hex_color(hex_str)
    # Relative luminance
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return "#000000" if lum > 140 else "#FFFFFF"


def find_similar_spools(
    target_hex: str,
    spools: List[Dict[str, Any]],
    max_delta_e: float = 15.0,
    limit: int = 10
) -> List[Tuple[Dict[str, Any], float]]:
    """Rank spools by delta-E color difference to target_hex."""
    tr, tg, tb, _ = parse_hex_color(target_hex)
    target_lab = rgb_to_lab(tr, tg, tb)

    results = []
    for spool in spools:
        s_hex = spool.get("color_code", "")
        sr, sg, sb, _ = parse_hex_color(s_hex)
        s_lab = rgb_to_lab(sr, sg, sb)
        de = delta_e_ciede2000(target_lab, s_lab)
        if de <= max_delta_e:
            results.append((spool, de))

    results.sort(key=lambda x: x[1])
    return results[:limit]
