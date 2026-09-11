# LABEL-X — Rule Implementation Plan

Source of truth: `9_The_Legal_Metrology__Package_Commodities__Rules__2011.pdf`
(notified 7 March 2011, GSR 202(E); in force from 1 April 2011).

This plan paraphrases the supplied PDF for engineering purposes only. **The rule
engine's actual runtime logic must be built from the PDF text, not from this
paraphrase** — this document is a build plan and coverage tracker, not the legal
source of truth itself.

Known amending/withdrawing notifications referenced inside the PDF, which any
version-aware implementation must respect:

| Notification | Date | Effect |
|---|---|---|
| GSR 734(E) | 30.09.2011 | Extended the deadline (originally 31 Mar 2012) for using up old/non-compliant packaging material under Rule 6(6) |
| GSR 748(E) | 24.10.2011 | Several provisos **withdrawn or amended effective 01.07.2012** — see per-rule notes below |

Whenever the engine evaluates a package, it must resolve rule status **as of the
package's relevant date** (e.g. manufacture/packing date if known, else "today"),
not assume the original 2011 text is still unmodified.

---

## Status legend

- **Planned (MVP)** — build in the initial phases.
- **Planned (quantity phase)** — build once MVP declaration checks work.
- **Later/optional** — explicitly deferred per project brief; do not build until asked.
- **Not modeled** — procedural/administrative rules not suited to automated label
  screening (e.g. registration, penalties) — reference only.

---

## MVP core rules (declaration presence/format checks)

### Rule 3 — Applicability of Chapter II
**Status: Planned (MVP) — gatekeeper, not a finding-producing rule.**
Chapter II (Rules 4–23, the bulk of retail-package declaration requirements) does
**not** apply to:
- (a) packages containing more than 25 kg or 25 litre of a commodity — **except**
  cement and fertilizer sold in bags up to 50 kg, which remain covered;
- (b) packages meant for industrial or institutional consumers (as defined: entities
  buying directly from the manufacturer for their own institutional/industrial use —
  e.g. transport, airlines, railways, hotels, hospitals).

Engineering note: this must run **before** any other Chapter II rule fires. If
package weight/volume or industrial/institutional context can't be determined
confidently → NEEDS REVIEW, not an assumption of applicability.

### Rule 4 — Regulation for pre-packing and sale
**Status: Planned (MVP).**
No commodity may be pre-packed for sale/distribution/delivery unless the package
bears (or has affixed) all declarations required under the rules. A package sitting
undeclared inside the manufacturer's own premises is not itself a violation — only
packages that have left the premises must carry the declarations. (This context —
"is this package in trade" — is generally assumed true for a screened/purchased
sample, but is worth flagging as an assumption in the applicability engine.)

### Rule 5 — Standard package sizes (Second Schedule)
**Status: Planned (MVP) — "where appropriate", per project brief.**
Commodities listed in the Second Schedule (includes **Biscuits, Tea, Salt,
Cereals/Pulses**, and others) must be packed in one of the specified standard
quantities for that commodity, unless the package instead carries a
"non-standard size" declaration.
**⚠ Version note:** the proviso permitting the "non-standard size" declaration as an
alternative to a Second-Schedule quantity **stands withdrawn effective 01.07.2012**
(GSR 748(E)). Implementation must treat this as: for current-day screening, a
package in a Second-Schedule category is expected to match a listed standard
quantity; the escape-hatch declaration is no longer a valid substitute post
01.07.2012. If the withdrawal's practical effect is ambiguous for a given demo
category, prefer NEEDS REVIEW over asserting non-compliance.

### Rule 6 — Declarations to be made on every package
**Status: Planned (MVP) — the central declaration-presence rule.**
Sub-rule (1): every package must declare —
- (a) name & address of manufacturer, or manufacturer **and** packer if different,
  and importer for imported packages (with explanatory presumptions if
  "manufactured by"/"packed by" qualifiers are absent, and special handling when a
  brand owner is named as marketer);
- (b) common/generic name of the commodity (and per-product name/quantity for
  multi-product packages);
