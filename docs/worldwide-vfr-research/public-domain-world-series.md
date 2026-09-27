# US military / NGA world aeronautical chart series as a free gap filler

Research date: 2026-09-27. Research was stopped early (session usage limit), so
some items are marked **NOT CHECKED**. Anything marked **UNVERIFIED** was
inferred or recalled rather than measured. Everything else below was measured
with real HTTP requests or read off downloaded sample sheets.

Working files (index CSVs, scripts, sample sheets) are in the session
scratchpad, not in the repo:

`C:\Users\jrbir\AppData\Local\Temp\claude\E--faa-tiles\73473049-9788-4c6b-b726-5c43b44ca519\scratchpad\research\`

| File | Contents |
| --- | --- |
| `ut_onc_sheets.tsv` | 270 ONC sheets at UT: name, URL, latest year, UT description |
| `ut_tpc_sheets.tsv` | 653 TPC files at UT (650 distinct sheet names), same columns |
| `onc_index_nyu.csv` | ONC sheet bounds (W,E,S,N), 218 rows / 212 sheets, from public NYU catalogue metadata |
| `tpc_index_nyu.csv` | TPC sheet bounds, 515 rows, same source |
| `jnc_index_nyu.csv` | JNC sheet bounds, 120 rows, same source |
| `gnc_index_nyu.csv` | GNC sheet bounds, 30 rows, same source |
| `tpc_index_mun.csv` | TPC index polygons' bounding boxes, 637 rows, Memorial University public feature service |
| `tpc_index_combined.csv` | Union of the two TPC indexes with producer group and an `at_ut` flag |
| `jog_index_scanned.csv` | JOG 1501 sheets with a scan link: **partial**, 2,000 of 3,869 rows |
| `samples\onc_e_2.jpg`, `onc_j_24.jpg`, `tpc_e-2a.jpg`, `tpc_m-26b.jpg` | the four sample sheets inspected |
| `gaps.py`, `rule_check.py`, `tpc_cross.py`, `parse_ut.py` | the analysis scripts |

## Summary table

| Series | Best free source | Sheets free | Format | Georeferenced | Scan age | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| ONC 1:1M | UT Perry-Castaneda Library | 270 | JPEG ~9250x6700, ~160 dpi effective | No | 1961-2001, mostly 1970s-80s | USABLE WITH CAVEATS |
| TPC 1:500k | UT Perry-Castaneda Library | 650 | JPEG ~9400x6800, ~158 dpi effective | No | 1966-2004, mostly 1980s-90s | USABLE WITH CAVEATS |
| JNC 1:2M | none complete | ~20 polar sheets only | NOT CHECKED | No | 1973-1982 | NOT USABLE |
| GNC 1:5M | none found | 0 | - | - | - | NOT USABLE |
| JOG-A 1:250k | UT + Univ. of Kansas, via a public index | 3,869 JOG scans linked (Air and Ground mixed) | NOT CHECKED | NOT CHECKED (Kansas files are KMZ) | 1961-2007 | USABLE WITH CAVEATS, patchy, low priority |

## Access note for the UT site

`maps.lib.utexas.edu` sits behind an Anubis proof-of-work challenge. A request
with a browser-like user agent gets the challenge page (HTTP 200, ~7.4 KB of
HTML, no chart links). A request with curl's own default user agent is served
the real page and the real files. Nothing was bypassed: the requests simply
identified themselves honestly as curl. `robots.txt` returns 404. A pipeline
should do the same, identify itself, and rate-limit; the site's operators
clearly do not want heavy automated traffic. This is a fragility to plan for.

---

## 1. ONC, Operational Navigation Chart, 1:1,000,000

### Source

- Index page: `https://maps.lib.utexas.edu/maps/onc/` (HTTP 200, 67,435 bytes).
- Sheet URL pattern:
  `https://maps.lib.utexas.edu/maps/onc/txu-pclmaps-oclc-8322829_{row}_{number}.jpg`
  with the row letter in lower case and underscores, e.g. `..._e_2.jpg`,
  `..._j_24.jpg`.
- Sheets available: **270 distinct files** (271 links, one duplicated).
- The series itself: catalogue metadata describes it as about 229 sheets in the
  commercially georeferenced set; UT holds more than that set does (see
  copyright below). A definitive series total was NOT CHECKED.

