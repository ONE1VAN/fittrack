
BG_DEEP      = (0.039, 0.055, 0.153, 1)
BG_MID       = (0.102, 0.122, 0.227, 1)
BG_SURFACE   = (0.071, 0.090, 0.180, 1)

NEON_CYAN    = (0.000, 0.941, 1.000, 1)
NEON_MAGENTA = (1.000, 0.000, 0.431, 1)
ENERGY_GREEN = (0.224, 1.000, 0.078, 1)
WARN_AMBER   = (1.000, 0.722, 0.000, 1)
DANGER_RED   = (1.000, 0.231, 0.376, 1)

TEXT_PRIMARY   = (0.949, 0.961, 1.000, 1)
TEXT_SECONDARY = (0.620, 0.659, 0.808, 1)
TEXT_MUTED     = (0.420, 0.459, 0.608, 1)

GLASS_TINT     = (1, 1, 1, 0.06)
GLASS_BORDER   = (1, 1, 1, 0.12)
GLOW_CYAN      = (0.000, 0.941, 1.000, 0.45)
GLOW_MAGENTA   = (1.000, 0.000, 0.431, 0.35)

FONT_DISPLAY = "Orbitron"
FONT_BODY    = "Roboto"

SIZE_DISPLAY = "32sp"
SIZE_H1      = "24sp"
SIZE_H2      = "20sp"
SIZE_BODY    = "15sp"
SIZE_CAPTION = "12sp"

RADIUS_CARD   = 18
RADIUS_BUTTON = 24
RADIUS_CHIP   = 14

PADDING = 16
GAP     = 12

STATUS_COLORS = {
    "active":    ENERGY_GREEN,
    "frozen":    NEON_CYAN,
    "expired":   DANGER_RED,
    "cancelled": TEXT_MUTED,
    "booked":    NEON_CYAN,
    "attended":  ENERGY_GREEN,
    "no_show":   DANGER_RED,
    "ok":        ENERGY_GREEN,
    "fault":     DANGER_RED,
    "maintenance": WARN_AMBER,
}

STATUS_LABELS_UA = {
    "active":      "Активний",
    "frozen":      "Заморожено",
    "expired":     "Прострочений",
    "cancelled":   "Скасовано",
    "booked":      "Заброньовано",
    "attended":    "Відвідано",
    "no_show":     "Не з'явився",
    "ok":          "Робочий",
    "fault":       "Несправний",
    "maintenance": "На ремонті",
}

DUR_FAST   = 0.18
DUR_NORMAL = 0.32
DUR_SLOW   = 0.55
EASE       = "out_quad"
EASE_BACK  = "out_back"