- (c) net quantity (standard unit of weight/measure, or count if sold by number);
- (d) month & year of manufacture/pre-packing/import;
- (e) retail sale price (MRP);
- (f) dimensions of the commodity, where size is relevant to more than one piece;
- (g) any other declaration required elsewhere in the rules.

Exemptions/carve-outs relevant to the MVP:
- Food articles are governed by the Prevention of Food Adulteration Act, 1954
  instead of sub-rule 6(1)(a)/(d) — this matters for Biscuits/Tea/Cereals/Pulses
  demo categories and should be modeled as a routing decision, not silently ignored.
- No manufacture-date declaration required for bidis/incense sticks, or 14.2 kg/5 kg
  domestic LPG cylinders marketed by a PSU.
- No MRP declaration required for bidis, or LPG cylinders priced under the
  Administrative Price Mechanism.
- Cosmetics fall under the Drugs and Cosmetics Rules, 1945 instead.
**⚠ Version note:** the proviso allowing month/year to be applied via rubber stamp
without overwriting **stands withdrawn effective 01.07.2012** (GSR 748(E)) — do not
treat a stamped, non-overwritten date as automatically compliant post that date.

Sub-rule (2): every package must also carry a consumer-complaint contact
(name/address/phone, and email if available).

Sub-rule (3)–(4): individual stickers cannot alter/create a required declaration,
**except** a sticker reducing MRP (which must not cover the original MRP);
stickers are fine for non-required declarations.

Sub-rule (6): unexhausted old packaging material could be used up to 31 Mar 2012
(deadline extended by GSR 734(E), 30.09.2011) provided declarations were corrected
via stamp/sticker/on-line printing — mostly historical for a present-day screening
tool, but relevant if a demo scenario involves old stock.

### Rule 7 — Principal display panel size/lettering
**Status: Planned (MVP), simplified for OCR-scale reasoning.**
Minimum numeral height for the quantity declaration depends on declared quantity
band (Table I: weight/volume in g/ml; Table II: length/area/number by PDP area),
with taller minimums when characters are blown/molded/embossed/perforated rather
than printed. Packages ≤5 cm³ may use a card/tape as the PDP. Doesn't apply where
another law already governs the same disclosure.
Engineering note: since bounding-box pixel height doesn't map directly to physical
mm without a size reference in the image, this rule is best implemented as a
**partial/heuristic check** (flag only clear violations where measurable) and
NEEDS REVIEW otherwise, rather than a strict pass/fail.

### Rule 8 — Where the declaration must appear
**Status: Planned (MVP).**
All required declarations must appear on the principal display panel, with the
quantity declaration kept clear of surrounding print by a margin (≥ numeral height
above/below, ≥ 2× numeral height left/right). Returnable soft-drink bottles may
show MRP on the crown cap and/or bottle as "MRP Rs...".

### Rule 9 — Manner of declaration
**Status: Planned (MVP).**
Declarations must be legible and prominent; MRP and net-quantity numerals must
contrastingly-colored against the background (waived for blown/molded glass/plastic
lettering, and hand-written declarations just need to be clear/unambiguous); no
declaration may require reading through a liquid commodity; an outer
wrapper/container must repeat all required declarations unless it's transparent and
the inner declarations are legible through it; declarations must be in Hindi
(Devanagari) or English (other languages may be added in addition).

### Rule 10 — Name & address of manufacturer, etc.
**Status: Planned (MVP).**
Every package must conspicuously show manufacturer's name/complete address, or
manufacturer **and** packer if different, and importer for imported goods.
Packages ≤5 cm³ may use a mark/inscription instead of a full address. Commodities
manufactured abroad but packed in India must also show the Indian
packer's/importer's details on the PDP. "Complete address" is defined (factory
postal address, or street/premises number + city/state or PIN code) sufficient to
locate the party.

### Rule 11 — General provisions on quantity declarations
**Status: Planned (MVP).**
Net quantity excludes wrapper/packaging weight. If a commodity's weight/measure
won't vary meaningfully with environment, the declared quantity must equal what the
consumer actually receives, with no "when packed" qualifier. Commodities with
negligible environmental variation must still declare quantity accounting for that
variation (no "when packed" wording). Only commodities in the **Third Schedule**
(all soaps, lotions, non-milk creams) may use "when packed" wording, for
commodities with genuinely significant environment-driven variation.