### HTTP verification (`curl -sIL`)

| Sheet | Region | Status | Content-Length | Type |
| --- | --- | --- | --- | --- |
| ONC E-2 | Europe | 200 | 21,176,362 | image/jpeg |
| ONC H-10 | Asia (Bangladesh, Burma, China, India) | 200 | 19,862,681 | image/jpeg |
| ONC D-13 | Canada | 200 | 17,348,577 | image/jpeg |
| ONC J-24 | Mexico | 200 | 15,475,154 | image/jpeg |
| ONC M-26 | South America | 200 | 10,678,395 | image/jpeg |

Last-Modified on all five is July 2011. UT's listed sizes run 6-48 MB, so the
whole series is roughly 4.5 GB (estimated from the listed sizes, not summed).

### Format and quality (two sheets downloaded and inspected)

- ONC E-2: JPEG, RGB, 9254 x 6688. ONC J-24: JPEG, RGB, 9254 x 6732.
- The files carry a 300 dpi tag, which is wrong. Measured on E-2, one degree of
  latitude (48N to 49N) spans 704 px, so the scan is **about 158 m per pixel,
  about 160 dpi** at 1:1,000,000.
- No geotransform, no CRS, no world file. EXIF says Photoshop CS5, 2011.
- Scans are of folded library copies: fold lines, library stamps, a barcode
  sticker and handwritten call numbers in the margin.
- Zoom this supports: 158 m/px is about z10 at the equator (z10 is 152.9 m) and
  between z9 and z10 at 50 degrees latitude. **Max zoom 9 or 10.**

### Edition dates

Latest year named in UT's description, 266 of 270 sheets carrying one:
range **1961 to 2001**. By decade: 1960s 16, 1970s 86, 1980s 135, 1990s 23,
2000s 6. The E-2 sample is edition 15, compiled April 1971, revised May 1972,
air information current through 6 June 1972.

### Coverage gaps

Tested by sampling Natural Earth 110m land on a 1-degree grid against sheet
bounds. **No real land gaps were found.** The test reported gaps in Canada and
Alaska between 68N and 72N, in southern Australia, and in New Zealand, but every
one traces to an index artefact (catalogue envelopes that stop at 68.28N for
C-9 to C-12, and bounds I had to estimate for 58 sheets), not to a missing
sheet: UT holds those sheets. Missing sheet numbers are open ocean. Treat the
"no gaps" result as likely, not proven.

---

## 2. TPC, Tactical Pilotage Chart, 1:500,000

### Source

- Index page: `https://maps.lib.utexas.edu/maps/tpc/` (HTTP 200, 149,657 bytes).
- Sheet URL pattern:
  `https://maps.lib.utexas.edu/maps/tpc/txu-pclmaps-oclc-22834566_{row}-{number}{quadrant}.jpg`
  lower case with a hyphen, e.g. `..._e-2a.jpg`, `..._m-26b.jpg`.
- Sheets available: **653 files, 650 distinct sheet names.** A few names are
  irregular and need special-casing: `F-16-D`, `N-12-B`, `G-18R`, and H-7B,
  H-8A and P-27D each listed twice.
- Union of every index I found is 663 sheet names; 13 are not at UT
  (BOSHZ, F-18B, H-10D, H-14A, H-14D, H-15D, M-13A, M-26A, N-12A, P-27B, Q-15D,
  R-13B, U-19C).

### HTTP verification

| Sheet | Region | Status | Content-Length |
| --- | --- | --- | --- |
| TPC E-2A | Europe (North Sea, UK, Netherlands) | 200 | 12,062,365 |
| TPC H-10A | Asia | 200 | 18,657,876 |
| TPC J-24A | Mexico | 200 | 14,711,239 |
| TPC M-26B | South America | 200 | 15,611,432 |
| TPC F-19A | Canada / US border | 200 | 24,922,227 |
| TPC D-12A | Canada (Yukon) | 200 | 21,470,537 |
| TPC D-13A | Canada | **404** | not held |
| TPC M-26A | South America | **404** | not held |

### Format and quality (two sheets downloaded and inspected)

