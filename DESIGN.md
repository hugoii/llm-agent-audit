---
name: ActionBoundary
description: A restrained evidence desk for high-impact agent authorization reviews.
colors:
  primary: "#0f766e"
  primary-deep: "#0b4f4a"
  primary-soft: "#e7f5f3"
  ink: "#161719"
  muted: "#626a75"
  paper: "#f7f8fa"
  surface: "#ffffff"
  line: "#dbe1e8"
  line-strong: "#b8c1cc"
  charcoal: "#151619"
  pass: "#166534"
  pass-soft: "#ecfdf5"
  warning: "#b45309"
  warning-soft: "#fff7ed"
  fail: "#991b1b"
  fail-soft: "#fef2f2"
typography:
  display:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
    fontSize: "clamp(3.1rem, 4.1vw, 4rem)"
    fontWeight: 780
    lineHeight: 0.98
    letterSpacing: "-0.055em"
  headline:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
    fontSize: "2.1rem"
    fontWeight: 800
    lineHeight: 1.08
    letterSpacing: "-0.03em"
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
    fontSize: "0.78rem"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "0.08em"
  code:
    fontFamily: "SFMono-Regular, Consolas, Liberation Mono, monospace"
    fontSize: "0.84rem"
    fontWeight: 600
    lineHeight: 1.45
rounded:
  sm: "4px"
  md: "8px"
  pill: "999px"
spacing:
  xs: "6px"
  sm: "8px"
  md: "12px"
  lg: "18px"
  xl: "32px"
  section: "64px"
components:
  button-primary:
    backgroundColor: "{colors.charcoal}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "11px 15px"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.primary-deep}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "11px 15px"
    height: "44px"
  button-outline:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.charcoal}"
    rounded: "{rounded.md}"
    padding: "11px 15px"
    height: "44px"
  evidence-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "18px"
---

# Design System: ActionBoundary

## Overview

**Creative North Star: "The Evidence Desk"**

ActionBoundary presents high-impact agent authorization as a reviewable body of evidence, not as spectacle. Cool paper surfaces, dark evidence panels, restrained teal, compact state markers, and report-like spacing create a calm working environment for founders, engineers, and security reviewers.

The system is information-dense but not cramped. It rejects generic AI SaaS landing-page clichés and keeps every decorative choice subordinate to scope, provenance, and verdict readability.

**Key Characteristics:**

- Strong first-fold claim anchored by a visible authorization trace.
- Cool paper sections and white report surfaces with restrained teal accents.
- Small-radius containers, precise borders, and compact evidence labels.
- Explicit limits, named responsibility, and reviewable source artifacts.
- Responsive layouts and reduced-motion behavior without hiding content.

## Colors

The palette separates evidence state from brand emphasis: teal signals navigation and trust, while green, amber, and red are reserved for verdict meaning.

### Primary

- **Boundary Teal:** links, focus treatments, selected proof paths, and quiet trust emphasis.
- **Deep Boundary Teal:** hover states and high-contrast accent text on light surfaces.
- **Soft Boundary Teal:** restrained highlighted backgrounds and selected states.

### Neutral

- **Evidence Ink:** primary body text and dense evidence labels.
- **Cool Paper:** the default page surface.
- **Report White:** cards, tables, and report-like containers.
- **Evidence Charcoal:** hero and dark evidence surfaces.
- **Ledger Lines:** borders and dividers that organize evidence without becoming decoration.

### State

- **Pass Green:** successful authorization evidence only.
- **Review Amber:** warnings, incomplete evidence, and caution states only.
- **Fail Red:** failed or unauthorized evidence only.

**The Evidence Color Rule.** Green, amber, and red are reserved for evidence state; they never decorate marketing sections.

**The One Accent Rule.** Teal remains visually scarce enough to identify interactive paths and trusted evidence without washing the page in brand color.

## Typography

**Display Font:** system sans-serif stack

**Body Font:** system sans-serif stack

**Label/Mono Font:** SFMono-Regular, Consolas, Liberation Mono, monospace