### Rule 12 — Manner of declaring quantity
**Status: Planned (MVP).**
Quantity must be declared in the unit(s) that give the consumer accurate, adequate
information. Default unit by commodity form (mass/length/area/volume/number),
**except** commodities listed in the **Fourth Schedule**, which have
commodity-specific unit rules (e.g. curd → weight; ready-made garments → number;
edible oil/vanaspati/ghee → weight or volume). Additional
dimension/number declarations required if weight/measure alone is insufficient.
No misleading qualifiers on quantity ("minimum", "not less than", "about",
"approximately", etc.).
**⚠ Version note:** sub-rule (6)'s wording on misleading qualifiers **was amended
effective 01.07.2012** (GSR 748(E)) to a broader formulation ("any word or
expression of any sort, whatsoever…"). The engine should apply the amended,
broader wording for current-day screening.

### Rule 13 — Statement of units
**Status: Planned (MVP).**
Governs which SI sub-unit/unit to use depending on the declared magnitude (e.g.
grams below 1 kg, kilograms at/above 1 kg; centimetres below 1 m, metres at/above;
millilitres below 1 L, litres at/above), prohibits count-words like "dozen"/"score"/
"gross", and requires SI units only (no imperial), with "N" or "U" as the symbol
for count-based items.

### Rule 26 — Exemptions
**Status: Planned (MVP) — gatekeeper, evaluated early alongside Rule 3.**
The whole rule set is exempted for:
- (a) packages of net weight/measure ≤10 g or ≤10 ml;
- (b) fast-food items packed by a restaurant/hotel and the like;
- (c) scheduled/non-scheduled drug formulations under the Drugs (Price Control)
  Order, 1995;
- (d) agricultural produce in packages above 50 kg.
**⚠ Version note:** a proviso requiring MRP + net-quantity declarations on packages
between 10–20 g or 10–20 ml (i.e., a partial carve-back into the exemption) **stands
withdrawn effective 01.07.2012** (GSR 748(E)) — for current-day screening, packages
in the 10–20 g/ml band fall under the plain ≤10 g/ml exemption boundary as
written, and the special partial requirement should **not** be enforced.

---

## Quantity-focused phase (build after MVP declaration checks work)

### Rule 19 — Inspection of quantity/error at manufacturer/packer premises
**Status: Planned (quantity phase) — model only the *evaluable* determinism, not the
inspection workflow.**
Defines the sampling and testing procedure Legal Metrology officers use at
manufacturing premises (sample size from the **Fifth Schedule**, test method from
the **Sixth Schedule**, results recorded on the **Seventh Schedule** form) and the
pass condition for a lot: sample average net quantity ≥ declared quantity, and no
individual sample's deficiency exceeds the Maximum Permissible Error (Rule 22 /
First Schedule). For LABEL-X (single-package image screening, not batch lot
testing), this rule is mainly relevant as the **definition of a compliant
quantity outcome** — the actual multi-package statistical sampling and fresh-test
procedures are out of scope for an image-based tool and are not modeled as
automated findings.

### Rule 21 — Inspection at wholesale/retail dealer premises
**Status: Planned (quantity phase), narrow scope.**
Governs when/how a dealer-premises quantity test may be triggered (complaint,
suspected tampering, missing declarations) and the "when packed" defense for
environmental deficiency. Relevant to LABEL-X mainly for the underlying quantity
check (declared vs. actual, deficiency vs. Rule 22 MPE) applied at the point of
sale rather than at the factory — same deterministic core as Rule 19's pass
condition, different trigger context. LABEL-X cannot itself weigh a package from an
image, so any "actual quantity" check depends on external measurement input, not
OCR — flag as NEEDS REVIEW unless an actual measured quantity is supplied.

### Rule 22 — Maximum Permissible Error (First Schedule)
**Status: Planned (quantity phase) — the deterministic core for any quantity-deficiency finding.**
Defines MPE as a lookup table:
- **First Schedule Table I** — MPE for weight/volume, banded by declared quantity
  (e.g. up to 50 g/ml: 9%; 50–100: 4.5 g/ml fixed; 100–200: 4.5%; … above 15,000:
  1.0%), rounded per the schedule's rounding rule.
