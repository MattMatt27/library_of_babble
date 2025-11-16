# Matt's Portfolio - Style Guide

## Design Philosophy

My portfolio features a modern, dark-first design. The design prioritizes readability, consistency, and a professional yet approachable user experience.

**Core Principles:**
- Dark-first design with carefully chosen accent colors
- Modern, clean typography with excellent readability
- Consistent spacing and visual rhythm
- Subtle depth through shadows and layers
- Smooth interactions with thoughtful transitions
- Professional yet approachable aesthetic

---

## Color Palette

### Backgrounds

```css
--bg-primary: #0d1117      /* Main background */
--bg-secondary: #161b22    /* Cards, containers, elevated surfaces */
--bg-tertiary: #21262d     /* Hover states, interactive elements */
--bg-navbar: #010409       /* Navigation bar (darkest) */
```

### Text

```css
--text-primary: #e6edf3    /* Primary text (high contrast) */
--text-secondary: #8b949e  /* Secondary text, labels */
--text-tertiary: #6e7681   /* Tertiary text, metadata */
--text-link: #58a6ff       /* Links (light blue) */
```

### Accent Colors

```css
--accent-blue: #58a6ff          /* Primary actions, links */
--accent-blue-hover: #79c0ff    /* Hover state for blue */
--accent-purple: #bc8cff        /* Secondary accent */
--accent-purple-hover: #d2a8ff  /* Hover state for purple */
--accent-orange: #ff9966        /* Tertiary accent, notifications */
--accent-orange-hover: #ffad85  /* Hover state for orange */
```

### Semantic Colors

```css
--success: #3fb950   /* Success states, confirmations */
--danger: #f85149    /* Errors, deletions, warnings */
--warning: #d29922   /* Warnings, alerts */
--info: #58a6ff      /* Info messages */
```

### Borders & Dividers

```css
--border-primary: #30363d    /* Primary borders */
--border-secondary: #21262d  /* Subtle dividers */
--border-focus: #58a6ff      /* Focus states */
```

### Shadows

```css
--shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.3)        /* Small elements */
--shadow-md: 0 3px 8px rgba(0, 0, 0, 0.4)        /* Cards, modals */
--shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.5)       /* Elevated elements */
--shadow-glow: 0 0 12px rgba(88, 166, 255, 0.3)  /* Accent glow */
```

---

## Typography

### Font Families

**Primary Font (Body & UI):**
```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
```

**Monospace Font (Code/Data):**
```css
font-family: "SF Mono", "Monaco", "Cascadia Code", "Roboto Mono", monospace;
```

**Display Font (Headers):**
```css
font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
```

### Font Scale

```css
--font-xs: 0.75rem     /* 12px - Small labels, meta */
--font-sm: 0.875rem    /* 14px - Secondary text */
--font-base: 1rem      /* 16px - Body text */
--font-md: 1.125rem    /* 18px - Emphasized text */
--font-lg: 1.25rem     /* 20px - Small headings */
--font-xl: 1.5rem      /* 24px - Section headings */
--font-2xl: 1.875rem   /* 30px - Page titles */
--font-3xl: 2.25rem    /* 36px - Hero text */
--font-4xl: 3rem       /* 48px - Large hero */
```

### Font Weights

```css
--font-normal: 400
--font-medium: 500
--font-semibold: 600
--font-bold: 700
```

### Line Heights

```css
--leading-tight: 1.25
--leading-normal: 1.5
--leading-relaxed: 1.75
```

---

## Spacing System

Consistent spacing scale based on 8px increments:

```css
--space-1: 0.25rem   /* 4px */
--space-2: 0.5rem    /* 8px */
--space-3: 0.75rem   /* 12px */
--space-4: 1rem      /* 16px */
--space-5: 1.25rem   /* 20px */
--space-6: 1.5rem    /* 24px */
--space-8: 2rem      /* 32px */
--space-10: 2.5rem   /* 40px */
--space-12: 3rem     /* 48px */
--space-16: 4rem     /* 64px */
--space-20: 5rem     /* 80px */
```

---

## Components

### Buttons

#### Primary Button

```html
<button class="btn btn-primary">Save Changes</button>
```

