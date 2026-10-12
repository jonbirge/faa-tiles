# Community and openly licensed VFR charts

Research for the world-wide VFR tileset. Scope: community-made and openly
licensed products, as opposed to official national charts.

- Researched 2026-09-27, current AIRAC cycle **2609** (effective 2026-09-03 to
  2026-10-01).
- **The research was stopped early** by the session's usage limit. Part 1
  (OpenFlightMaps) is largely complete and measured. **Part 2 (every other
  source) was not reached**; its table holds recollection only, marked
  NOT CHECKED, and must not be relied on.
- Status words: *verified* means observed in this session with a real request
  or a file inspected with GDAL/pdfium. UNVERIFIED means inferred. NOT CHECKED
  means no request was made.
- No account was created, no form submitted, no terms accepted.

## Summary

| Source | Coverage | Format | Licence verdict | Overall |
| --- | --- | --- | --- | --- |
| OpenFlightMaps tile zips | 18 European regions | EPSG:3857 z/x/y PNG, z4-z11, 256 and 512 px | Redistribution of derived works allowed with attribution; text only found on the Wayback Machine | **USABLE WITH CAVEATS** |
| OpenFlightMaps PDF charts | 21 regions, 86 sheets, incl. South Africa and Namibia | Vector PDF over a raster basemap, A1, not georeferenced | Same | **USABLE WITH CAVEATS** (needs registration per sheet) |
| OpenFlightMaps MBTiles | 18 European regions | MBTiles, 256 and 512 px | Same | **NOT USABLE for the current cycle** (all 404 for 2609) |
| OpenFlightMaps GeoTIFF | none now | withdrawn after 2018 | n/a | **NOT USABLE** (no longer published) |
| OpenFlightMaps live tile API | as the tile zips | 512 px PNG/JPEG to z12 | No terms found; sponsor-operated | **NOT USABLE** (do not harvest) |
| Everything in Part 2 | - | - | NOT CHECKED | NOT CHECKED |

## 1. OpenFlightMaps

Publisher: open flightmaps association (OFMA), a not-for-profit. The licence
text gives a Salzburg address; the current About page gives Winterthur,
Switzerland. Site: <https://openflightmaps.org/> (rebuilt as a static Hugo site
on 2026-03-07; `www.` redirects to the bare domain).

### 1.1 Regions

Verified from the Downloads menu of the home page and from each region's
publication XML for cycle 2609. **21 regions.** The "XML code" is what the
download URLs and the publication service use, and it is not always the
two-letter prefix.

| Menu entry | XML code | URL path segment | 1:500k PDF sheets | Tile zips (2609) |
| --- | --- | --- | --- | --- |
| EB Belgium | EBBU | ebbu | 1 (EB-1) | yes |
| ED Germany | ED | ed | 8 (ED-1..ED-8) | yes |
| EF Finland | EFIN | efin | 7 (EF-1..EF-7) | yes |
| EH Netherlands | EHAA | ehaa | 2 | yes |
| EK Denmark | EKDK | ekdk | 1 | yes |
| EP Poland | EPWW | epww | 4 | yes |
| ES Sweden | ESAA | esaa | 6 | yes |
| **FA South Africa** | FA | fa | 8 (FA-1..FA-8), titled **1:1,000,000** | **no** |
| **FY Namibia** | FYWH | fywh | 1 (`fywh_gld_1000k`) | **no** |
| LD Croatia | LDZO | ldzo | 2 | yes |
| LF France | LF | lf | 14 (LF1..LF14) | yes |
| LG Greece | LGGG | lggg | 3 | yes |
| LH Hungary | LHCC | lhcc | 1 | yes |
| LI Italy | LI | li | 18 (LI-1..LI-18) | yes |
| LJ Slovenia | LJLA | ljla | 1 | yes |
| LK Czech Republic | LKAA | lkaa | 1 | yes |
| LM Malta | LMMM | lmmm | 2 (LM1, LM2) | **no** |
| LO Austria | LOVV | lovv | 1 (+ 55 aerodrome plates) | yes |
| LR Romania | LRBB | lrbb | 3 | yes |
| LS Switzerland | LSAS | lsas | 1 | yes |
| LZ Slovakia | LZBB | lzbb | 1 | yes |