- **First Schedule Table II** — MPE for length/area/number (e.g. length: 2% up to
  10 m then 1%; area: 4% up to 10 m² then 1%; number: 2% flat).

This table should be implemented as **data** (e.g. a lookup table in `rules/`),
not hardcoded conditionals, so it can be versioned like everything else. As with
Rule 21, actually computing "deficiency" requires an externally supplied measured
quantity — the rule engine validates the *comparison*, not the *measurement*.

---

## Later / optional (do not build without explicit instruction)

Rules 14–18 (dimension/sheet-count/container-shape declarations for specific
commodity classes), Rules 23–25 (deceptive packages, wholesale-package
declarations, export/import restrictions), Rules 27–31 (manufacturer/packer/importer
*registration* — an administrative process, not a label-content check), Rule 32
(penalties), Rule 33 (Central Government's power to relax rules), Rule 34
(repeal & savings vs. the 1977 predecessor rules).

## Not modeled as automated findings

- Rule 32 (penalties) and Rule 33 (power to relax) are legal/administrative
  provisions with no label-content signal to extract — reference only, never
  surfaced as a "finding."
- Registration-related Rules 27–30 concern manufacturer/packer paperwork with the
  Legal Metrology Directorate/Controller, not something visible on a package image.

---

## Schedules referenced by MVP rules

| Schedule | Used by | Contents relevant to MVP |
|---|---|---|
| First Schedule | Rule 22 (and 19/21) | MPE tables (Table I: weight/volume; Table II: length/area/number) |
| Second Schedule | Rule 5 | Standard pack sizes per commodity — includes Biscuits, Tea, Salt, Cereals/Pulses (all demo categories except Soap, which is not schedule-restricted to fixed sizes but does appear for the Rule 11/Third Schedule "when packed" allowance) |
| Third Schedule | Rule 11(4) | Commodities allowed the "when packed" qualifier — all soaps, lotions, creams (other than milk cream) |
| Fourth Schedule | Rule 12(2) | Commodity-specific unit-of-measure exceptions |
| Fifth/Sixth/Seventh Schedule | Rule 19 | Sampling manner, test method, and officer's data-sheet form — reference only, not modeled as automated findings |

## Demo category cross-reference

| Category | Second Schedule entry | Notes |
|---|---|---|
| Biscuits | Yes — 25g/50g/.../300g then 100g multiples up to 1kg | Food article → Rule 6 routes mfg-date/address rules through PFA Act instead |
| Tea | Yes — 25g/50g/100g/125g/250g/500g/1kg then 1kg multiples | Food article, same PFA routing note |
| Soap | Not Second-Schedule-restricted per se, but laundry/toilet/detergent-cake sizing bands exist informally in the schedule; falls under Third Schedule "when packed" allowance | Non-food — full Rule 6(1)(a)/(d) applies (no PFA carve-out) |
| Cereals/Pulses | Yes — 100g/200g/500g/1kg/2kg/5kg then 5kg multiples | Food article, PFA routing note |
| Salt | Yes — sub-50g in 10g multiples, then 50g up to 5kg then 5kg multiples | Food article, PFA routing note |

## Build order recommendation

1. Rule 3 + Rule 26 (applicability/exemption gatekeepers) — everything downstream
   depends on knowing whether Chapter II even applies to this package.
2. Rule 6 (the central declaration set) + Rule 10 (name/address specifics) +
   Rule 9 (manner/language) — the fields most demo categories will actually show.
3. Rule 5 (standard sizes, Second Schedule) — directly demoable against all five
   demo categories.
4. Rule 12 + Rule 13 (unit correctness) and Rule 11 ("when packed" eligibility) —
   needs Third/Fourth Schedule data tables.
5. Rule 7 + Rule 8 (PDP/lettering/placement) — treat as heuristic/partial given
   OCR-to-physical-size limitations; low priority relative to declaration presence.
6. Rule 22 (MPE table) + Rule 19/21 narrow scope — once a measured-quantity input
   path exists.

Each of these will get its own phase; do not implement multiple rules' engine code
in a single phase without checking `docs/PROJECT_STATUS.md` first.
