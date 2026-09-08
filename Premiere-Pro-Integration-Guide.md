# Premiere Pro Integration Guide

## Overview
Complete guide for integrating organized creative resources into Adobe Premiere Pro. All assets are consolidated under `X:/Work Drive/Resources/` with per-folder index files documenting contents, formats, and usage.

---

## Complete Folder Structure

```
X:/Work Drive/Resources/
|
+-- Fonts/
|   +-- _Consolidated/
|   |   +-- Serif/           (3 families) — Formal, editorial, headlines
|   |   +-- Sans-Serif/      (11 families) — Clean, modern, body text
|   |   +-- Display/         (21 families) — Impact, posters, titles
|   |   +-- Handwriting/     (3 families) — Personal, quotes, informal
|   |   +-- Monospace/       (3 families) — Code, technical, monolithic
|   +-- Serif/               (raw source — OTF/TTF/WEB/WOFF per family)
|   +-- Sans-Serif/          (raw source — subdirs per family)
|   +-- Display/             (raw source — many subdirs)
|   +-- Handwriting/         (raw source — 3 extracted families)
|   +-- Monospace/           (raw source — 3 subdirs)
|
+-- LUTs/
|   +-- Pro-video-luts/      (102 LUTs) — .cube, .look, .3dl
|   +-- Creative-LUTs/       (3 LUTs) — .cube
|   +-- Shutterstock-Free-LUTs/ (13 LUTs) — .cube
|   +-- LUTS/                (empty — source directory)
|
+-- Transitions/
|   +-- Camera-transitions/      (4 packages + Premiere Pro/)
|   |   +-- Camera Fisheye Transitions for Premiere Pro/
|   |   +-- Camera Optics Transitions for Premiere Pro/
|   |   +-- Camera Perspective Transitions for Premiere Pro/
|   |   +-- Clicks Camera Transitions/
|   |   +-- Premiere Pro/        (.prproj + Assets)
|   +-- Cinematic-transitions/   (8 items — .prproj + subdirs)
|   |   +-- 02 Premiere Pro/     (.prproj + Assets)
|   |   +-- Aesthetic Transitions/
|   |   +-- Footage/
|   |   +-- Fast Shutter Effect In Premiere Pro 4K.prproj
|   |   +-- Film Damage Optic 03.prproj
|   |   +-- Film Damage Panoramic 02.prproj
|   +-- Distorted-transitions/  (3 packages + Premiere Pro/)
|   |   +-- MOGRT/               (Motion Graphics templates)
|   |   +-- Premiere Pro/        (.prproj files)
|   |   +-- Crazy Lens Transitions HD.prproj
|   |   +-- Crazy Lens Transitions UHD.prproj
|   |   +-- Insane Distort Transitions.prproj
|   +-- Fast-transitions/       (8+ packages + .prproj)
|       +-- 01. Transitions/
|       +-- 02. Sound FX/
|       +-- Lens Push Transitions/
|       +-- Panoramic Transitions Premiere Pro Template/
|       +-- Real Camera Transitions For Premiere Pro/
|       +-- Smooth Transitions For Premiere Pro/
|       +-- Viral Transitions/
|       +-- CRT Panoramic Transitions Vol. 03.prproj
|       +-- Light Camera Transitions.prproj
|
+-- Effects/
|   +-- After Effects/      (After Effects project files)
|   +-- Main File/          (Source PSD/PRPROJ)
|   +-- Help/               (Documentation)
|   +-- Glass 3D Text Effect.psd
|
+-- Mockups/
|   +-- Posters/            (6 PSD files — wall, outdoor, numbered)
|   +-- Laptops/            (1 PSD — laptop mockup)
|   +-- Concert ticket Mockup/ (4 PSDs + Guide PDF)
|   +-- Files/              (2 PSDs — business card front/back)
|   +-- Main File/          (Brochure mockup PSD + Guide)
|   +-- Main Files/         (Guide PDF + nested subdir)
|   +-- MAINFILE/           (Additional mockup files)
|   +-- Help/               (Guide, help PDFs)
|
+-- Templates/
|   +-- After Effects/      (After Effects templates)
|   +-- Craftis_v1.2.10/    (Instagram Stories Pack)
|   +-- Main File/          (Source templates)
|   +-- mainfiles aixor/    (Aixor template source)
|   +-- My-Templates-01/    (Custom template collection)
|   +-- themeforest-innove/ (Innove theme)
|   +-- themeforest-konstruktion/ (Konstruktion theme)
|   +-- Smooth Sub Bass Drop Downer_SFX/ (Sound effects)
|   +-- Fashionamen - E commerce Website.fig (Figma design)
|   +-- Swipe 1/2/3.mp3/.wav (Transition swipe sounds)
|   +-- Pop.wav (Pop sound effect)
|   +-- Font Used.txt, Font 1.rtf, Font 1 copy.rtf (Font references)
|   +-- Help File - How to Use Text Effect.pdf
|
+-- Plugins/
    +-- MisterHorseProductManagerSetup_3.7.2.msi
```