Notes:

- **Outside Europe: South Africa and Namibia only**, both PDF only. South
  Africa's product is titled 1:1,000,000, not 1:500,000. Namibia's product is
  titled 1:500k but its single file is named `fywh_gld_1000k`; which scale it
  really is was NOT CHECKED (the file was not downloaded).
- Croatia's page lives at `/downloads/lb/` although LB is Bulgaria's prefix.
  Bulgaria appears in 2016 news posts as a published region but is **not** in
  the current menu. Whether any Bulgarian product still exists: NOT CHECKED.
- A 2016 post title mentions Romania together with Moldova. Whether the LR
  product covers Moldova: NOT CHECKED.
- Tile zips probed at the expected path for FA, FYWH and LMMM return 404, so
  the absence is real, not just an omission from the XML.

### 1.2 Products per region (cycle 2609)

Every region's XML has the same three sections.

| Section | Product | Notes |
| --- | --- | --- |
| Aeronautical Charts | VFR chart PDFs | one file per sheet, with basemap |
| Aeronautical Charts | VFR plates | Austria only, aerodrome plates, not enroute |
| Application Formats | "EPSG3857 Tiles" | two zips: `slippyTiles_clipped.zip`, `slippyTiles_original.zip` |
| Application Formats | "Mapbox Tiles" | two MBTiles: normal and `@2x` |
| Data | OFMX, ARINC424, OPENAIR, CUP | vector/aeronautical data, not raster charts |

What is **no longer** offered, established from historical XMLs for LSAS:

- **GeoTIFF**: listed as `geoTiff.zip` in cycles 1701 and 1801, gone from the
  XML by 1901. The old URLs for 1701, 1801 and 1812 now return 404, as do 2608
  and 2609. **There is no GeoTIFF product to download.** Its CRS therefore
  cannot be inspected; it sat in a directory named `epsg3857`, so Web Mercator
  is likely but UNVERIFIED. A 2016 post says the files were cut to under
  10,000 px a side, several per large country.
- **PDFs without basemap**: `<sheet>.pdf.zip` and `<sheet>_noBasemap.pdf.zip`
  were listed through 2401 and are absent from 2501 onward. For 2401 they still
  download (200; 81.8 MB and 10.2 MB for `ls1`). For 2609 the equivalent names
  return 404. Sheet names also changed (`ls1`, `ls2` became `ls-1`).

### 1.3 URL patterns and the AIRAC cycle

All downloads are on `snapshots.openflightmaps.org`, served through Cloudflare
from Google Cloud Storage, open, no key, `Accept-Ranges: bytes`,
`Access-Control-Allow-Origin: *`.

```
Publication index (XML), one per region and cycle:
  https://snapshots.openflightmaps.org/publicationServices/<XMLCODE>_<AIRAC>.xml
  e.g.  .../publicationServices/LSAS_2609.xml

Tile zips:
  https://snapshots.openflightmaps.org/live/<AIRAC>/tiles/<region>/noninteractive/epsg3857/slippyTiles_clipped.zip
  https://snapshots.openflightmaps.org/live/<AIRAC>/tiles/<region>/noninteractive/epsg3857/slippyTiles_original.zip

MBTiles:
  .../live/<AIRAC>/tiles/<region>/noninteractive/epsg3857/<region>_256.mbtiles
  .../live/<AIRAC>/tiles/<region>/noninteractive/epsg3857/<region>_256@2x.mbtiles

Chart PDFs:
  https://snapshots.openflightmaps.org/live/<AIRAC>/charts/<region>/<sheet>/latest/<sheet>.pdf
  e.g.  .../live/2609/charts/ed/ed-8/latest/ed-8.pdf
```

- `<AIRAC>` is the four-digit cycle id `YYNN` (2609 = ninth cycle of 2026).
  `<region>` is the XML code in lower case.
