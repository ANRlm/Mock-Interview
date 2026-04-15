# Plan: Landing Page Geist Redesign

## TL;DR

**Summary**: Complete redesign of the landing page (HomePage + 6 section components) in Vercel Geist style - removing all emoji icons, colorful gradients, and flashy elements in favor of minimalist monochrome design.

**Deliverables**:
- HeroSection with clean headline, subtle floating UI preview
- FeaturesSection with monochrome icon cards
- TechSection using Lucide icons only
- ArchitectureSection with single-tone pipeline
- HowItWorksSection with subtle step indicators
- MetricsSection with clean metric cards
- HomePage with recent sessions in Geist style

**Effort**: Medium
**Parallel**: YES - 2 waves
**Critical Path**: Hero → Features/Tech/Architecture → HowItWorks/Metrics → HomePage

---

## Context

### Original Request
User: "重构前端首页部分，面试页效果基本达标，但是首页依旧太难看了，我需要vercel风格，简约高级设计感"

### Current Issues Found
- **Emoji icons everywhere** - ⚛️🔷🎨✨📦🛣️🧩💎🚀🗄️🔌🔐🎤🔊🤖🧠🐳⚡🎮🌐
- **Colorful gradients** - `from-blue-500 to-blue-600`, `from-amber-500 to-amber-600`, etc.
- **Flashy colored backgrounds** - `bg-primary/10`, `bg-amber-500/10` on every card
- **Gradient text** - `bg-gradient-to-r ${color} bg-clip-text text-transparent`
- **Busy section backgrounds** - `bg-grid-pattern opacity-5`
- **Noisy animations** - Pulsing circles, complex transforms
- **Numbered badges** - Colored circles with numbers in HowItWorks
- **Heavy visual weight** - Too many accent colors competing

### Geist Design Principles Applied
1. **Monochrome palette** - Only primary accent, everything else grayscale
2. **Typography hierarchy** - Large headings, muted body text
3. **Subtle borders** - Not heavy shadows, clean lines
4. **Minimal animations** - 120/200-300/400ms, ease-out only
5. **No emoji** - Lucide icons or simple SVG
6. **Generous whitespace** - Let content breathe

---

## Work Objectives

### Core Objective
Redesign all 6 landing sections + HomePage to match Vercel Geist aesthetic

### Deliverables
1. HeroSection - Clean, focused, subtle floating mockup
2. FeaturesSection - 6 cards with Lucide icons, monochrome
3. TechSection - Grid with Lucide icons, no gradients
4. ArchitectureSection - Single-color pipeline flow
5. HowItWorksSection - 5 steps, minimal indicators
6. MetricsSection - 4 metrics + progress bars, clean
7. HomePage - Recent sessions in Geist Card style

### Definition of Done
- Zero emoji in any landing component
- Zero gradient text or colored backgrounds on cards
- All icons from Lucide React or inline SVG (stroke only)
- Build passes: `npm run build`
- Design tokens used throughout

### Must Have
- Dark/light mode support preserved
- Responsive layouts unchanged
- Animation cadence: 120/200-300/400ms

### Must NOT Have
- Emoji icons
- Colorful gradients (blue/amber/emerald/purple)
- Flashy hover effects
- Grid background patterns
- Numbered badges

---

## Verification Strategy

- **Test decision**: Tests-after (existing Playwright smoke tests)
- **QA policy**: Visual inspection via dev server
- **Build verification**: `npm run build` must pass

---

## TODOs