---

## Fonts Integration

### Installation (Recommended)
1. Open `X:/Work Drive/Resources/Fonts/_Consolidated/`
2. Navigate to the desired category (Serif, Sans-Serif, Display, Handwriting, Monospace)
3. Open the font family folder
4. **Windows**: Right-click each `.ttf` or `.otf` → `Install for all users`
   **macOS**: Double-click → `Install Font`
5. Restart Premiere Pro
6. Access via `Window → Essential Graphics` → Fonts dropdown

### Font Categories

| Category | Families | Best For |
|----------|----------|----------|
| **Serif** (3) | GroutpixFlowSlabSerif, Ciscela, SATriumph | Formal titles, editorial, headlines |
| **Sans-Serif** (11) | Bigstage, Boldonse, Corify, Franie, GCVank, GrandMighty, Know, Monigue, NeueKalimat, Sublime, XenonNue | Body text, modern UI, clean titles |
| **Display** (21) | AOTLostContact, Bitroad, Boomme, Bredast, CookConthic, Enligas, FilthyCreation, Grift, Locatro, MaltinerDisplay, Midruns, MysticDream, Newblack, Nority, PCMerchis, QEBOXCHROME, Rions, Seatren, Shadows, SquidBoy, Swinger | Impact titles, posters, social media |
| **Handwriting** (3) | Lust, Soge, SunsetScript | Personal touches, quotes, informal |
| **Monospace** (3) | CSClaireMono, LeniaMono, Monoblock | Code displays, technical, monolithic |

### Font Formats in `_Consolidated/`
- **OTF** (OpenType) — Full feature support, ligatures, alternates
- **TTF** (TrueType) — Universal compatibility, safe for all apps
- **Variable** (VF) — Single file, multiple weights via axis sliders
- **WOFF/WOFF2** — Web-only, not needed for Premiere Pro

---

## LUTs Integration

### Apply in Lumetri Color
1. `Window → Lumetri Color`
2. `Creative` tab → `Browse` under `Looks`
3. Navigate to `X:/Work Drive/Resources/LUTs/`

### LUT Collections