- TPC E-2A: JPEG, RGB, 6739 x 9200 (portrait). TPC M-26B: 9462 x 6850.
- Same wrong 300 dpi tag. Measured on E-2A, half a degree of latitude spans
  690 px, so **about 80.6 m per pixel, about 158 dpi** at 1:500,000.
- Not georeferenced.
- Zoom this supports: z11 is 76.4 m at the equator. **Max zoom 10 or 11.**
- The printed map bleeds well past the nominal sheet limits. E-2A is nominally
  52N to 56N but its paper carries map up to roughly 58N (read off a thumbnail,
  UNVERIFIED to the degree). Useful: overlap can cover a missing neighbour.

### Edition dates

Range **1966 to 2004**, 644 of 653 carrying a year. By decade: 1960s 5,
1970s 41, 1980s 261, 1990s 306, 2000s 31. Noticeably newer than the ONCs.

### Coverage gaps (approximate, same 1-degree method)

Share of land cells with no TPC sheet at UT, by continent: Europe 0.1%,
Asia 0.8%, South America 8.9%, Africa 10.6%, Oceania 27.5%,
North America 30.4%.

Worst countries: Greenland 60%, Botswana 58%, Mauritania 53%, Central African
Republic 47%, Chile 46%, Ghana 43%, Canada 42%, Mali 42%, Republic of the
Congo 39%, Namibia 36%, Bangladesh 36%, Argentina 32%, Australia 30%
(partly an estimation artefact), Zimbabwe 24%, Mozambique 21%.

In plain terms: most of Canada has no TPC, nor does the Amazon interior
(M-26 A, C, D are absent), southern Chile and Argentina, or a band of the Sahel
and southern Africa. ONC is the only cover there.

---

## 3. Sheet grid rule, as far as derived

### Latitude bands (row letter)

Rows are 8 degrees of latitude, lettered from the north, skipping I and O.
Confirmed against the index bounds for every row listed:

| Row | Latitude | Row | Latitude |
| --- | --- | --- | --- |
| A | 80N-84N (index shows 84, not 88) | L | 0-8N |
| B | 72N-80N | M | 8S-0 |
| C | 64N-72N | N | 16S-8S |
| D | 56N-64N | P | 24S-16S |
| E | 48N-56N | Q | 32S-24S |
| F | 40N-48N | R | 40S-32S |
| G | 32N-40N | S | 48S-40S |
| H | 24N-32N | T | 56S-48S |
| J | 16N-24N | U | 64S-56S (UNVERIFIED, no index bounds) |
| K | 8N-16N | | |

### Longitude (sheet number)

Numbers run eastward from near the prime meridian. Sheet width depends on the
row, read off the index:

| Row | Width | Row | Width |
| --- | --- | --- | --- |
| A | 70 | G | 14 |
| B | 38 | H to Q | 12 (a few 13) |
| C | 26-28 | R | 14 |
| D | 22 (21 in Alaska, 18 at the east end) | S | 16 |
| E | 18 (16 over eastern Canada) | T | 18-20 |
| F | 16 | | |

Row origins in the eastern hemisphere, from the index: E-3 starts 16E, F-1
13W, G-1 10W, H-1 19W, J-1 24W, K-1 17W, L-1 18W, M-3 7E, N-3 6E, P-3 5E,
Q-4 13E, R-4 17E. Within a run, west edge = origin + width x (n - first).

**There is no closed formula for the whole series, and a program must use a
table.** Reasons, all observed in the index:

- The arithmetic does not carry across the Pacific. M-3 at 7E predicts M-24 at
  101W; it is actually 94W.
- Some sheets are shifted in latitude: K-0 is 10N-18N, F-22 is 43N-51N, M-29 is
  6S-2N, J-24 reaches south to 15.67N, G-21 stops at 33.1N.
- Sheets crossing the antimeridian are split into E and W parts in the index.
- US sheets in row G are staggered.

### TPC quadrants

A TPC is a quarter of its parent ONC: **A = north-west, B = north-east,
C = south-east, D = south-west** (clockwise from the north-west). Tested
against the index: the rule reproduces **420 of 472 sheets (89%)** to within a
quarter degree. The 52 exceptions are concentrated in rows F, G (13, mostly the
staggered US sheets), H, J and K, and at high latitudes where sheets are
irregular. Use the table for bounds and the rule only as a fallback.