- **Discovering the current cycle.** Two ways, both verified:
  1. Compute it. The site's own script counts 28-day steps from 2003-01-23 and
     numbers them within the year.
  2. Read `<nearCycles>` in any region's XML, which lists the current and the
     three previous cycles with `startValidity` and `endValidity` timestamps.
     The XML must be asked for by cycle, so a script computes the cycle, asks
     for it, and falls back one cycle on 404.
- **Do not build sheet URLs by pattern; read them from the XML.** Sheet names
  are irregular (`ed-8`, `lf11`, `lm1`, `lr1`, `fywh_gld_1000k`).
- **A 404 here is an HTTP 404 with a 1,166-byte `image/png` body** dated
  2017-10-25. Check the status code; a length or content-type check on its own
  could mistake it for a small tile.
- The XML for a region code that does not exist (e.g. `EB_2609.xml` instead of
  `EBBU_2609.xml`) returns the same 404.
- Old cycles stay online: LSAS tile zips and MBTiles return 200 for 2401, 2501,
  2513, 2601, 2606, 2607 and 2608.

### 1.4 Verified requests (HEAD, 2026-09-27)

158 URLs from the 2609 XMLs were requested with `curl -sIL`. **122 returned
200, 36 returned 404**; the 36 are exactly the MBTiles.

Tile zips, all 200:

| Region | clipped zip (bytes) | original zip (bytes) | Last-Modified |
| --- | --- | --- | --- |
| ebbu | 155,511,998 | 175,008,343 | 24 Aug 2026 |
| ed | 1,088,460,154 | 1,156,925,250 | 26 Aug 2026 |
| efin | 708,821,600 | 723,264,117 | 29 Aug 2026 |
| ehaa | 244,148,114 | 266,972,506 | 24 Aug 2026 |
| ekdk | 259,431,427 | 278,022,805 | 24 Aug 2026 |
| epww | 628,265,864 | 657,785,147 | 29 Aug 2026 |
| esaa | 1,146,293,077 | 1,176,218,831 | 28 Aug 2026 |
| ldzo | 299,613,521 | 322,780,958 | 28 Aug 2026 |
| lf | 1,243,474,416 | 1,277,838,344 | 27 Aug 2026 |
| lggg | 295,788,816 | 300,420,733 | 27 Aug 2026 |
| lhcc | 225,512,192 | 257,145,394 | 27 Aug 2026 |
| li | 828,773,134 | 877,989,411 | 28 Aug 2026 |
| ljla | 156,083,857 | 175,624,874 | 27 Aug 2026 |
| lkaa | 332,867,469 | 360,509,902 | 27 Aug 2026 |
| lovv | 467,140,470 | 519,602,680 | 27 Aug 2026 |
| lrbb | 466,551,163 | 484,353,345 | 28 Aug 2026 |
| lsas | 244,720,372 | 273,148,852 | 27 Aug 2026 |
| lzbb | 193,033,453 | 220,194,957 | 27 Aug 2026 |
| **total** | **8.98 GB** | **9.50 GB** | |

Chart PDFs: **all 86 return 200**, `application/pdf`, 2.87 MB (`lm2`) to
105.2 MB (`lo-1`), **3.30 GB in total**. Last-Modified ranges from 20 Aug to
16 Sep 2026, so PDFs are re-rendered *within* a cycle (the path says `latest`)
while the tiles were built once, 24-29 Aug, about a week before the cycle took
effect.

MBTiles: **all 36 URLs listed for 2609 return 404.** The same files for 2608
all return 200 (e.g. `lsas_256.mbtiles` 29,491,200 bytes, `lsas_256@2x.mbtiles`
83,787,776; `ed_256@2x.mbtiles` 362,991,616; `lf_256@2x.mbtiles` 401,059,840).
Whether 2609's were never built or are late: UNVERIFIED. Either way a pipeline
must not depend on them. No MBTiles file was downloaded, so their internal
zoom range and tile format are NOT CHECKED.

### 1.5 What is inside a tile zip

Read from the zip central directories with HTTP range requests, for all 18
regions and both zips, without downloading the archives. Individual tiles were
then extracted the same way.

```
clip/<layer>/<size>/latest/<z>/<x>/<y>.png          (slippyTiles_clipped.zip)
original/<layer>/<size>/latest/<z>/<x>/<y>.png      (slippyTiles_original.zip)
original/merged/<size>/latest/metadata.json         (original zip only)
```