| Collection | Count | Format | Use Case |
|-----------|-------|--------|----------|
| **Pro-video-luts/** | 102 | .cube, .look, .3dl | Professional grading, cinematic looks |
| **Creative-LUTs/** | 3 | .cube | Artistic effects, experimental grades |
| **Shutterstock-Free-LUTs/** | 13 | .cube | Free collection, various styles |

### Notable LUTs

**Pro-video-luts/** (102 files):
- `Amelia.look` — Portrait beautification
- `APx90 series` (9 LUTs) — City Lights, Dreamy Days, Icy Blue, Moody Gloss, Neon Vibes, etc.
- `PB_*` series (15 LUTs) — Palm Beach collection: Basin, Boulder, Butte, Everest, etc.
- `Teal And Orange.cube` — Popular cinematic grade
- `Subtle Sci-Fi.cube` — Sci-fi looks
- `Vivid Teal.cube`, `War Brown.cube` — Aesthetic grades
- `F-8700-*`, `F-9380-*`, `W-9270-*` — Camera-specific LOG-to-Rec.709 conversions

**Creative-LUTs/** (3 files):
- `Slog3_Cinematics.cube` — Sony S-Log3 to Rec.709 cinematic

**Shutterstock-Free-LUTs/** (13 files):
- `BlueHour.cube`, `ColdChrome.cube`, `MagicHour.cube`
- `CrispAutumn.cube`, `LushGreen.cube`, `OrangeAndBlue.cube`

---

## Transitions Integration

### Apply from Effects Panel
1. `Window → Effects`
2. Browse transition packages
3. Drag and drop onto edit point between two clips
4. Adjust duration by dragging edge

### Transition Packages

| Category | Packages | Key Files | Best For |
|----------|----------|-----------|----------|
| **Camera-transitions/** | 4 packages | Fisheye, Optics, Perspective, Clicks | Camera moves, perspective shifts |
| **Cinematic-transitions/** | 8 items | Film Artefact, Fast Shutter 4K, Film Damage | Film looks, artistic fading |
| **Distorted-transitions/** | 3 packages | Crazy Lens HD/UHD, Insane Distort, MOGRT | Extreme distortion, creative warping |
| **Fast-transitions/** | 8+ packages | Lens Push, Panoramic, Real Camera, Smooth, Viral, CRT | Quick cuts, social media, speed effects |

### Premiere Pro Project Files (.prproj)

All transition packages include `.prproj` files that open directly in Premiere Pro:
- `Camera-transitions/Premiere Pro/` — Camera Transitions.prproj, Action Camera Transitions.prproj
- `Cinematic-transitions/02 Premiere Pro/` — Film Artefact Transitions.prproj
- `Cinematic-transitions/` — Fast Shutter Effect In Premiere Pro 4K.prproj, Film Damage *.prproj
- `Distorted-transitions/Premiere Pro/` — Crazy Lens Transitions HD/UHD.prproj, Insane Distort Transitions.prproj
- `Fast-transitions/` — CRT Panoramic Transitions Vol. 03.prproj, Light Camera Transitions.prproj

### Transition Tips
- **Camera-transitions**: Perspective changes, optical zooms, angle shifts
- **Cinematic-transitions**: Scene changes, time jumps, film-style transitions
- **Distorted-transitions**: Creative warping, psychedelic effects, logo reveals
- **Fast-transitions**: Music videos, social media, fast-paced editing

---

## Effects Integration

### Contents
| Item | Format | Description |
|------|--------|-------------|
| Glass 3D Text Effect.psd | PSD | Glass 3D text effect template |
| After Effects/ | Dir | After Effects project files |
| Main File/ | Dir | Source files for effects |
| Help/ | Dir | Documentation |

### Usage
- Open `.psd` files in Photoshop, import into Premiere Pro via `File → Import`
- After Effects compositions can be dynamically linked via `File → Adobe Dynamic Link`

---

## Mockups Integration

### Contents by Type
| Directory | Files | Format | Description |
|-----------|-------|--------|-------------|
| Posters/ | 6 | PSD | Wall posters, outdoor, numbered mockups |
| Laptops/ | 1 | PSD | High quality laptop mockup |
| Concert ticket Mockup/ | 4 PSD + 1 PDF | PSD/PDF | Concert ticket designs |
| Files/ | 2 | PSD | Business card front/back |
| Main File/ | 1 PSD + 1 PDF | PSD/PDF | Trifold brochure mockup |
| Help/ | 3 | PDF | Guides and documentation |

### Usage
- Open `.psd` in Photoshop
- Edit smart objects to insert your design
- Export or import into Premiere Pro for video mockup presentations

---

## Templates Integration

### Contents
| Directory/Item | Type | Description |
|----------------|------|-------------|
| After Effects/ | Dir | After Effects templates |
| Craftis_v1.2.10/ | Dir | Instagram Stories Pack |
| themeforest-innove/ | Dir | Innove WordPress theme |
| themeforest-konstruktion/ | Dir | Konstruktion theme |
| My-Templates-01/ | Dir | Custom template collection |
| Fashionamen - E commerce Website.fig | Figma | E-commerce website design |
| Smooth Sub Bass Drop Downer_SFX/ | Dir | Sound effects |
| Swipe 1/2/3.mp3, .wav | Audio | Transition swipe sounds |
| Pop.wav | Audio | Pop sound effect |

### Font References
- `Font Used.txt` — Lists fonts used in templates
- `Font 1.rtf`, `Font 1 copy.rtf` — Font specimen files

---

## Plugins Integration

### MisterHorse Product Manager
**File**: `X:/Work Drive/Resources/Plugins/MisterHorseProductManagerSetup_3.7.2.msi`

**Install**:
1. Double-click `.msi` or run: `msiexec /i "MisterHorseProductManagerSetup_3.7.2.msi"`
2. Follow installer wizard
3. Restart Premiere Pro

**Access**: `Window → Extensions → MisterHorse Product Manager`

**Requirements**: Windows 10+, Premiere Pro 2022+, .NET Framework 4.7.2+

---

## Quick Start

1. **Fonts**: Install from `_Consolidated/` → restart Premiere Pro → Essential Graphics
2. **LUTs**: Lumetri Color → Creative → Browse → `LUTs/`
3. **Transitions**: Effects panel → browse packages → drag to edit points
4. **Effects**: Import PSD via File → Import → place on timeline
5. **Mockups**: Open PSD in Photoshop → edit smart objects → import to Premiere
6. **Plugins**: Install MisterHorse → restart → Window → Extensions

---

## Round 2 — Adobe Creative Suite Taxonomy

Additional folder structure for Photoshop, Illustrator, After Effects, and cross-app assets.

```
X:/Work Drive/Resources/
|
+-- Graphics/                       — Illustrator & Photoshop assets
|   +-- Illustrator/                — .ai, .eps, .svg
|   |   +-- Icons/
|   |   +-- Illustrations/
|   |   +-- Logos/
|   |   +-- Patterns/
|   |   +-- Swatches/              — .ase color libraries
|   |   +-- Brushes/               — .ai brush libraries
|   +-- Photoshop/                  — .psd, .psb
|   |   +-- Templates/             — Social media, print templates
|   |   +-- Actions/               — .atn action sets
|   |   +-- Brushes/               — .abr brush sets
|   |   +-- Styles/                — .asl layer styles
|   |   +-- Patterns/              — .pat pattern files
|   |   +-- Gradients/             — .grd gradient maps
|   |   +-- Shapes/                — .csh custom shapes
|   |   +-- Overlays/              — Light leaks, textures (PNG/PSD)
|   +-- Shared/                     — Cross-app assets
|       +-- Color-Books/            — .ase, .aco swatch files
|       +-- Export-Presets/         — .epr, .xml export settings
|
+-- Motion-Graphics/                — MOGRTs, presets, scripts
|   +-- Premiere-Pro/               — .mogrt templates
|   |   +-- Titles/                 — Lower thirds, title cards
|   |   +-- Transitions/            — .mogrt transitions
|   |   +-- Callouts/               — Arrows, badges, labels
|   |   +-- Social-Media/           — Instagram, TikTok, YouTube layouts
|   |   +-- Infographics/           — Charts, progress bars, counters
|   |   +-- Kinetic-Type/           — Animated text templates
|   +-- After-Effects/              — .ffx presets, .jsx scripts
|   |   +-- Presets/                — .ffx effect presets
|   |   +-- Expressions/            — .jsx expression scripts
|   |   +-- Scripts/                — .jsx/.jsxbin automation
|   +-- Cross-App/                  — .mogrt usable in both PR & AE
|
+-- Projects/                       — Active & archived project files
|   +-- Premiere-Pro/
|   |   +-- Active/
|   |   +-- Archived/
|   |   +-- Templates/
|   +-- After-Effects/
|   |   +-- Active/
|   |   +-- Archived/
|   |   +-- Templates/
|   +-- Shared-Assets/
|       +-- Footage/                — Shared video clips
|       +-- Audio/                  — Shared music/SFX
|       +-- Graphics/               — Shared brand elements
|
+-- Extensions/                     — CEP & UXP plugins
|   +-- ZXP/                        — .zxp extension packages (CEP)
|   +-- UXP/                        — .uxp plugin packages (modern)
|
+-- Media/                          — Raw unprocessed assets
|   +-- Video/                      — .mp4, .mov, .mpeg
|   +-- Audio/                      — .wav, .mp3, .aac
|   +-- Images/                     — .jpg, .png, .tiff, .webp
|
+-- _Incoming/                      — Drop zone for new uncategorized files
```

### Round 2 Quick Start

| Task | Where | How |
|------|-------|-----|
| Install Illustrator brushes | `Graphics/Illustrator/Brushes/` | Window → Brush Libraries → Other Library |
| Load Photoshop actions | `Graphics/Photoshop/Actions/` | Window → Actions → Load Actions |
| Load Photoshop brushes | `Graphics/Photoshop/Brushes/` | Brush tool → picker → gear → Import Brushes |
| Import MOGRTs to PR | `Motion-Graphics/Premiere-Pro/` | Essential Graphics → Install Motion Graphics Template |
| Load AE presets | `Motion-Graphics/After-Effects/Presets/` | Effects & Presets → Import Presets |
| Run AE scripts | `Motion-Graphics/After-Effects/Scripts/` | File → Scripts → Run Script File |
| Install extensions | `Extensions/ZXP/` or `UXP/` | Use ZXP Installer or drag-drop .uxp |
| Drop new files | `_Incoming/` | Run `Scripts\ResourceIntake.ps1` to categorize |

### Workflow Scripts

| Script | Purpose |
|--------|---------|
| `Scripts/ResourceIntake.ps1` | Scan `_Incoming/`, auto-route files by extension/keyword |
| `Scripts/GenerateIndexes.ps1` | Regenerate RESOURCES-INDEX.md across all folders |

---

## Per-Folder Documentation

Every subfolder contains a `RESOURCES-INDEX.md` file documenting:
- **Contents** — What's inside (file names, counts)
- **Formats** — File types and their use
- **Usage** — How to use in Premiere Pro / video editing workflow
- **Notes** — Any special instructions or dependencies

Category-level folders also contain a `README.md` with:
- Directory structure overview
- Installation guides per app
- Naming conventions
- Best practices

Look for `RESOURCES-INDEX.md` in any folder for detailed inventory.

---

*Guide updated: August 17, 2026*
*Source: X:/Work Drive/Resources/*
*41 font families | 118 LUTs | 24+ transition packages | Effects, Mockups, Templates | Graphics | Motion Graphics | Projects | Extensions | Media*