- [ ] 1. Redesign HeroSection - clean Geist-style hero

  **What to do**:
  - Remove pulsing blur circles
  - Replace GeistAnimation with a clean floating UI mockup (simple card + waveform)
  - Use Lucide ArrowRight for CTA button
  - Use Lucide ChevronDown for scroll indicator
  - Monochrome stats section (no colored numbers)
  - Clean heading with primary color on key word only

  **Must NOT do**:
  - No pulsing glow effects
  - No abstract circular animations
  - No emoji

  **Recommended Agent Profile**:
  - Category: `visual-engineering`
  - Skills: `[]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 1

  **References**:
  - Design tokens: `src/styles/design-tokens.css:1-135`
  - Existing HeroSection: `src/components/landing/HeroSection.tsx:1-163`
  - Geist typography: `src/styles/typography.css`

  **Acceptance Criteria**:
  - [ ] `npm run build` passes
  - [ ] No emoji characters in file
  - [ ] Uses design tokens (--geist-* vars) or Tailwind token classes

  **QA Scenarios**:
  ```
  Scenario: Build verification
    Tool: Bash
    Steps: cd frontend && npm run build 2>&1 | tail -5
    Expected: "built in Xms" success message
    Evidence: .sisyphus/evidence/landing-hero-build.txt
  ```

  **Commit**: YES | Message: `refactor(landing): redesign HeroSection in Geist style` | Files: `src/components/landing/HeroSection.tsx`

- [ ] 2. Redesign FeaturesSection - monochrome icon cards

  **What to do**:
  - Replace emoji icons with Lucide icons (stroke-width: 1.5)
  - Remove colored backgrounds `bg-primary/10`, `bg-amber-500/10`
  - Use `bg-surface` or `bg-transparent` for cards
  - Clean border, subtle hover (border-hover color change)
  - Section title uses `text-heading-32`, descriptions use `text-copy-16 text-text-secondary`

  **Must NOT do**:
  - No colored backgrounds on icons
  - No colored text on titles
  - No gradient text

  **Recommended Agent Profile**:
  - Category: `visual-engineering`
  - Skills: `[]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 1

  **References**:
  - Design tokens: `src/styles/design-tokens.css`
  - Existing FeaturesSection: `src/components/landing/FeaturesSection.tsx`
  - Lucide icons: `src/components/ui/icons.tsx` (if exists) or direct import from lucide-react

  **Acceptance Criteria**:
  - [ ] Zero emoji in file
  - [ ] Icons use Lucide with stroke (not filled)
  - [ ] Card hover uses border-hover transition

  **QA Scenarios**:
  ```
  Scenario: Build verification
    Tool: Bash
    Steps: cd frontend && npm run build 2>&1 | tail -5
    Expected: "built in Xms" success message
    Evidence: .sisyphus/evidence/landing-features-build.txt
  ```

  **Commit**: YES | Message: `refactor(landing): redesign FeaturesSection with Lucide icons` | Files: `src/components/landing/FeaturesSection.tsx`

- [ ] 3. Redesign TechSection - remove all emoji, clean grid

  **What to do**:
  - Replace all emoji with Lucide icons
  - Remove `bg-gradient-to-r ${color}` gradient text
  - Category titles use `text-text` not colored gradient
  - Tech cards use clean `bg-surface` background
  - Grid layout preserved (2 cols desktop, 4 cols for tech items)

  **Must NOT do**:
  - No emoji anywhere
  - No gradient text
  - No colored backgrounds on cards

  **Recommended Agent Profile**:
  - Category: `visual-engineering`
  - Skills: `[]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 1

  **References**:
  - Design tokens: `src/styles/design-tokens.css`
  - Existing TechSection: `src/components/landing/TechSection.tsx`
  - Map: ⚛️→Monitor, 🔷→Code, 🎨→Palette, ✨→Sparkles, 📦→Box, 🛣️→Route, 🧩→Puzzle, 💎→Gem

  **Acceptance Criteria**:
  - [ ] Zero emoji in file
  - [ ] All icons from Lucide
  - [ ] Build passes

  **QA Scenarios**:
  ```
  Scenario: Build verification
    Tool: Bash
    Steps: cd frontend && npm run build 2>&1 | tail -5
    Expected: "built in Xms" success message
    Evidence: .sisyphus/evidence/landing-tech-build.txt
  ```

  **Commit**: YES | Message: `refactor(landing): replace emoji with Lucide icons in TechSection` | Files: `src/components/landing/TechSection.tsx`

- [ ] 4. Redesign ArchitectureSection - single-tone pipeline

  **What to do**:
  - Remove all colored gradients (`from-blue-500`, `from-purple-500`, etc.)
  - Use single `border-border` and `bg-surface` for all pipeline boxes
  - Labels use `text-text` primary text, sublabels use `text-text-muted`
  - Bottom stats row uses `text-primary` for values
  - Remove background grid pattern

  **Must NOT do**:
  - No colored pipeline boxes
  - No gradient text
  - No grid background pattern

  **Recommended Agent Profile**:
  - Category: `visual-engineering`
  - Skills: `[]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 1

  **References**:
  - Design tokens: `src/styles/design-tokens.css`
  - Existing ArchitectureSection: `src/components/landing/ArchitectureSection.tsx`

  **Acceptance Criteria**:
  - [ ] All boxes use monochrome styling
  - [ ] No gradient colors anywhere
  - [ ] Build passes

  **QA Scenarios**:
  ```
  Scenario: Build verification
    Tool: Bash
    Steps: cd frontend && npm run build 2>&1 | tail -5
    Expected: "built in Xms" success message
    Evidence: .sisyphus/evidence/landing-arch-build.txt
  ```

  **Commit**: YES | Message: `refactor(landing): monochrome pipeline in ArchitectureSection` | Files: `src/components/landing/ArchitectureSection.tsx`