- **Three layers**: `aero` (the aeronautical overlay alone, **RGBA** with real
  transparency), `base` (the basemap alone), `merged` (both).
- **Two tile sizes**: `256` and `512`. The 512 set is the "@2x" rendering of
  the same z/x/y grid, not a different zoom.
- **Scheme is XYZ** (y counted from the top), Web Mercator, EPSG:3857.
  Verified by position: the Swiss tiles' x/y ranges convert to 5.45-10.55 E,
  45.46-48.11 N under the XYZ formula, matching the declared bounds.
- **Zoom range z4 to z11 in every region**, except France (z7-z11) and Greece
  (z5-z11). **Maximum zoom is 11.**
- **`base` and `merged` tiles are 8-bit palette PNGs** (256 entries), not RGB.
  Inside this repo that means RGB expansion before any resampling, the same
  rule the palette sectionals already follow.
- `metadata.json` holds name, cycle (`"version": "2609"`), description,
  `"format": "png"`, a lon/lat `bounds` string, and an attribution naming the
  open flightmaps association and its website.

**Native resolution.** A z11 tile spans 19,568 m of Mercator. At 512 px that is
**38.2 m per pixel in Mercator units, about 26 m on the ground at 47 N** --
the same pixel density as ordinary 256 px tiles at **z12**. The 256 px set is
half that (76.4 m, z11 proper). For comparison a 1:500,000 chart scanned at
300 dpi is 42.3 m/px, which is what the FAA sectionals are. So the 512 px set
is the one to use, and its natural home is **z12 in a 256 px pyramid**: each
512 px z11 tile splits exactly into four 256 px z12 tiles with no resampling.

Tile counts for `clip/merged/512`, all zooms, and at z11:

| Region | tiles | MB (uncompressed PNG) | z11 tiles |
| --- | --- | --- | --- |
| ebbu | 683 | 42.8 | 482 |
| ed | 5,198 | 338.4 | 3,801 |
| efin | 9,501 | 208.4 | 6,978 |
| ehaa | 1,639 | 66.0 | 1,179 |
| ekdk | 3,214 | 77.6 | 2,354 |
| epww | 4,094 | 190.2 | 2,995 |
| esaa | 13,574 | 366.4 | 10,034 |
| ldzo | 1,839 | 86.9 | 1,331 |
| lf | 7,815 | 381.1 | 5,768 |
| lggg | 3,664 | 99.5 | 2,667 |
| lhcc | 1,315 | 64.7 | 931 |
| li | 5,917 | 257.0 | 4,344 |
| ljla | 574 | 47.0 | 404 |
| lkaa | 1,424 | 104.9 | 1,036 |
| lovv | 1,571 | 150.1 | 1,114 |
| lrbb | 2,890 | 147.1 | 2,092 |
| lsas | 840 | 74.9 | 592 |
| lzbb | 883 | 59.4 | 624 |
| **total** | **66,635** | **2.76 GB** | |

Only about a third of each zip is the layer and size a build would use; the
rest is the other five layer/size combinations. Range requests against the
central directory can fetch just the wanted members, which was how the samples
here were taken.

Declared bounds (lon/lat, W S E N) from each `metadata.json`:

| Region | bounds |
| --- | --- |
| ebbu | 1.7694, 49.2847, 6.79, 51.7892 |
| ed | 5.5, 47, 15, 55 |
| efin | 18, 58.5, 32, 70.5 |
| ehaa | 1, 50, 8, 55 |
| ekdk | 5, 54, 16, 59 |
| epww | 14, 49, 25, 56 |
| esaa | 10, 54, 27, 70 |
| ldzo | 12, 41, 20, 47 |
| lf | -5.888672, 38.68551, 10.26123, 51.59072 |
| lggg | 18, 32.8333, 30.8333, 42 |
| lhcc | 16, 45.5, 23, 48.5 |
| li | 6.0418, 36.1942, 19.358, 47.506 |
| ljla | 13, 45, 17, 47 |
| lkaa | 12, 48, 19, 51.5 |
| lovv | 9, 46, 17.5, 49 |
| lrbb | 20, 43, 31, 49 |
| lsas | 5.5, 45.5, 10.5, 48 |
| lzbb | 16.5, 47.5, 23, 50 |

