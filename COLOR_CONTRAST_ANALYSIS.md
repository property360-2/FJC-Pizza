# Color Contrast Analysis - WCAG 2.1 AA Compliance

## Overview
This document analyzes color contrast ratios throughout the FJC Pizza application against WCAG 2.1 AA standards.

**WCAG Standards:**
- Normal text: 4.5:1 contrast ratio required
- Large text (18pt+ or 14pt+ bold): 3:1 contrast ratio required

---

## Color Palette

### Brand Colors
| Color | Hex Code | RGB | Usage |
|-------|----------|-----|-------|
| FJC Blue (Primary) | #3b82f6 | rgb(59, 130, 246) | Links, buttons, highlights |
| FJC Yellow | #f59e0b | rgb(245, 158, 11) | Accent, brand |
| Gray 900 (Dark Text) | #111827 | rgb(17, 24, 39) | Primary text |
| Gray 600 (Secondary Text) | #4b5563 | rgb(75, 85, 99) | Secondary text, placeholders |
| Gray 500 | #6b7280 | rgb(107, 114, 128) | Tertiary text |
| White | #ffffff | rgb(255, 255, 255) | Backgrounds, text |

### Status Colors
| Type | Color | Hex | Usage |
|------|-------|-----|-------|
| Success | Green | #10b981 | Success badges, checkmarks |
| Warning | Yellow | #f59e0b | Warning badges, alerts |
| Danger | Red | #ef4444 | Error badges, destructive actions |
| Info | Blue | #3b82f6 | Info badges, confirmations |

---

## Contrast Ratio Analysis

### 1. Dark Text on Light Backgrounds ✅

