# Design System Document

## 1. Overview & Creative North Star: "The Academic Curator"

This design system moves away from the rigid, boxy layouts of traditional student portals and toward a "Digital Curator" experience. It treats information as a curated exhibition—using high-end editorial typography, intentional asymmetry, and deep tonal layering to provide a sense of prestige and focus.

**The Creative North Star: The Academic Curator**
The goal is to provide a sense of "Quiet Authority." We achieve this through the "Breathe and Bleed" technique: using expansive white space (`spacing-12` and `spacing-16`) to let content breathe, while allowing high-contrast red accents (`primary`) to "bleed" into the white space via soft gradients and glassmorphism. This system rejects the "standard" dashboard aesthetic in favor of a fluid, layered environment that feels more like a premium publication than a utility tool.

---

## 2. Colors

The color palette leverages the University of Maryland’s heritage colors but applies them with a modern, sophisticated restraint. Instead of heavy blocks of red and gold, we use them as "illuminations" against a neutral, layered backdrop.

### Surface Hierarchy & Nesting
We define depth through background shifts rather than lines.
- **Base Layer:** `surface` (#f9f9f9) for the global background.
- **Sectioning:** Use `surface_container_low` (#f3f3f3) for large content areas.
- **Interactive Islands:** Use `surface_container_lowest` (#ffffff) for primary cards and interaction points. This "nesting" creates a soft, natural lift.

### The "No-Line" Rule
**Strict Mandate:** Designers are prohibited from using 1px solid borders to section content. Boundaries must be defined solely through background color shifts. For instance, a list of courses should sit on `surface_container` (#eeeeee) with individual items on `surface_container_lowest` (#ffffff).

### The "Glass & Gradient" Rule
To elevate the UI from "web app" to "experience," use Glassmorphism for floating elements (like navigation bars or modal headers). Use `surface_container_lowest` at 80% opacity with a `24px` backdrop blur. 
- **Signature Textures:** For primary CTAs, do not use flat red. Use a linear gradient from `primary` (#b80023) to `primary_container` (#e21833) at a 135-degree angle to provide visual "soul."

---

## 3. Typography

The system uses a pairing of **Manrope** (Display/Headlines) and **Inter** (Body/Labels) to balance academic authority with modern readability.

- **Display (Manrope):** Set with tight letter-spacing (-0.02em) to create a bold, editorial feel. Use `display-lg` for hero greetings and `headline-md` for section headers.
- **Body (Inter):** Chosen for its neutral, high-legibility character. Use `body-lg` for student-facing messages to ensure a friendly, approachable tone.
- **The Hierarchy Strategy:** Use `primary` (#b80023) sparingly in typography—only for high-level "Title" tokens to draw the eye. Body text should always remain `on_surface` (#1a1c1c) for maximum accessibility.

---

## 4. Elevation & Depth

We move beyond Material Design’s standard shadows by utilizing **Tonal Layering**.

- **The Layering Principle:** Place a `surface_container_highest` (#e2e2e2) element atop a `surface` (#f9f9f9) background to signify "pressed" or "secondary" status. Place a `surface_container_lowest` (#ffffff) element on anything else to signify "active" or "primary."
- **Ambient Shadows:** For floating modals, use a custom shadow: `0px 20px 40px rgba(0, 0, 0, 0.04)`. The shadow must be almost imperceptible, mimicking natural light.
- **The "Ghost Border" Fallback:** If a container requires definition against an identical background (e.g., a white card on a white section), use the `outline_variant` (#e6bdba) at **15% opacity**. Never use a 100% opaque border.

---

## 5. Components

### Buttons
- **Primary:** Gradient from `primary` to `primary_container`. Roundedness: `full`. Padding: `spacing-3` vertical, `spacing-6` horizontal.
- **Secondary:** Surface-only with a "Ghost Border." Text color is `primary`.
- **Tertiary:** No background. Use `label-md` in `primary` with a `spacing-1` underline that expands on hover.

### Cards & Lists
- **Rule:** Forbid the use of divider lines. Use `spacing-4` of vertical white space to separate list items. 
- **The "Academic Tile":** Cards should use `rounded-xl` (1.5rem) to feel approachable. On hover, a card should shift from `surface_container_low` to `surface_container_lowest` rather than growing in size.

### Input Fields
- **Styling:** Inputs use `surface_container_high` (#e8e8e8) with no border. On focus, the background shifts to `surface_container_lowest` (#ffffff) with a 2px `secondary` (#725c00) "glow" (shadow), not a border.
- **Labels:** Use `label-sm` in `on_surface_variant` (#5d3f3e), positioned 8px above the input.

### Signature Component: The "Course Aura" Chip
A custom chip for course status. 
- **Active:** Background `secondary_container` (#fdd000), text `on_secondary_container` (#6e5900), `rounded-full`.
- **Completed:** Background `surface_container_highest`, text `on_surface_variant`.

---

## 6. Do's and Don'ts

### Do
- **Do** use `spacing-20` (5rem) for top-level section margins to create an "Editorial" feel.
- **Do** overlap elements slightly (e.g., a profile image overlapping a header container) to break the grid.
- **Do** use `secondary` (Gold) for "Achievement" moments (grades, credits earned).

### Don't
- **Don't** use solid black (#000000) for text; use `on_background` (#1a1c1c) for a softer, more premium look.
- **Don't** use `spacing-px` or `spacing-1` for anything other than icons. Tight spacing creates "Academic Stress," which we want to avoid.
- **Don't** use 90-degree corners. Everything—from inputs to large containers—must use at least `rounded-md` (0.75rem).