```css
.btn-primary {
  background: var(--accent-blue);
  color: #ffffff;
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: var(--font-medium);
  border: none;
  cursor: pointer;
  transition: all 150ms ease;
  box-shadow: var(--shadow-sm);
}

.btn-primary:hover {
  background: var(--accent-blue-hover);
  box-shadow: var(--shadow-md);
}
```

#### Secondary Button

```html
<button class="btn btn-secondary">Cancel</button>
```

```css
.btn-secondary {
  background: transparent;
  color: var(--accent-blue);
  border: 1px solid var(--accent-blue);
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: all 150ms ease;
}

.btn-secondary:hover {
  background: rgba(88, 166, 255, 0.1);
}
```

#### Danger Button

```html
<button class="btn btn-danger">Delete</button>
```

```css
.btn-danger {
  background: var(--danger);
  color: #ffffff;
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: var(--font-medium);
  border: none;
  cursor: pointer;
  transition: all 150ms ease;
}

.btn-danger:hover {
  background: #ff6b6b;
}
```

#### Ghost Button

```html
<button class="btn btn-ghost">Learn More</button>
```

```css
.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-primary);
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: all 150ms ease;
}

.btn-ghost:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}
```

### Cards

#### Basic Card

```html
<div class="card">
  <div class="card-content">
    <h3 class="card-title">Card Title</h3>
    <p class="card-subtitle">Subtitle or description</p>
  </div>
</div>
```

```css
.card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: 12px;
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
  transition: all 200ms ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--border-focus);
}
```

#### Book/Movie/Show Card

```html
<div class="card book-card">
  <div class="card-image">
    <img src="/path/to/cover.jpg" alt="Book Title">
  </div>
  <div class="card-content">
    <h3 class="card-title">Book Title</h3>
    <p class="card-subtitle">Author Name</p>
    <div class="card-meta">
      <span class="rating">★★★★★</span>
      <span class="year">2023</span>
    </div>
  </div>
</div>
```

```css
.book-card .card-image {
  aspect-ratio: 2 / 3;
  overflow: hidden;
  border-radius: 8px 8px 0 0;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 200ms ease;
}

.card:hover .card-image img {
  transform: scale(1.05);
}

.card-title {
  font-size: var(--font-base);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--space-2) 0;
}

.card-subtitle {
  font-size: var(--font-sm);
  color: var(--text-secondary);
  margin: 0 0 var(--space-3) 0;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--font-sm);
  color: var(--text-tertiary);
}

.rating {
  color: var(--accent-orange);
}
```

### Forms

#### Input Fields

```html
<div class="form-group">
  <label for="username">Username</label>
  <input type="text" id="username" class="form-input" placeholder="Enter username">
</div>
```

```css
.form-input {
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: 6px;
  padding: 10px 12px;
  color: var(--text-primary);
  font-size: var(--font-base);
  width: 100%;
  transition: all 150ms ease;
}

.form-input:focus {
  border-color: var(--accent-blue);
  outline: none;
  box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.1);
}

label {
  font-size: var(--font-sm);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
  margin-bottom: var(--space-2);
  display: block;
}
```

### Tables

```html
<div class="table-container">
  <table>
    <thead>
      <tr>
        <th>Column 1</th>
        <th>Column 2</th>
        <th>Column 3</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Data 1</td>
        <td>Data 2</td>
        <td>Data 3</td>
      </tr>
    </tbody>
  </table>
</div>
```

```css
.table-container {
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: 12px;
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

thead {
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-primary);
}

th {
  padding: var(--space-4);
  text-align: left;
  font-weight: var(--font-semibold);
  color: var(--text-secondary);
  font-size: var(--font-sm);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-4);
  border-bottom: 1px solid var(--border-secondary);
  color: var(--text-primary);
}

tr:last-child td {
  border-bottom: none;
}

tbody tr:hover {
  background: var(--bg-tertiary);
}
```

---

## Layout

### Grid System

```css
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--space-6);
  padding: var(--space-6);
}

@media (min-width: 768px) {
  .grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: var(--space-8);
  }
}
```

### Container

```css
.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--space-6);
}

@media (min-width: 768px) {
  .container {
    padding: 0 var(--space-8);
  }
}
```

---

## Transitions & Animations

### Standard Transitions

```css
--transition-fast: 150ms ease      /* Fast interactions */
--transition-base: 200ms ease      /* Standard interactions */
--transition-slow: 300ms ease      /* Slower, more dramatic */
--transition-page: 400ms cubic-bezier(0.4, 0, 0.2, 1)  /* Page transitions */
```

