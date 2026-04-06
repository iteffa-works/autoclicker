"""Design tokens: 8px grid, slate + indigo palette (dark/light)."""

from __future__ import annotations

# Spacing (px) — 8px grid
S8 = 8
S12 = 12
S16 = 16
S24 = 24
S32 = 32

# Main window (fixed, no resize)
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 900

# Outer padding головної області контенту
CONTENT_PADDING = 16

# Form rows: label column + capped control width (avoid overstretched inputs)
FORM_LABEL_MIN_W = 140
FORM_FIELD_MAX_W = 280
FORM_COMBO_MAX_W = 360
# Вузькі колонки на вкладці «Автоклікер» (сітка 2–3 колонки)
AC_COL_FIELD_MAX_W = 220
AC_COL_COMBO_MAX_W = 260
# Однакова ширина колонки підписів у сітках автокліку (праве вирівнювання)
AC_GRID_LABEL_W = 120
# Підписи рядків биндів (одна колонка)
BINDS_LABEL_MIN_W = 190
# Кнопки стовпчика «Макроси» — однакова ширина
MACRO_SIDE_BTN_MIN_W = 128

# Вкладка «Тест клавіатури» (клавіші трохи світліші за plate — «преміум» панель)
KB_TEST_KEY_UNIT_W = 54
KB_TEST_KEY_H = 50
KB_TEST_GRID_GAP = 6
KB_TEST_MAIN_NUM_GAP = 16  # відстань main | numpad
KB_TEST_ACCENT = "#3B82F6"
KB_TEST_ACCENT_SOFT = "rgba(59,130,246,0.35)"
KB_TEST_KEY_FACE = "#283548"
KB_TEST_KEY_FACE_HOVER = "#34455a"
KB_TEST_KEY_FACE_ACTIVE = "#1e2d3f"
KB_TEST_KEY_BORDER = "#3d4d64"
KB_TEST_PLATE = "#151d2e"
KB_TEST_PLATE_OUTER = "#0F172A"

L_KB_TEST_KEY_FACE = "#F1F5F9"
L_KB_TEST_KEY_FACE_HOVER = "#E8EEF4"
L_KB_TEST_KEY_FACE_ACTIVE = "#DCE4EE"
L_KB_TEST_KEY_BORDER = "#CBD5E1"
L_KB_TEST_PLATE = "#FFFFFF"
L_KB_TEST_PLATE_OUTER = "#F1F5F9"
L_KB_TEST_ACCENT = "#2563EB"
L_KB_TEST_ACCENT_SOFT = "rgba(37,99,235,0.25)"

# --- Dark (primary) ---
D_BG_APP = "#0F172A"
D_BG_ELEVATED = "#111827"
D_BG_SURFACE = "#1E293B"
D_BG_SURFACE2 = "#1F2937"
D_BORDER_SUBTLE = "#334155"
D_BORDER_FOCUS = "#6366F1"
D_TEXT_PRIMARY = "#E5E7EB"
D_TEXT_SECONDARY = "#9CA3AF"
D_TEXT_DISABLED = "#6B7280"
D_ACCENT = "#6366F1"
D_ACCENT_HOVER = "#818CF8"
D_ACCENT_ACTIVE = "#4F46E5"
D_STATE_ERROR = "#EF4444"
D_STATE_SUCCESS = "#22C55E"
D_STATE_WARNING = "#F59E0B"
D_SELECTION_BG = "#312E81"
D_SELECTION_FG = "#F8FAFC"

# --- Light (paired with dark structure) ---
L_BG_APP = "#F1F5F9"
L_BG_SURFACE = "#FFFFFF"
L_BG_SURFACE2 = "#F8FAFC"
L_BORDER_SUBTLE = "#E2E8F0"
L_BORDER_STRONG = "#CBD5E1"
L_BORDER_FOCUS = "#6366F1"
L_TEXT_PRIMARY = "#111827"
L_TEXT_SECONDARY = "#64748B"
L_TEXT_DISABLED = "#94A3B8"
L_ACCENT = "#6366F1"
L_ACCENT_HOVER = "#4F46E5"
L_ACCENT_ACTIVE = "#4338CA"
L_SELECTION_BG = "#E0E7FF"
L_SELECTION_FG = "#1E1B4B"