### Projection

- **Lambert Conformal Conic, standard parallels 1 degree 20 minutes inside each
  band edge.** Read directly off ONC E-2 (band 48N-56N): standard parallels
  49 deg 20 min and 54 deg 40 min, convergence factor 0.78830. Applying the
  same rule to other bands is UNVERIFIED but is the series convention.
- TPC projection note: NOT CHECKED on the scan. Expected to match the parent
  ONC band (UNVERIFIED).
- Polar sheets (above 80 degrees): polar stereographic, UNVERIFIED.
- Neatlines are parallels and meridians, so a sheet's nominal limit is a
  rectangle in longitude/latitude, not in the projected CRS. Its top and bottom
  are arcs on the paper. Crop with a densified lon/lat cutline.
- Datum of the older sheets: NOT CHECKED. TPC E-2A's margin says its grid
  values are compatible with WGS except British National Grid references. At
  80-160 m per pixel a datum shift of a few hundred metres is 1-3 pixels.

### Machine-readable indexes that exist

| Index | Where | Access | Notes |
| --- | --- | --- | --- |
| ONC, TPC, JNC, GNC sheet envelopes | `github.com/OpenGeoMetadata/edu.nyu`, one JSON record per sheet, field `locn_geometry` | Public repository | Bounds of East View's georeferenced rasters. The rasters and the index shapefiles themselves are restricted to NYU. |
| TPC index polygons, 637 | ArcGIS Online feature service `TPC_Index`, owner QEII_MapRoom (Memorial University of Newfoundland) | Public, queryable | Includes producer and date for 128 sheets |
| TPC index, 509 | ArcGIS Online `TPC_MsuOwned` (Michigan State) | Public index, restricted rasters | Gives each raster's pixel size and bounds |
| JOG series 1501, 9,533 footprints | ArcGIS Online `World_JOG_1501`, owner cthiry (Colorado School of Mines) | Public; its licence text says no use constraints | 3,869 carry a link to a scan |
| UT clickable index maps | on the UT ONC and TPC pages | Public | HTML image maps in pixel space. NOT CHECKED. |

Gaps in the indexes: 58 of UT's 270 ONC sheets and 28 of its 650 TPC sheets
have no bounds in any index. I estimated them from TPC quadrants or by row
interpolation; those estimates are rough and some are plainly wrong where only
part of a sheet's quadrants exist (Q-12, M-16, N-17). They need reading off the
sheets.

---

## 4. Georeferencing: what it would take

Neither series is georeferenced at the free source. Per sheet:

1. Build the LCC CRS for the sheet's band from the rule above, central meridian
   at the sheet centre.
2. Identify at least four, preferably six to nine, graticule intersections in
   pixel space and fit an affine transform to projected coordinates. Residuals
   show paper distortion at the folds.
3. Mask to the nominal sheet limits from the index table, as a lon/lat cutline.
   The legend panel, margins and library stamps fall outside it. This matches
   the mask approach `cesiumtiles.mosaic` already uses.

Effort, as a judgement rather than a measurement:

- By hand, about 2-3 minutes a sheet: **ONC about 10-14 hours, TPC about
  25-35 hours.**
- Automated graticule detection is plausible (the graticule is printed, ticked
  and labelled at regular intervals) but is several days of development and
  will still need a review pass. Trust numbers over thumbnails, as with the
  sectional detectors.
- The Esri tile service (below) could serve as a visual cross-check of a
  finished ONC registration. It must not be used as a data source.

---

## 5. Copyright

This is the main caveat, and it is more serious than the hosting site's
listing suggests.

- **UT's position.** Its FAQ says most maps it serves are public domain and
  need no permission, asks for credit to University of Texas Libraries, and
  warns: "The U.S. Government may claim copyright outside of the U.S."
  (`https://maps.lib.utexas.edu/maps/faq.html`). It recommends that anyone
  republishing outside the US contact the publisher. Every sheet is listed as
  not for navigational use.