### 1.6 Overlap or abut

**Regions overlap; they do not abut.** The declared rectangles overlap widely
(Switzerland ends at 10.5 E, Austria starts at 9 E), and the tiles bear it out:
the Swiss and Austrian clipped sets share **162 of their z11 tiles**.

Each region draws the whole rectangle, neighbours' airspace included, from the
one shared database. Two shared z11 tiles were compared pixel for pixel:

| Tile (512 px, z11) | Opaque in both | Identical pixels | Differing by more than 32 levels |
| --- | --- | --- | --- |
| merged 1082/716 | 100% | 100% | 0% |
| merged 1078/718 | 100% | 74.4% | 7.7% |
| aero 1078/718 | 13.4% | 96.6% | 2.2% |

So the overlap is the same chart drawn twice, mostly but not always
identically. The cause of the differences (label placement or palette
quantisation) was NOT CHECKED. A paint-order rule is needed, but unlike the
FAA series the choice is nearly invisible.

"Clipped" against "original": the clipped zips are about 5% smaller, and a
clipped Swiss tile on the west edge is 29% transparent with a straight vertical
cut near 5.5 E, the declared bound. So clipping appears to be to the declared
**rectangle**, not to the FIR or national boundary. What exactly the original
set holds beyond that was NOT CHECKED.

**PDF sheets within a region also overlap.** The index diagram printed on
ED-8 shows Germany's eight sheets as overlapping rectangles. The amount was not
measured.

### 1.7 The PDF charts

One sample was downloaded and inspected: `ed-8.pdf` (Hamburg), 27,077,257
bytes, cycle 2609.

- One page, **840 x 594 mm (A1 landscape)**, produced by PDFsharp, titled as a
  VFR aeronautical chart at scale 1:500,000.
- **Vector**: 225,293 path objects and 704 text objects. **The basemap is
  raster**, four embedded 3181 x 2245 images at 144 dpi. So rendering at a
  higher scale sharpens the aeronautical layer and only enlarges the basemap.
- **No georeferencing at all.** No `VP`, `Measure`, `GPTS` or `LGIDict` entry
  in the file, and GDAL does not recognise it as a raster. Projection unknown;
  the sheet prints graticule ticks.
- **The sheet is not a clean map rectangle.** A title and legend panel is
  printed over the map's top-left corner and an aerodrome frequency table over
  the top-right, with a scale bar bottom-left. These would need masking, as the
  FAA sheets' collars do.
- A printed note says the chart is not to be used as a primary source of
  navigation.

Using the PDFs would mean registering every sheet by hand or by graticule
detection, per edition, then masking the panels. The tile zips already are what
that work would produce. **The PDFs matter only for Malta, South Africa and
Namibia**, which have no tiles.

### 1.8 The live tile service

The site's own map reads tiles from a different host:

```
https://nwy-tiles-api.prod.newaydata.com/tiles/{z}/{x}/{y}.png?path=<AIRAC>/aero/latest
https://nwy-tiles-api.prod.newaydata.com/tiles/{z}/{x}/{y}.jpg?path=<AIRAC>/base/latest
```

- 512 px tiles; `aero` is RGBA PNG, `base` is JPEG. Eight tiles were requested.
- **It goes one zoom deeper than the zips**: real content at z11 and z12
  (38-72 KB), and from z13 a 1,233-byte blank PNG.
- **It answers 200 for everything**, blank tiles included, so status alone says
  nothing about coverage.
- No terms of use, no `robots.txt` (404). The host belongs to a sponsor's
  infrastructure, and the OFMA legal notice reserves the right to cut off users
  to prevent abuse of sponsor-provided servers.
- **Verdict: NOT USABLE.** It is a live service behind a web page, not a
  published download. The zips are the offered bulk route. If z12 at 512 px is
  wanted, ask OFMA for it rather than harvest it.

### 1.9 Licence