**Character:** The single sans family keeps the site operational and unbranded by fashion. Weight, size, alignment, and mono evidence labels carry hierarchy.

### Hierarchy

- **Display:** heavy, tightly tracked hero claims used once per page.
- **Headline:** compact section conclusions with short line lengths.
- **Title:** strong component labels and report headings.
- **Body:** calm explanatory text, generally capped near 70 characters per line.
- **Label:** compact uppercase or technical metadata with deliberate tracking.
- **Code:** hashes, field names, tool calls, schema identifiers, and trace excerpts only.

**The Scan First Rule.** A busy founder should understand the claim, proof boundary, and next action without parsing every paragraph.

**The No Jargon Fog Rule.** Technical vocabulary is allowed only when it names an actual artifact, field, control, or failure mode.

## Elevation

The system is flat by default. Borders and tonal changes define most surfaces; small ambient shadows distinguish report cards from the paper background, and stronger shadows appear only for featured or interactive surfaces.

### Shadow Vocabulary

- **Ambient low** (`0 2px 8px rgba(16, 24, 40, 0.08)`): quiet report-card separation.
- **Interactive lift** (`0 8px 14px rgba(16, 24, 40, 0.10)`): featured surfaces and meaningful hover feedback.

**The Report Surface Rule.** A surface should feel like evidence placed on a desk, not a floating SaaS widget.

**The Border-or-Shadow Rule.** Do not pair a strong border with a wide soft shadow; use one structural signal at a time.

## Components

### Buttons

- **Shape:** gently curved rectangle with an eight-pixel radius and a minimum forty-four-pixel target.
- **Primary:** charcoal on light surfaces; light neutral on the dark hero.
- **Hover / Focus:** shift to deep teal or a slightly brighter hero surface; preserve a visible two-pixel focus outline.
- **Secondary / Outline:** white or translucent surface with a real border, never a gradient-filled marketing treatment.

### Cards / Containers

- **Corner Style:** eight-pixel radius.
- **Background:** white on paper, charcoal variants only for evidence contrast.
- **Shadow Strategy:** flat or ambient low; interactive lift is exceptional.
- **Border:** one-pixel ledger line where structure needs an explicit edge.
- **Internal Padding:** twelve to eighteen pixels for compact evidence; thirty-two pixels only for major offer or report panels.

### Inputs / Fields

- **Style:** white surface, strong ledger border, eight-pixel radius, and plain-language labels.
- **Focus:** two-pixel translucent teal outline with offset.
- **Error / Disabled:** pair state color with text; never use color alone.

### Navigation

- Compact horizontal navigation uses the same sans family, quiet glass or paper treatment, deep-teal hover text, and a clearly bounded primary action. Mobile navigation may wrap, but must preserve visible access to AP review, evidence, trust, and contact paths.

### Evidence Status

- PASS, BLOCKED, and INCONCLUSIVE use text labels, state color, and a short reason. Hashes and artifact versions use mono type. No status may rely on a colored dot alone.

## Do's and Don'ts

### Do:

- **Do** show bound evidence and explicit limitations before promotional claims.
- **Do** lead public navigation and examples with AP and finance authorization.
- **Do** preserve staging-only scope, named responsibility, and customer-execution provenance.
- **Do** use the eight-pixel radius, cool paper, report white, evidence charcoal, and restrained teal consistently.
- **Do** keep focus states, keyboard order, semantic headings, and reduced-motion fallbacks intact.

### Don't:

- **Don't** imitate a generic AI safety platform or all-purpose governance suite.
- **Don't** turn evidence into benchmark leaderboard or vendor-ranking theater.
- **Don't** imply compliance certification, a security seal, or a "certified secure" result.
- **Don't** present anonymous scanner findings without customer execution evidence.
- **Don't** use generic AI SaaS landing-page clichés, purple-blue gradients, robot imagery, floating orbs, decorative dashboards, or glassmorphism.
- **Don't** use absolute claims such as "buyer-ready" or "verifiable" when an artifact is synthetic, illustrative, incomplete, or not bound to customer execution.
- **Don't** use side-stripe borders as a card accent or combine one-pixel borders with wide soft shadows.