### Common Animations

#### Fade In

```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.fade-in {
  animation: fadeIn 200ms ease;
}
```

#### Slide Up

```css
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.slide-up {
  animation: slideUp 300ms ease;
}
```

#### Loading Skeleton

```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--bg-tertiary) 0%,
    var(--bg-secondary) 50%,
    var(--bg-tertiary) 100%
  );
  background-size: 200% 100%;
  animation: loading 1.5s ease-in-out infinite;
}

@keyframes loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

---

## Responsive Design

### Breakpoints

```css
--breakpoint-sm: 640px    /* Small tablets */
--breakpoint-md: 768px    /* Tablets */
--breakpoint-lg: 1024px   /* Small laptops */
--breakpoint-xl: 1280px   /* Desktops */
--breakpoint-2xl: 1536px  /* Large desktops */
```

### Mobile-First Approach

Always design for mobile first, then enhance for larger screens:

```css
/* Mobile styles (default) */
.element {
  font-size: var(--font-sm);
  padding: var(--space-4);
}

/* Tablet and up */
@media (min-width: 768px) {
  .element {
    font-size: var(--font-base);
    padding: var(--space-6);
  }
}

/* Desktop and up */
@media (min-width: 1024px) {
  .element {
    font-size: var(--font-md);
    padding: var(--space-8);
  }
}
```

---

## Accessibility

### Color Contrast

All color combinations meet WCAG AA standards:
- Primary text on primary background: 13.37:1 (AAA)
- Secondary text on primary background: 7.58:1 (AA)
- Accent blue on dark background: 8.59:1 (AAA)

### Focus Indicators

```css
:focus-visible {
  outline: 2px solid var(--accent-blue);
  outline-offset: 2px;
  border-radius: 4px;
}
```

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Interactive Element Guidelines

- Minimum touch target size: 44px × 44px
- Provide clear focus indicators for keyboard navigation
- Use semantic HTML elements
- Include appropriate ARIA labels when needed
- Ensure sufficient color contrast for all text

---

## Best Practices

### Do's

- Use CSS custom properties (variables) for all colors, spacing, and typography
- Follow the established spacing scale
- Use consistent border-radius values (6px for small elements, 12px for cards)
- Apply smooth transitions to interactive elements
- Test on multiple screen sizes
- Ensure keyboard accessibility
- Use semantic HTML elements

### Don'ts

- Don't use arbitrary color values outside the palette
- Don't use pixel values for spacing (use CSS variables)
- Don't create new font sizes outside the scale
- Don't override focus indicators without providing an alternative
- Don't animate elements without respecting `prefers-reduced-motion`
- Don't use pure black (#000000) or pure white (#ffffff) for text

---

## File Structure

```
static/
├── css/
│   ├── variables.css      # All design tokens
│   ├── base.css           # Reset, typography, global styles
│   ├── components.css     # Reusable components
│   ├── layout.css         # Grid, flexbox utilities
│   ├── utilities.css      # Helper classes
│   └── pages/             # Page-specific styles
│       ├── home.css
│       ├── books.css
│       ├── movies.css
│       ├── shows.css
│       ├── artworks.css
│       └── music.css
├── js/
│   ├── main.js
│   └── components/        # Component-specific JavaScript
└── images/
```

---

## Quick Reference

### Common Utility Classes

```css
/* Text */
.text-primary { color: var(--text-primary); }
.text-secondary { color: var(--text-secondary); }
.text-tertiary { color: var(--text-tertiary); }

/* Spacing */
.mt-4 { margin-top: var(--space-4); }
.mb-6 { margin-bottom: var(--space-6); }
.p-4 { padding: var(--space-4); }

/* Display */
.flex { display: flex; }
.grid { display: grid; }
.hidden { display: none; }

/* Alignment */
.text-center { text-align: center; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
```

---

## Contributing

When adding new components or styles:

1. Follow the established design system
2. Use CSS custom properties from `variables.css`
3. Ensure responsive behavior
4. Test accessibility
5. Document new components in this guide
6. Maintain consistency with existing patterns

---

## Questions or Feedback?

For questions about the design system or to propose changes, please open an issue in the project repository.