- **UT's producer labels are unreliable.** UT lists TPC E-2A as a US Defense
  Mapping Agency chart. The sheet itself says it was produced by Military
  Survey, UK Ministry of Defence, in 1996, and carries a Crown copyright notice
  dated 1996. That is not a US government work. Crown copyright in a published
  work runs 50 years, so to the end of 2046 (my reading, not legal advice).
- **How many sheets are affected.** NOT CHECKED sheet by sheet. The Memorial
  University index attributes 76 TPC polygons to the UK Ministry of Defence and
  31 to the Australian Department of Defence. Of UT's sheets, 71 match the
  UK-attributed names and 27 the Australian ones: about **98 of 650 TPC sheets,
  15%**. They cover the UK and North Sea, Scandinavia, central Europe, the
  Middle East and Arabian peninsula, Malaysia and Indonesia, and Australia.
  UT's copy of a sheet may be a different edition from Memorial's, so the
  imprint on each scan is the only reliable test.
- **ONC.** The E-2 sample is a US DMA chart reprinted for the UK Directorate of
  Military Survey; no copyright notice was seen in the parts inspected. The
  commercially georeferenced ONC set omits 59 sheets that UT holds, including
  E-1, E-2, D-1, the Middle East (H-5, H-6, J-6, J-7) and Australia. Esri
  describes its copy as excluding areas where charts are not publicly
  available. That omission pattern matches the UK and Australian co-produced
  sheets and is a strong hint, not proof, of which sheets carry restrictions.
- **NGA's own statement.** In the Federal Register of 18 November 2004 NGA
  announced it would withdraw aeronautical products, including the navigation
  and planning charts, from public sale, giving among its reasons the avoidance
  of intellectual property disputes with foreign agencies that supply
  host-nation data
  (`https://www.federalregister.gov/documents/2004/11/18/04-25631/`).
  Summaries of the outcome say US, Caribbean and South American charts were
  exempted. Read from search summaries; the notice itself was NOT CHECKED in
  full.
- **Georeferenced copies are all claimed.** Esri's service is marked copyright
  East View Cartographic. NYU's copies are East View's and restricted. Toronto's
  and Michigan State's are Land Info's and restricted by vendor contract to
  enrolled students and staff.

Practical reading: sheets with a US DMA, NIMA or ACIC imprint and no foreign
notice are US government works and free to use in the US. Sheets with a UK or
Australian imprint should be excluded unless cleared. **Every sheet's imprint
needs checking before it is published**, and since the repo and site are public
worldwide, UT's warning about claims outside the US applies.

---

## 6. JNC (1:2,000,000) and GNC (1:5,000,000)

- UT does not host them: `/maps/jnc/` and `/maps/gnc/` both return 404.
- University of Minnesota UMedia returned 20 JNC records, all polar or
  Antarctic sheets (JNC 108N to 125), dated 1973-1982, in its USGS Polar Maps
  collection. Its rights note says use may be governed by US and international
  copyright law. Whether 20 is the full count or a page limit was NOT CHECKED.
  File format and size NOT CHECKED.
- archive.org: two items with "jet navigation chart" in the title, none for
  GNC.
- ArcGIS Online account `nga_hurricane` has three public JNC PDFs covering the
  Caribbean. NOT CHECKED.
- Georeferenced sets exist (East View at NYU: 120 JNC records, 30 GNC) but are
  restricted. Their bounds are in `jnc_index_nyu.csv` and `gnc_index_nyu.csv`.
- Library of Congress: searches for both returned nothing relevant.

**Verdict: NOT USABLE.** No free set with world coverage was found. They would
add little anyway: 1:2M supports about z8 and 1:5M about z6-7, below what ONC
already gives.

---

## 7. JOG-A (Joint Operations Graphic, Air, 1:250,000)

Low priority and only partly examined.

- Index page: `https://maps.lib.utexas.edu/maps/jog/` (HTTP 200), linking 26
  regional directories (Afghanistan, Algeria/Tunisia, Burma, Central Africa,
  Chad, East Africa, Haiti, India, Indonesia, Iran, Iraq, Japan, Latin America,
  Libya, Madagascar, Nigeria, Pakistan, Russia, Saudi Arabia, Somalia, Southern
  Africa, Sudan, Syria, Vietnam, West Africa). Air and Ground editions are
  mixed; Haiti has separate Air and Ground indexes.