**The licence text is no longer on the live site.** The new site links to no
licence, and `/license/`, `/licence/` and `/legal/` return 404. The old site
linked three PDFs under `/live/downloads/`, which now return 404 on all three
OFM hosts. They were read from the Wayback Machine:

| Document | Archived copy |
| --- | --- |
| General Users' License (7 pages) | <http://web.archive.org/web/20250406184228/https://www.openflightmaps.org/live/downloads/20150306-GUL.pdf> |
| Legal and Copyright Notice (4 pages) | <http://web.archive.org/web/20250413173513/https://www.openflightmaps.org/live/downloads/20150306-LCN.pdf> |
| Disclaimer (1 page) | <http://web.archive.org/web/20250130160422/https://www.openflightmaps.org/live/downloads/20150306-DC.pdf> |

The file names date the text to 2015-03-06. Whether it has been revised since:
UNVERIFIED. The current About and FAQ pages still describe the same licence in
the same terms.

**What it says.** It is modelled closely on the Open Database License: a
worldwide, royalty-free, non-exclusive licence covering copyright and the EU
database right, with "Produced Work" and "Derivative Database" defined as the
ODbL defines them. The deciding sentence, from section 3.1:

> "These rights explicitly include commercial use, and do not exclude any field of endeavour."

The granted rights list distribution and making available, by any means and in
any form. A map image made from the data is a Produced Work by the licence's
own definition.

**Conditions**, paraphrased:

1. **Attribution (4.2).** Anyone shown the work must be made aware that the
   OFM database was a source. The licence offers two example notices that
   satisfy this: one saying the work contains information from the open
   flightmaps database and giving the website, the other a one-line copyright
   notice naming open flightmaps contributors.
2. **Contribute alterations (4.3).** If you *alter the data*, the changes go
   back to OFMA within 15 days. Re-tiling an image alters no data.
3. **Let your users report alterations (4.4).** Applies only where your users
   can change the data. A tile viewer does not allow that.
4. **No sub-licensing, no further restrictions (4.5).**
5. Governed by Austrian law. A breach ends the licence automatically, with a
   route to reinstatement.

**Caveats that matter.**

- **The licence is for the database, and the tiles are a rendering.** The
  legal notice says the rendering software belongs to sponsors and is outside
  the licence, and the FAQ says rendered products such as plate packages are
  separately copyrighted and that an agreement with the copyright owner is
  advisable. Against that, OFMA's own release announcements describe charts,
  tiles and data together as published under its user licence, free for
  private and commercial use, and each tileset's `metadata.json` carries only
  an attribution line. **No licence file specific to the tiles or PDFs was
  found.** Which reading governs the rendered tiles is UNVERIFIED.
- **The basemap is not OFMA's.** The site's map credits OpenStreetMap
  contributors and NASA elevation data beside OFMA. OpenStreetMap data is ODbL
  and needs its own credit. Using the `aero` layer alone, over our own
  basemap, avoids carrying the OSM-derived layer at all.
- **The OFM logo needs permission** before it is displayed anywhere, by a
  separate 2016 policy statement.
- Part of the data derives from national AIPs via the European AIS Database,
  under an agreement between OFMA and EAD; copyright in those items stays with
  the national authorities. The licence does not cover rights in individual
  contents.

**Redistribution verdict.** Publishing derived tiles on a public,
non-commercial website **appears permitted**, given attribution to OFMA and,
if the basemap is kept, to OpenStreetMap contributors. It is not certain,
because the licence text is off the live site and nothing states the terms of
the rendered tiles directly. **Recommended before publishing: one email to
`info@openflightmaps.org`**, which the home page gives for licence requests,
asking them to confirm that the GUL covers the tile zips and to say which
attribution line they want.

### 1.10 Record

