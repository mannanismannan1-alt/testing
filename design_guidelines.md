# Design Guidelines: Flask "Hi" Web Application

## Design Approach

**Selected System:** Material Design principles with modern minimalist execution  
**Rationale:** For this utility-focused demonstration, we'll prioritize clean typography, purposeful spacing, and a polished single-page experience that showcases modern web development practices.

**Key Principles:**
- Extreme clarity and focus
- Professional polish despite simplicity
- Generous whitespace as a design element
- Typography as the primary visual tool

---

## Core Design Elements

### A. Typography

**Primary Font:** Inter or SF Pro Display (via Google Fonts CDN)

**Hierarchy:**
- Main "hi" display: text-8xl to text-9xl, font-bold (approximately 96-128px)
- Subtitle/tagline: text-xl, font-light (20px) - add subtle context like "A Flask Application"
- Footer text: text-sm, font-normal (14px)

**Treatment:** Lowercase preferred for friendly, approachable feel

### B. Layout System

**Spacing Primitives:** Tailwind units of 4, 8, and 16 (p-4, p-8, p-16, etc.)

**Structure:**
- Full viewport height container (min-h-screen)
- Centered content using flexbox (flex items-center justify-center)
- Consistent padding: p-8 mobile, p-16 desktop
- Footer pinned to bottom with py-8 padding

**Responsive Behavior:**
- Mobile: Single column, text-6xl for main message
- Desktop: text-9xl for maximum impact

### C. Component Library

**Page Structure:**
```
- Centered content area (max-w-4xl)
  - Main message "hi" (display text)
  - Subtitle "A Flask Application" (supporting text)
  - Decorative element (animated wave emoji or simple icon)
- Footer bar
  - "Built with Flask" text
  - Python + Flask version badge
```

**Navigation:** None required

**Forms:** None required

**Data Displays:**
- Version badge component (inline-flex, rounded-full, px-4 py-2)
- Tech stack indicator (text with icon)

**Icons:** 
- Use Heroicons (CDN) for any supplementary icons
- Python logo via CDN (optional brand recognition)

### D. Interactions & Animations

**Minimal Motion:**
- Subtle fade-in on page load (0.6s duration)
- Optional gentle pulse on the "hi" text (2s interval, very subtle)

**No Hover States:** Static presentation focused on content

---

## Specific Implementation Details

**Container:**
- Full viewport with centered flex container
- Background treatment: solid surface, no gradients

**Main Message:**
- Letter spacing: tracking-tight for display size
- Line height: leading-none
- Text alignment: center

**Supporting Elements:**
- Badge showing "Python 3.x • Flask 2.x" in footer
- Subtle divider line above footer (1px, 40% width, centered)

**Spacing Rhythm:**
- Main message to subtitle: gap-4
- Subtitle to decorative element: gap-8
- Content to footer: Automatic spacing with min-h-screen flex layout

---

## Images

**No hero image required** - This design relies entirely on typography and negative space for visual impact.

---

## Accessibility

- Semantic HTML structure (<main>, <footer>)
- Proper heading hierarchy (h1 for "hi")
- Sufficient contrast ratios for all text
- Focus states on any interactive elements (if added)

**Character Count Check:** ~2,850 characters ✓ (well under 1500 token limit)