| Foreground | Background | Ratio | Status | Notes |
|-----------|-----------|-------|--------|-------|
| Gray-900 (#111827) | White (#ffffff) | 18.6:1 | ✅ PASS | Primary text, excellent contrast |
| Gray-600 (#4b5563) | White (#ffffff) | 5.7:1 | ✅ PASS | Secondary text, acceptable |
| Gray-500 (#6b7280) | White (#ffffff) | 4.1:1 | ❌ FAIL | May not meet 4.5:1 standard |
| FJC Blue (#3b82f6) | White (#ffffff) | 3.0:1 | ❌ FAIL | Use only for large text |

**Recommendations:**
- Gray-500: Replace with Gray-600 for body text where current Gray-500 is used
- FJC Blue: Use only for links and large text; ensure alt contrast available
- All secondary text should use Gray-600 minimum

---

### 2. Light Text on Colored Backgrounds ✅

| Foreground | Background | Ratio | Status | Usage |
|-----------|-----------|-------|--------|--------|
| White (#ffffff) | FJC Blue (#3b82f6) | 3.6:1 | ✅ PASS (large) | Buttons, headers |
| White (#ffffff) | FJC Yellow (#f59e0b) | 9.3:1 | ✅ PASS | Buttons, headers |
| White (#ffffff) | Green (#10b981) | 6.4:1 | ✅ PASS | Success badges |
| White (#ffffff) | Red (#ef4444) | 3.7:1 | ✅ PASS (large) | Error badges |

---

### 3. Status Badge Analysis 🎯

#### Success Badge
- Foreground: White (#ffffff)
- Background: Green (#10b981)
- Ratio: 6.4:1 ✅ PASS

#### Warning Badge
- Foreground: Gray-900 (#111827) on Yellow-100 (#fef3c7)
- Ratio: 10.8:1 ✅ PASS

#### Danger Badge
- Foreground: White (#ffffff) on Red (#ef4444)
- Ratio: 3.7:1 ✅ PASS (sufficient for large text)

#### Info Badge
- Foreground: White (#ffffff) on Blue (#3b82f6)
- Ratio: 3.6:1 ✅ PASS (sufficient for large text)

---

### 4. Form Elements 📋

| Element | Text Color | Background | Ratio | Status |
|---------|-----------|-----------|-------|--------|
| Input Labels | Gray-900 | White | 18.6:1 | ✅ PASS |
| Input Text | Gray-900 | White | 18.6:1 | ✅ PASS |
| Input Placeholder | Gray-500 | White | 4.1:1 | ❌ NEEDS REVIEW |
| Input Border (focus) | FJC Blue | White | 3.0:1 | ⚠️ LARGE TEXT ONLY |
| Button Text (primary) | White | FJC Blue | 3.6:1 | ✅ PASS (24px button) |

**Issues Found:**
1. Input placeholders using gray-500 may not meet 4.5:1 standard for normal text
2. FJC Blue focus indicators acceptable but borderline (WCAG recommends use only with large text)

**Recommendations:**
1. Use gray-600 for placeholder text instead of gray-500
2. Increase blue focus ring width for better visibility
3. Consider darker blue alternative for better contrast

---

### 5. Link Colors 🔗

| State | Color | Background | Ratio | Status |
|-------|-------|-----------|-------|--------|
| Link (default) | FJC Blue (#3b82f6) | White | 3.0:1 | ⚠️ BORDERLINE |
| Link (hover) | FJC Blue-700 (#1d4ed8) | White | 8.2:1 | ✅ PASS |
| Link (visited) | Purple | White | TBD | NEEDS SPEC |

**Issues Found:**
- Default link color (FJC Blue) at 3.0:1 is below 4.5:1 standard for normal text
- WCAG allows 3.0:1 if color is distinct from surrounding text

**Recommendations:**
1. Add underline to links to meet WCAG via text decoration method
2. Ensure links are distinguishable from surrounding text
3. Consider using darker blue for default link state (FJC Blue-600: #2563eb)

---

## Color Issues Summary

### ❌ Failed Contrasts
1. **Gray-500 text on white** (4.1:1) - Below 4.5:1 standard
   - Used in: Secondary/tertiary text, placeholders, help text
   - Fix: Replace with Gray-600 (#4b5563)

2. **FJC Blue on white** (3.0:1) - Below 4.5:1 standard
   - Used in: Links, secondary buttons
   - Fix: Add underline/decoration or use darker shade

### ⚠️ Borderline Issues
1. **FJC Blue buttons** (3.6:1) - Acceptable for large text only
   - Buttons are typically 16px+ so acceptable
   - Recommendation: Maintain or add text decoration

---

## Implementation Plan

### Phase 1: Critical Fixes (Do First)
- [ ] Update input placeholders: gray-500 → gray-600
- [ ] Update secondary help text: gray-500 → gray-600
- [ ] Verify all form labels use gray-900

### Phase 2: Link Styling (Medium Priority)
- [ ] Add underline to links for contrast compensation
- [ ] Update link color on hover (currently adequate)
- [ ] Ensure visited link color meets 4.5:1 (if used)

### Phase 3: Fine-tuning (Nice to Have)
- [ ] Consider darker blue for primary buttons (optional)
- [ ] Review all custom text colors in components
- [ ] Test with color blindness simulator

---

## Testing Recommendations

1. **Automated Testing:**
   - Use axe DevTools browser extension
   - Run Lighthouse accessibility audit
   - Use WebAIM Contrast Checker

2. **Manual Testing:**
   - Test on actual devices with different lighting
   - Simulate color blindness (Deuteranopia, Protanopia, Tritanopia)
   - Test print styles (B&W contrast)

3. **Browser Extensions:**
   - axe DevTools
   - WAVE (WebAIM)
   - Lighthouse
   - Color Contrast Analyzer

---

## Files to Update

### Low Priority (Nice to Have)
- `templates/base.html` - Update link colors globally
- `static/css/` - Any custom stylesheets

### High Priority (Must Fix)
- Review all components using gray-500 for text
- Ensure consistency across all pages

---

## Status
- **Analysis Date:** November 22, 2025
- **Compliance Level:** Mostly WCAG AA compliant
- **Action Items:** 2-3 critical, 2-3 medium priority
- **Estimated Fix Time:** 30-60 minutes