| Field | Value |
| --- | --- |
| Publisher | open flightmaps association (OFMA) |
| Coverage | 21 regions; tiles for 18, all European |
| Scale / zoom | charts 1:500,000 (South Africa 1:1,000,000); tiles z4-z11, 512 px equal to z12 |
| Format | PNG tiles in zip; MBTiles; vector PDF with raster basemap |
| Georeferencing | tiles EPSG:3857 XYZ; PDFs none |
| Edition / cycle | AIRAC, 28 days; tiles built about a week ahead; PDFs refreshed in-cycle |
| Discovery | compute the AIRAC id, or read `nearCycles` from the publication XML |
| Access | open, no registration, no key |
| Licence | OFMA General Users' License, Wayback copy only |
| Redistribution | appears permitted with attribution; confirm by email |
| Verdict | **USABLE WITH CAVEATS** |

### 1.11 Recommendation for the pipeline

1. Ingest `slippyTiles_clipped.zip`, layer `merged` or `aero`, size `512`.
2. Fetch only the wanted members by range request: 2.76 GB instead of 8.98 GB.
3. Treat each region as one already-warped source in EPSG:3857. No detection,
   no masks, no upsampling.
4. Expand the palette before compositing.
5. `max_zoom` **12** in a 256 px pyramid. Anything finer magnifies.
6. Pick a paint order for the overlaps; it will rarely show.
7. Skip MBTiles. Skip the PDFs unless Malta, South Africa or Namibia are
   wanted enough to register sheets by hand.

## 2. Other free raster VFR products

**NOT CHECKED. No request was made for anything in this section.** The
research was stopped before it began. The rows below are recollection from
general knowledge, recorded only so the next pass knows where to start. Every
cell is UNVERIFIED, including the licences, and none of it should drive a
decision.

| Source | Coverage | Format | Licence (recollection) | Overall | Key URL |
| --- | --- | --- | --- | --- | --- |
| openAIP | world-wide aeronautical data | vector data and a raster/vector tile API; an overlay, not an ICAO chart | recalled as CC BY-NC; tile API recalled as needing an API key, which needs an account | NOT CHECKED | <https://www.openaip.net/> |
| SkyVector | world-wide, own charts plus national ones | web tile service of a commercial product | recalled as prohibiting automated harvesting | NOT CHECKED; expected NOT USABLE | <https://skyvector.com/> |
| ForeFlight, Garmin Pilot, SkyDemon, Jeppesen | world-wide | in-app charts, subscription | commercial | NOT CHECKED; expected NOT USABLE (paid) | - |
| Open Glider Network | - | recalled as an aircraft tracking network, not a chart publisher | - | NOT CHECKED; expected not relevant | <https://www.glidernet.org/> |
| National aeroclub, glider or ultralight federation charts | - | - | - | NOT CHECKED | - |
| ICAO-style chart projects on GitHub | - | - | - | NOT CHECKED | - |
| Charts rendered by third parties from openAIP or OFM data | - | - | - | NOT CHECKED | - |

## 3. Left unfinished

- All of Part 2.
- Whether the 2609 MBTiles are late or abandoned.
- Zoom range and tile format inside an MBTiles file.
- What `slippyTiles_original.zip` holds beyond the clipped rectangle.
- The cause of pixel differences between two regions' renderings of one tile.
- The true scale of the Namibia sheet, and the projection of the PDF charts.
- Whether Bulgaria and Moldova are still covered.
- Whether the General Users' License has been revised since 2015, and whether
  it governs the rendered tiles. This one needs OFMA's answer, not more
  searching.

## 4. Working files

In the session scratchpad, beside this report, under
`C:\Users\jrbir\AppData\Local\Temp\claude\E--faa-tiles\73473049-9788-4c6b-b726-5c43b44ca519\scratchpad\research\`:

- `xml/` -- the 21 publication XMLs for 2609 and nine historical LSAS ones
  (plus some stale 404 bodies saved under wrong region codes, e.g.
  `EB_2609.xml`, which are PNG error pages, not XML)
- `ofm_urls.tsv`, `ofm_head.tsv` -- every product URL and its HEAD result
- `ofm_tilesets_2609.json` -- per-region tile counts and sizes by layer, size
  and zoom
- `licence/GUL.txt`, `LCN.txt`, `DC.txt` -- extracted licence text
- `samples/` -- `ofm_ed-8_2609.pdf`, its preview, and about twenty single tiles
- `zipdir.py`, `zipget.py`, `allregions.py` -- the range-request readers