- [ ] 5. Redesign HowItWorksSection - minimal step indicators

  **What to do**:
  - Remove numbered badges (`-top-2 -right-2 w-6 h-6 rounded-full bg-primary`)
  - Remove colored backgrounds on icon circles
  - Use simple `border border-border` circle for icon
  - Icon inside circle uses `text-text-muted`
  - Steps connected by subtle `border-border` line (not gradient line)
  - Clean typography hierarchy

  **Must NOT do**:
  - No numbered badges
  - No primary-colored circles
  - No gradient connector lines

  **Recommended Agent Profile**:
  - Category: `visual-engineering`
  - Skills: `[]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 2

  **References**:
  - Design tokens: `src/styles/design-tokens.css`
  - Existing HowItWorksSection: `src/components/landing/HowItWorksSection.tsx`

  **Acceptance Criteria**:
  - [ ] No numbered badges
  - [ ] Monochrome icon circles
  - [ ] Build passes

  **QA Scenarios**:
  ```
  Scenario: Build verification
    Tool: Bash
    Steps: cd frontend && npm run build 2>&1 | tail -5
    Expected: "built in Xms" success message
    Evidence: .sisyphus/evidence/landing-howitworks-build.txt
  ```

  **Commit**: YES | Message: `refactor(landing): minimal step indicators in HowItWorksSection` | Files: `src/components/landing/HowItWorksSection.tsx`

- [ ] 6. Redesign MetricsSection - clean metric cards

  **What to do**:
  - Remove all colorful `text-*` and `bg-*/10` color accents
  - Metric values use `text-text` (not colored)
  - Icon containers use `bg-surface` with `text-text-muted`
  - Progress bars use `bg-border` for track, `bg-text-muted` for fill
  - Remove colored blur backgrounds at section top/bottom
  - Clean border on cards

  **Must NOT do**:
  - No colored metric values (amber/blue/emerald)
  - No colorful blur backgrounds
  - No bg-amber-500/bg-emerald-500/bg-blue-500 on progress

  **Recommended Agent Profile**:
  - Category: `visual-engineering`
  - Skills: `[]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 2

  **References**:
  - Design tokens: `src/styles/design-tokens.css`
  - Existing MetricsSection: `src/components/landing/MetricsSection.tsx`

  **Acceptance Criteria**:
  - [ ] All metric values monochrome
  - [ ] Progress bars use neutral colors
  - [ ] Build passes

  **QA Scenarios**:
  ```
  Scenario: Build verification
    Tool: Bash
    Steps: cd frontend && npm run build 2>&1 | tail -5
    Expected: "built in Xms" success message
    Evidence: .sisyphus/evidence/landing-metrics-build.txt
  ```

  **Commit**: YES | Message: `refactor(landing): monochrome metrics in MetricsSection` | Files: `src/components/landing/MetricsSection.tsx`

- [ ] 7. Redesign HomePage - Geist-style recent sessions

  **What to do**:
  - Replace `text-lg font-medium text-text` headings with `text-heading-24 font-semibold`
  - Cards use clean `bg-surface` with `border border-border`
  - Hover state uses `hover:border-border-hover` transition
  - Status Badge uses semantic colors from design tokens
  - Recent sessions section header use Geist typography
  - Remove any leftover emoji

  **Must NOT do**:
  - No custom colored headings
  - No heavy shadows

  **Recommended Agent Profile**:
  - Category: `visual-engineering`
  - Skills: `[]`
  - Omitted: `[]`

  **Parallelization**: Can Parallel: YES | Wave 2

  **References**:
  - Design tokens: `src/styles/design-tokens.css`
  - Existing HomePage: `src/pages/HomePage.tsx`

  **Acceptance Criteria**:
  - [ ] Typography uses Geist scale classes
  - [ ] Cards use design tokens
  - [ ] Build passes

  **QA Scenarios**:
  ```
  Scenario: Build verification
    Tool: Bash
    Steps: cd frontend && npm run build 2>&1 | tail -5
    Expected: "built in Xms" success message
    Evidence: .sisyphus/evidence/landing-homepage-build.txt
  ```

  **Commit**: YES | Message: `refactor(landing): apply Geist typography to HomePage` | Files: `src/pages/HomePage.tsx`

---

## Final Verification Wave (MANDATORY)

- [ ] F1. Build passes - `npm run build`
- [ ] F2. No emoji in landing files - grep for emoji pattern
- [ ] F3. Design tokens used - verify --geist-* or Tailwind token classes
- [ ] F4. Animation cadence - verify 120/200-300/400ms values

---

## Commit Strategy

Single commit after all tasks: `refactor(frontend): complete Geist redesign of landing page`

---

## Success Criteria

1. All 6 sections + HomePage use design tokens
2. Zero emoji characters across all landing files
3. Zero gradient text or colorful card backgrounds
4. All icons from Lucide React or inline SVG (stroke only)
5. Build passes without errors
6. Minimalist, premium Vercel/Geist aesthetic achieved