- The public `World_JOG_1501` index has 9,533 footprints, of which **3,869 link
  to a scan**. In the 2,000 rows I retrieved, hosts were the University of
  Kansas (`jogsmaps.dept.ku.edu`, 1,091, KMZ files, so possibly georeferenced)
  and UT (about 900), plus a handful at USGS and Michigan State. Only 34 of the
  2,000 URLs name themselves as Air editions.
- The index links use UT's old `www.lib.utexas.edu` host. Whether they still
  resolve was NOT CHECKED. No JOG sheet was downloaded, so format, pixel
  dimensions and dpi are NOT CHECKED.
- Dates, where the index gives one (234 of 2,000): 1961-2007, mostly 1960s and
  1970s.
- Copyright: the index flags 398 of 9,533 footprints as Crown copyright, 3 as
  French and 1 as Italian.
- archive.org has seven JOG-A items from the University of Alberta, sheets of
  Canada.
- Grid: sheet numbers follow the International Map of the World scheme, a
  hemisphere letter, a 4-degree latitude band letter, a 6-degree zone number,
  then a sub-sheet number, e.g. NO 35-06. From the index, NQ 35,36-06 is
  27E-30E, 66N-67N, so sheets are 1 degree tall and widen with latitude.
  Projection is Transverse Mercator (UNVERIFIED). The index polygons make the
  rule unnecessary.

**Verdict: USABLE WITH CAVEATS.** Coverage is patchy by country, editions are
the oldest of any series here, and Air sheets are a minority of what is
scanned. Georeferencing thousands of sheets is a large job unless the Kansas
KMZ files turn out to be usable. Not worth starting before ONC and TPC.

---

## 8. Leads checked and rejected

| Lead | Result |
| --- | --- |
| Esri `Specialty/World_Navigation_Charts` tile service | Live, Web Mercator, z0-z10, JPEG tiles, ONC only (over 200 charts). Marked copyright East View Cartographic, tile export disabled, under Esri's Master License Agreement, in mature support and due to retire March 2028. **Not usable as a source.** |
| NYU Spatial Data Repository | East View georeferenced ONC, TPC, JNC, GNC. Access restricted; the download URL returns a login page. Catalogue search returned 403 to curl. Metadata is public on GitHub. |
| University of Toronto Map and Data Library | 506 TPC GeoTIFFs, restricted to Toronto faculty, staff and students; copyright Land Info. |
| Michigan State University | 509 TPC GeoTIFFs, restricted by vendor contract. Public preview JPEGs at `https://archive.lib.msu.edu/maps/public/TPC/{SHEET}.jpg` exist (A02C 204,842 bytes, H10A 266,916 bytes) but are thumbnails. |
| archive.org | No ONC or TPC collection. A few JOG-A and JNC items. |
| Library of Congress | Searches for all five series returned nothing relevant. |
| loadmap.net | Request redirected to a `ww547.loadmap.net` address and returned 401. Appears parked or dead. Terms NOT CHECKED. |
| NOAA / NCEI | NOT CHECKED. |
| CADRG / ADRG public releases | None found by search. NOT CHECKED further. |
| UC Berkeley digital collections, Leventhal Map Center, UK Hydrographic Office archive | Surfaced by search as holding TPC. NOT CHECKED. |

---

## 9. Verdicts

**ONC: USABLE WITH CAVEATS.** Complete land coverage, free, one predictable URL
pattern. Caveats: not georeferenced (10-14 hours by hand), 25 to 60 years old,
tops out at z9-z10, UK and Australian co-produced sheets need excluding, and
the host discourages automated traffic.

**TPC: USABLE WITH CAVEATS.** Twice the resolution and newer, but with real
holes (Canada, Amazon, southern cone, parts of Africa) and about 15% of sheets
likely under Crown or Commonwealth copyright. 25-35 hours of georeferencing by
hand. Best used over ONC where it exists.

**JNC, GNC: NOT USABLE.** No free world set.

**JOG-A: USABLE WITH CAVEATS**, low priority, largely NOT CHECKED.

Suggested order if this goes ahead: ONC first as the world base (z0-z9), TPC
over it where held and cleared (to z10-z11), current national charts on top.
Before any bulk download, read the imprint on every sheet and build the
exclusion list.
