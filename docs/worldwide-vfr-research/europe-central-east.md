# World-wide VFR research: Central, Eastern and South-Eastern Europe

Official national sources of the ICAO 1:500 000 VFR chart (or the national
equivalent) that can be obtained **without payment**. Researched 2026-09-27.
OpenFlightMaps and other community charts are out of scope here.

Countries: Poland, Czech Republic, Slovakia, Hungary, Slovenia, Croatia, Bosnia
and Herzegovina, Serbia, Montenegro, North Macedonia, Albania, Kosovo, Greece,
Cyprus, Bulgaria, Romania, Moldova, Ukraine, Belarus, Estonia, Latvia,
Lithuania, Turkey, Georgia, Armenia, Azerbaijan.

## How to read this

- Every URL given with a status code and a byte count was requested on
  2026-09-27 with curl, the venv Python or GDAL's `/vsicurl/`. Anything not
  confirmed that way is marked **UNVERIFIED**.
- Nothing was logged into, registered for, accepted or submitted. Bot walls
  (Cloudflare challenge, Akamai, reCAPTCHA) were recorded, not worked around.
  For a scripted pipeline a bot wall is a finding in itself.
- **Licence statements are paraphrased**, each with the URL and the place the
  text sits. Only one is quoted verbatim (Slovakia, because it is the only
  permissive one). Read the source before relying on a paraphrase.
- The work was split: Poland, Czech Republic, Slovakia, Hungary, Slovenia,
  Croatia, the Baltic states, Kosovo and Azerbaijan were researched directly;
  the Western Balkans, the south-east and the eastern countries by helper
  agents, whose key URLs were then re-requested (Romania, Albania, Bosnia,
  Cyprus, Bulgaria, Moldova, Greece, Georgia all answered as they reported).
- **The venv's GDAL 3.13.3 cannot read PDFs** (its PDF driver is write-only
  here: "not recognized as being in a supported file format"). Georeferencing
  was read by inflating the PDF object streams and searching for `/Measure`,
  `/GPTS` and the WKT. A raw byte search for `/GPTS` finds nothing in most of
  these files, because the dictionary sits inside a compressed object stream.
  The pipeline would have to do the same, or gain a PDF-reading GDAL.

## Summary

| Country | Series | Scale | Format | Georeferenced | Licence verdict | Overall verdict | Key URL |
|---|---|---|---|---|---|---|---|
| Latvia | LGS VFR Aeronautical Chart ICAO, 1 sheet, 15th ed., WEF 03 SEP 2026 | 1:500 000 | PDF, fully vector, 15.4 MB | Yes, embedded (LCC, WGS84) | Unclear: AIP says copyright policy not applicable, sheet carries copyright marks | **USABLE WITH CAVEATS** | https://ais.lgs.lv/page/VFR_Suport |
| Estonia | EANS Aeronautical Chart ICAO "ESTONIA 2153 A", 1 sheet, 18 APR 2024 | 1:500 000 | PDF (vector, 22.6 MB) and TIFF (9705 x 6752, 250 dpi) | PDF yes (L-EST97 LCC); TIFF no | Prohibited without written consent | **USABLE WITH CAVEATS** | https://aim.eans.ee/en/vfr-chart |
| Romania | ROMATSA VFR Chart ICAO, 4 sheets, ed. 9.0, 11 JUN 2026 | 1:500 000 | PDF, vector over 150 dpi raster relief, 5-7 MB a sheet | Yes, embedded (LCC, WGS84) | Prohibited without permission | **USABLE WITH CAVEATS** | https://www.aisro.ro/publications/hartivfrv02.php |
| Slovakia | LPS SR VFR Manual web chart (overlay + 1:500 000 topographic base) | web tiles, z7-z14 | ArcGIS tile cache / WMTS, PNG, EPSG:3857 | Yes (it is a tile service) | Overlay: permitted with attribution and link. Base map: third-party copyright, unclear | **USABLE WITH CAVEATS** | https://gis.lps.sk/vfrm/index.html |
| Czech Republic | ANS CR Aeronautical Chart ICAO "PRAHA (2231-ABCD)", 1 sheet, WEF 19 MAR 2026 | 1:500 000 | PDF wrapping one raster, 300 dpi (36.7 MB) and 600 dpi (99.2 MB) | No | Prohibited without prior consent | **USABLE WITH CAVEATS** | https://aim.rlp.cz/ |
| Slovenia | Slovenia Control VFR aeronautical chart, 1 sheet + reverse, ed. 2026 | **1:250 000** | PDF, vector overlay on ~200 dpi raster, 14.0 MB | No | Prohibited without permission | **USABLE WITH CAVEATS** | https://aim.sloveniacontrol.si/aim/products/vfr-charts/ |
| Albania | Albcontrol Aeronautical Chart ICAO, 1 sheet, 01 OCT 2026 | 1:500 000 | PDF wrapping one 7015 x 9933 raster (A1, 300 dpi); also JPEG | Embedded but **wrong**; register from graticule | Prohibited without written permission | **USABLE WITH CAVEATS** | https://www.albcontrol.al/aip/ |
| Bosnia and Herzegovina | BHANSA VFR Chart with recommended VFR routes, 1 sheet, 03 SEP 2026 | 1:500 000 | PDF, vector overlay on raster base, 9.7 MB | No (projection and metric scale printed) | Prohibited without written permission | **USABLE WITH CAVEATS** | https://www.bhansa.gov.ba/en |
| Hungary | HungaroControl ICAO chart, single sheet and 34-page A4 atlas, data 17 APR 2025 | 1:500 000 | PDF, 68.5 MB (sheet), 94.7 MB (atlas); content not inspected | UNVERIFIED | **Explicitly prohibited** by a click-through licence | NOT USABLE as-is (licence) | https://ais-en.hungarocontrol.hu/vfrmanual/ |
| Cyprus | DCA Local VFR Chart (Local VFR Manual), 30 APR 2019 | labelled 1:500 000, drawn on A4 | Vector PDF, 1.2 MB | No | All rights reserved | NOT USABLE as ICAO chart; weak fallback | http://vrfmanual.dca.mcw.gov.cy/menu.html |
| Georgia | Sakaeronavigatsia Aeronautical Chart ICAO, 1 sheet, 2020 ed. | 1:500 000 | GeoTIFF and Geospatial PDF per AIP; no file reachable | UNVERIFIED | Unclear | NOT USABLE today (page says temporarily not available) | https://ais.airnav.ge/en/aeronautical-chart |
| Bulgaria | BULATSA Aeronautical chart, ed. 13.0, 14 MAY 2026 | 1:500 000 | PDF and KMZ per the app; not reachable | UNVERIFIED | Not visible | NOT USABLE (login) | https://b-flip.bulatsa.com/publications/aeronautical-chart |
| Croatia | Croatia Control VFR chart | UNVERIFIED | behind AIM Portal | UNVERIFIED | All rights reserved | NOT USABLE (registration and ordering) | https://aim.crocontrol.hr/ |
| Lithuania | Oro navigacija VFR Aeronautical Chart ICAO, 13th ed., 19 MAR 2026 (UNVERIFIED) | 1:500 000 | jpg, png, pdf, tif per search snippets | UNVERIFIED | Not seen | NOT USABLE (e-shop; every host behind a bot wall) | https://www.ans.lt/en/eshop/vfr-chart |
| Poland | PANSA Lotnicza Mapa Polski ICAO, 6 sheets | 1:500 000 | paper only | n/a | Prohibited without consent | NOT USABLE (paper, sold) | https://ais.pansa.pl/lotnicza-mapa-polski/ |
| Serbia | SMATSA Aeronautical Chart ICAO, 3 sheets, 22 JAN 2026 | 1:500 000 | paper, sold | n/a | Copyright reserved | NOT USABLE (12 EUR a sheet) | https://www.smatsa.rs/upload/aip/published/start_page.html |
| Montenegro | same SMATSA series (Part 3 Podgorica) | 1:500 000 | paper, sold | n/a | Copyright reserved | NOT USABLE (12 EUR a sheet) | same |
| North Macedonia | M-NAV: chart listed as NIL | 1:500 000 | not published | n/a | All rights reserved | NOT USABLE (does not exist yet) | https://ais.m-nav.info/eAIP/Start.htm |
| Kosovo | none: no VFR or 1:500 000 chart in GEN 3.2; ENR 6 "to be developed" | - | - | - | not stated | NOT USABLE (not published) | https://kans-ks.org/eAIP/default.html |
| Greece | HASP AIP Greece; no 1:500 000 chart in ENR 6 | none found | PDF eAIP | n/a | Not seen | NOT USABLE (Akamai 403 + reCAPTCHA) | https://aisgr.hasp.gov.gr/ |
| Moldova | MoldATSA "VFR charts" section (content unknown) | UNVERIFIED | UNVERIFIED | UNVERIFIED | Not seen | NOT USABLE (bot wall, then sign-in) | https://aim.moldatsa.md/ |
| Turkey | DHMI AIP; HGM special air chart, JOG-A, TFC | 1:500 000, 1:250 000 | HGM GeoTIFF, 300 dpi | HGM yes, sold | Paid, reuse fees | NOT USABLE (paid) | https://www.harita.gov.tr/urun/1500000-olcekli-raster-turkiye-ozel-hava-haritasi/27 |
| Ukraine | UkSATSE Aeronautical chart (ANC), 8 sheets | 1:500 000 | PDF / ISO, behind login | UNVERIFIED | All rights reserved | NOT USABLE (paid, login) | https://www.aisukraine.net/titul_en.php |
| Belarus | none listed in AIP GEN 3.2; AIP VFR is paid | - | - | - | Unclear | NOT USABLE (paid, login) | https://www.ban.by/ru/sbornik-aip/amdt |
| Armenia | ARMATS Aeronautical Chart ICAO | 1:500 000 | purchase only, assume paper | UNVERIFIED | Not granted | NOT USABLE (purchase only) | https://armats.am/en/category/eaip/ |
| Azerbaijan | unknown: no public official AIP found | - | - | - | - | NOT USABLE on current evidence | https://www.caa.gov.az/ |

### What this adds up to

- **Eight countries give the chart away as a file, and one as tiles**: Latvia,
  Estonia, Romania, Czech Republic, Slovenia (1:250 000), Albania, Bosnia and
  Herzegovina, Hungary (file), Slovakia (tiles).
- **Three are already georeferenced vector PDFs** and need no registration
  step at all: Latvia, Estonia, Romania. They fit the existing
  `render_pdfs.py` approach (draw from vector at the scale the zoom needs),
  with the affine read from the PDF instead of registered against a GeoTIFF.
- **Licence is the real obstacle, not format.** Only Slovakia states that its
  data may be reused (with attribution and a link), and only for its own
  layers. Latvia states no policy. Every other free source reserves
  reproduction to itself and asks for prior permission; Hungary's licence
  forbids publication in so many words. A public tileset built from these
  needs written permission from each publisher. The contacts are in the
  sections below.
- **No free official source**: Poland, Croatia, Serbia, Montenegro, North
  Macedonia, Kosovo, Greece, Bulgaria, Moldova, Ukraine, Belarus, Lithuania,
  Turkey, Georgia (for now), Armenia, Azerbaijan. What was checked for each is
  listed in its section so it is not researched twice.
- **No country in this region publishes a free 1:1 000 000 VFR chart.** The
  only 1:250 000 national sheet is Slovenia's; Turkey's 1:250 000 series are
  sold.

### Samples kept

In `scratchpad/research/samples/` (one per source, all under 100 MB):

| File | Bytes |
|---|---|
| `lv_VFR_Chart_15th_edition_03SEP2026.pdf` | 15,408,182 |
| `ee_VFR_2024_chart_map_2024_web.pdf` | 22,635,230 |
| `cz_2026_ICAO_300.pdf` | 36,652,692 |
| `si_VFR_chart_2026_front.pdf` | 14,005,110 |
| `ro_2026_06_11_LRSE_ED9.pdf` | 5,262,566 |
| `al_aeronautical_chart_01OCT2026.pdf` | 17,448,948 |
| `ba_vfr_karta_3sep2026.pdf` | 9,736,615 |
| `cy_VFR_CHART_LCCC.pdf` | 1,184,955 |
| `sk_vfrm_z10_composite.png`, `sk_vfrm_z11_composite.png` | eight 256 px tiles each, composited |

Hungary was **not** sampled: its terms say that downloading is acceptance.

---

# Part 1 - Sources that publish a free file or service

## Latvia

**Publisher and series.** SJSC "Latvijas gaisa satiksme" (LGS), Aeronautical
Information Service. "VFR Aeronautical Chart - ICAO 1:500 000", sheet "LATVIA
2153 DC". **One sheet**, all of Latvia with margins of Estonia, Lithuania,
Russia and Belarus and the Baltic coast. AIP GEN 3.2 lists no 1:250 000 or
1:1 000 000 VFR series.

**URLs (verified).**

| What | URL | Status | Bytes |
|---|---|---|---|
| Index page | https://ais.lgs.lv/page/VFR_Suport | 200 | 26,447 |
| Current issue | https://ais.lgs.lv/uploads/fck/file/VFR%20charts/VFR_Chart_15th_edition_03SEP2026.pdf | 200, application/pdf, Last-Modified 22 Jul 2026 | 15,408,182 |
| Next issue | https://ais.lgs.lv/uploads/fck/file/VFR%20charts/VFR_Chart_15th_edition_29OCT2026.pdf | 200, Last-Modified 03 Sep 2026 | 15,337,332 |
| eAIP index | https://ais.lgs.lv/aiseaip | 200 | 29,967 |
| eAIP GEN 3.2 | https://ais.lgs.lv/eAIPfiles/2026_003_03-SEP-2026-Non-AIRAC/data/2026-09-03/html/eAIP/EV-GEN-3.2-en-GB.html | 200 | 68,891 |
| eAIP GEN 0.1 | same folder, `EV-GEN-0.1-en-GB.html` | 200 | 15,889 |

**Format (sample inspected).** PDF 1.6, one page, 3996.7 x 1760.3 pt =
**1410 x 621 mm**. **Fully vector**: 1,108,249 paths, 9,289 text runs, and
only two small images (700 x 1200 and 820 x 565, cover art). The page holds the
title panel and legend on the left, the map, tables below and an inset, so the
map has to be cropped to its viewport.

**Georeferenced: yes**, ISO 32000 geospatial PDF exported from ArcGIS, inside a
compressed object stream.

- CRS (WKT "WGS_1984_Lambert_Conformal_Conic"): Lambert Conformal Conic, WGS84,
  central meridian 24.0, standard parallels 55.3333 and 58.6667, latitude of
  origin 57.0, false easting 500000, false northing 6375000, metres.
- **Three viewports.** `GPTS` (lat lon) of each:
  - 55.30087 17.26376 / 58.07456 16.74582 / 58.1922 28.72422 / 55.41013 28.38561
    - the main map;
  - 53.70752 18.37062 / 59.77276 17.37788 / 59.77363 30.60443 / 53.70826 29.61431
    - a small-scale overview panel;
  - 57.91574 20.44562 / 58.5477 20.38267 / 58.57498 21.55892 / 57.94255 21.60145
    - an inset.
  A script must choose the viewport by its page area, not take the first.

**Edition, cycle, discovery.** 15th edition; the digital issue is re-released
with each change (WEF 03 SEP 2026 current, WEF 29 OCT 2026 already posted as
"next"). The page says changes listed in GEN 3.2.8 are drawn only into the
digital version and that each new digital issue invalidates the previous one.
The paper edition is dated 14 MAY 2026 in GEN 3.2. **Script discovery:** parse
the index page for `uploads/fck/file/VFR charts/VFR_Chart_*_edition_<DDMMMYYYY>.pdf`
and take the newest date that is not in the future; the page labels them
"CURRENTLY EFFECTIVE" and "NEXT ISSUE". The file name is not predictable.

**Access.** Open. No login, no click-through. (The site's login is for its data
submission and distribution tools, not for this page.)

**Licence.** No terms-of-use page was found on ais.lgs.lv. The AIP's copyright
section (GEN 0.1 section 5, URL above) states that a copyright policy is not
applicable. The chart itself carries two copyright marks, LGS and the Latvian
Geospatial Information Agency (the base map). The paper chart is sold through
the map shop Jana seta. Redistribution of derived tiles: **unclear** - nothing
forbids it and nothing grants it. Contact: ais@lgs.lv.

**Verdict: USABLE WITH CAVEATS.** Technically the best source in the region
with Estonia: free, open, current to the AIRAC cycle, vector and georeferenced.
The caveat is that reuse is not addressed; ask LGS.

## Estonia

**Publisher and series.** Estonian Air Navigation Services (EANS / Lennuliiklus-
teeninduse AS) publishes the digital chart; the Estonian Transport
Administration sells the paper one. "Aeronautical Chart - ICAO 1:500 000",
"ESTONIA 2153 A". **One sheet** plus a separate legend sheet. No 1:250 000 or
1:1 000 000 VFR series; the other ENR 6 charts are 1:2 000 000 index charts.

**URLs (verified).**

| What | URL | Status | Bytes |
|---|---|---|---|
| Index page | https://aim.eans.ee/en/vfr-chart (Estonian: `/et/vfr-kaart`) | 200 | 55,442 |
| Chart PDF | https://aim.eans.ee/sites/default/files/forms/aim_published_vfrchart/VFR_2024_chart_map_2024_web.pdf | 200, Last-Modified 07 May 2024 | 22,635,230 |
| Legend PDF | .../aim_published_vfrchart/VFR_legend_2024_web.pdf | 200 | 3,178,313 |
| Chart TIFF | .../aim_published_vfrchart/VFR_2024_chart_map_2024_web_0.tif | 200, image/tiff, Last-Modified 25 Jun 2024 | 26,249,800 |
| Legend TIFF | .../aim_published_vfrchart/VFR_legend_2024_web_1.tif | 200 | 11,682,346 |
| Copyright page | https://aim.eans.ee/en/copyright | 200 | 53,188 |
| eAIP GEN 3.2 | https://eaip.eans.ee/2026-08-06/html/eAIP/EE-GEN-3.2-en-GB.html | 200 | 72,760 |
| eAIP ENR 6 | https://eaip.eans.ee/2026-08-06/html/eAIP/EE-ENR-6-en-GB.html | 200 | 6,163 |

The chart is **not in the eAIP** (ENR 6 has seven small-scale charts). GEN 3.2
only mentions the paper chart, at 20.00 EUR from the Transport Administration;
the free digital files are on the AIM site alone, which is why a first pass
through the eAIP misses them.

**Format.**

- **PDF** (sample inspected): PDF 1.6, one page, 2795.0 x 1944.6 pt =
  **986 x 686 mm**. Vector: 147,869 paths, 5,194 text runs, 28 small images
  (symbols, the largest 1947 x 538). **Georeferenced**, one viewport.
  CRS WKT "Estonia_1997_Estonia_National_Grid" (L-EST97, EPSG:3301): Lambert
  Conformal Conic, GRS80, central meridian 24.0, standard parallels 58.0 and
  59.3333, latitude of origin 57.5176, false easting 500000, false northing
  6375000. `GPTS` 57.27335 20.12429 / 60.27484 19.77484 / 60.26454 28.54225 /
  57.26389 28.16671. The page notes that the PDF holds vector data and
  georeferencing and therefore opens slowly in a browser.
- **TIFF** (header read over `/vsicurl/`, not downloaded): 9705 x 6752 px,
  250 dpi, CMYK source with alpha, DEFLATE, striped. **No georeferencing**
  (pixel corner coordinates only). Use the PDF.

**Edition, cycle, discovery.** Date of aeronautical information 18 APR 2024.
No fixed cycle is stated; corrections since then are listed in GEN 3.2 section
8 (aerodromes, obstacles and areas added or removed) and are **not** drawn into
the file, so the chart is two years behind in places. The index page gives a
CRC for each file (chart PDF 14FD8438). **Script discovery:** parse the index
page for `aim_published_vfrchart/*chart_map*.pdf`; the name carries the year
and Drupal adds `_0`, `_1` suffixes to re-uploads, so it cannot be constructed.

**Access.** Open. The site has a login, not needed here.

**Licence.** https://aim.eans.ee/en/copyright: all rights reserved to EANS; the
information may be used for informative or operational purposes with the
copyright notice displayed; any other use needs EANS's prior written consent.
eAIP GEN 0.1 section 6 says the same of the AIP. Redistribution of derived
tiles: **prohibited without written consent**. Contact: aip@eans.ee.

**Verdict: USABLE WITH CAVEATS.** Free, open, vector, georeferenced. Caveats:
written consent needed to publish; 2024 data with known corrections pending.

## Romania

**Publisher and series.** ROMATSA, Aeronautical Information Management Unit,
site `aisro.ro`. "VFR Chart - ICAO" 1:500 000, **four sheets**: LR-NW, LR-NE,
LR-SE, LR-SW (file codes LRNV, LRNE, LRSE, LRSV). Other VFR scales: 1:300 000
"NAPOC TMA VFR Routes" (ENR 6-70) and aerodrome Visual Operations Charts. No
1:250 000 or 1:1 000 000 VFR chart.

**URLs (verified).**

| URL | Status | Bytes |
|---|---|---|
| https://www.aisro.ro/publications/hartivfrv02.php (current index) | 200 | 6,576 |
| https://www.aisro.ro/files/hartivfr/2026_06_11_LRNE_ED9.pdf | 200 | 6,683,731 |
| https://www.aisro.ro/files/hartivfr/2026_06_11_LRNV_ED9.pdf | 200 | 6,372,602 |
| https://www.aisro.ro/files/hartivfr/2026_06_11_LRSE_ED9.pdf | 200 | 5,262,566 |
| https://www.aisro.ro/files/hartivfr/2026_06_11_LRSV_ED9.pdf | 200 | 6,522,015 |
| https://www.aisro.ro/files/hartivfr/2025_04_17_LR_ENR_6_70_en.pdf (1:300 000) | 200 | 4,739,202 |
| https://www.aisro.ro/aip/aip.php (points at the current eAIP) | 200 | 665 |
| https://www.aisro.ro/aip/2026-09-03/DOCS/AIP/GEN/GEN3/LR_GEN_3_2_en.pdf | 200 | 723,233 |
| https://www.aisro.ro/disclaimer/disclaimerv01.php | 200 | 6,704 |

Stale page to avoid: `publications/hartivfr.php` (200, 5,539 bytes) is the 2017
index and links Edition 1 files such as `files/harti/LR_SE_ED1e.pdf`
(7,069,150 bytes, 2017). A web search returns those first.

**Format (sample LRSE inspected).** PDF 1.7, 2 pages, each 2738.2 x 1870.5 pt =
966 x 660 mm; page 1 is the chart, page 2 the reverse. Page 1: 9,888 paths,
2,311 text runs, 141 images that are strips 4771 x 28 px, i.e. one 4771 x 3948
raster cut into bands - the relief and topographic base, about **150 dpi**
across the 808 mm map frame. Line work, names and graticule are vector.

**Georeferenced: yes**, ISO 32000 geospatial PDF in a compressed object stream.
CRS (WKT named "CAA"): Lambert Conformal Conic, WGS84, standard parallels
44.666666 and 47.333333, central meridian 25.0, latitude of origin 43.0, false
easting 500000, false northing 0. Main map viewport
`BBox [421.46 1842.18 2711.67 70.76]` pt with `GPTS` 43.73975 25.41338 /
46.55183 25.43454 / 46.41193 30.69407 / 43.60668 30.41773. **Three viewports**
in the file (main map, the locator inset, one on page 2): take the largest on
page 1.

**Edition, cycle, discovery.** Edition 9.0/2026, file date 11 JUN 2026. Roughly
annual; no cycle stated. File names carry date and edition
(`YYYY_MM_DD_LR(NE|NV|SE|SV)_ED<n>.pdf`), so parse `hartivfrv02.php`; the index
page name has itself changed once, so resolve it from `start_left.php` by the
link text "VFR Charts". The sheets are **not** inside the eAIP's ENR 6.

**Access.** Open; plain curl works.

**Licence.** No licence page. The deciding text is printed on the chart, beside
a ROMATSA copyright line: ROMATSA's permission must be obtained before the
chart is reproduced. GEN 3.2 prices the printed sheet at 5 EUR. Base data is
credited to AIGA, USGS, Esri Romania, OpenStreetMap and EuroGeographics.
Redistribution of derived tiles: **prohibited without permission**. Contact:
ais@aisro.ro.

**Verdict: USABLE WITH CAVEATS.** Free, open, scriptable, vector, georeferenced
and covering the largest area of any source here. Caveats: permission needed;
relief base only 150 dpi.

Also checked: Romanian CAA https://www.caa.ro/ (200, 43,029) - nothing.

## Slovakia

**Publisher.** Letove prevadzkove sluzby Slovenskej republiky, s.p. (LPS SR).

**What is free.** Not a chart file but a **public tile service**: the "VFR
Manual" web application, an ArcGIS Web AppBuilder site whose map is an
aeronautical overlay over a topographic base taken from the Slovak ICAO
1:500 000 chart. One service description says so directly: the topographic
basemap is based on the topographic layer of the ICAO ANC chart 1:500 000.

**URLs (verified).**

| What | URL | Status | Bytes |
|---|---|---|---|
| Web application | https://gis.lps.sk/vfrm/index.html | 200 | 6,306 |
| Application config | https://gis.lps.sk/vfrm/config.json | 200 | 19,155 |
| Web map item (public) | https://gis.lps.sk/arcgis/sharing/rest/content/items/81b2bf20907146eeac2c0857046e5de7?f=json | 200 | 920 |
| Web map layers | .../items/81b2bf20907146eeac2c0857046e5de7/data?f=json | 200 | 14,545 |
| Service directory | https://gis.lps.sk/server/rest/services?f=json | 200 | - |
| Overlay service | https://gis.lps.sk/server/rest/services/VFRM/VFRM_cache/MapServer?f=json | 200 | 3,999 |
| Base service | https://gis.lps.sk/server/rest/services/basemaps/VFRM_basemap/MapServer?f=json | 200 | 3,784 |
| WMTS capabilities | https://gis.lps.sk/server/rest/services/VFRM/VFRM_cache/MapServer/WMTS/1.0.0/WMTSCapabilities.xml | 200 | 21,508 |
| Example tile | https://gis.lps.sk/server/rest/services/VFRM/VFRM_cache/MapServer/tile/10/352/566 | 200, image/png, ETag, `Cache-Control: public, max-age=86400` | 15,622 |
| Example base tile | https://gis.lps.sk/server/rest/services/basemaps/VFRM_basemap/MapServer/tile/10/352/566 | 200, image/png | 184,384 |

**Services and zoom levels** (all EPSG:3857 / wkid 102100, 256 px tiles,
origin -20037508.34, 20037508.34 - the ordinary web scheme, so ArcGIS
`tile/{z}/{y}/{x}` maps straight onto `z/x/y`):

| Service | Content | Declared scales | Tiles observed |
|---|---|---|---|
| `VFRM/VFRM_cache` | aeronautical overlay, transparent PNG | z7 to z17 | z7-z14 return content over Bratislava; empty 190-byte tiles where nothing is drawn |
| `basemaps/VFRM_basemap` | topographic base (copyright TOPU, LPS SR), PNG32 | z10 to z13 | z10-z13: 200; z7-z9 and z14: 404 |
| `VFRM/VFRM_topo` | topographic base from the ICAO 1:500 000 chart | z9 to z11 | z9-z11: 200; z8, z12: 404 |
| `VFRM/VFRM_service` | combined rendering | z7 to z11 | z8-z11: 200 with content |

Full extent of the overlay: x 1836407..2525029, y 6011309..6442775 (Web
Mercator), i.e. Slovakia. `exportTilesAllowed` is false on all of them, so
tiles come one request at a time. A composite of overlay on base at z10 reads
as a proper VFR chart (airspace, aerodromes with frequencies, obstacles,
relief); see the two sample PNGs.

**The printed ICAO 1:500 000 chart and the AIP.** Behind a login. The AIS
portal https://aim.lps.sk/web/ (200, 20,892) states that all AIS products are
available only through it and that a free registration is required; its
product list shows "Login is required" against every item. `https://aim.lps.sk/`
itself answers 403. Whether the printed chart is offered as a file, and at what
price, is **UNVERIFIED**.

**Edition, cycle, discovery.** The tile service carries no edition field. The
web map item was last modified 8 Sep 2026 (`modified` 1788852583310), which
suggests it follows the AIRAC cycle: UNVERIFIED. Each tile has an ETag, so a
harvest can be refreshed conditionally.

**Access.** Open, no key, no login.

**Licence.** The overlay service's description is a reuse statement, in Slovak:

> "Pouzitie udajov VFR Manualu nie je limitovane."

(Use of the VFR Manual's data is not limited - diacritics dropped here.) It
goes on to say that anyone reusing print outputs, documents or map layers other
than for personal need must cite the source as VFR Manual, LPS SR s.p., and,
when publishing on the internet, add a hyperlink to https://gis.lps.sk/vfrm;
that LPS SR takes no responsibility for the data away from its source; and that
layers from outside contributors follow their owners' rules, naming Esri,
OpenStreetMap, **the 1:500 000 aeronautical chart and VM200 as copyright of
TOPU Banska Bystrica**, and ZB GIS as copyright of GKU. So:

- aeronautical overlay: **permitted**, with attribution and the link;
- topographic base: **unclear** - it belongs to the military topographic
  institute, and its terms were not found.

The AIM portal's own terms (https://aim.lps.sk/web/index.php?fn=31&lng=en, 200,
20,383) cover the AIP: informative or operational use with the LPS SR copyright
notice, anything else by prior written agreement.

**Verdict: USABLE WITH CAVEATS.** The only source in the region with an
explicit permission to reuse, already in Web Mercator. Caveats: the base map's
rights are a third party's; it is a live server, so harvest politely and cache;
it is the VFR Manual's web chart rather than the printed sheet; one could also
pair the permitted overlay with a base of our own.

## Czech Republic

**Publisher and series.** Air Navigation Services of the Czech Republic (ANS CR
/ RLP CR), AIM Centre, with the Office of Military Geography and
Hydrometeorology for the base. "Aeronautical Chart - ICAO 1:500 000", sheet
"PRAHA (2231-ABCD)". **One sheet**, the whole country. GEN 3.2 lists no
1:250 000 or 1:1 000 000 VFR area chart (WAC index: not applied); the
1:250 000 entries are per-aerodrome VFR arrival and departure charts.

**URLs (verified).**

| What | URL | Status | Bytes |
|---|---|---|---|
| Index (news item on the home page) | https://aim.rlp.cz/ | 200 | 7,683 |
| 300 dpi | https://aim.rlp.cz/data/icao_mapa/2026_ICAO_300.pdf | 200, Last-Modified 08 Apr 2026 | 36,652,692 |
| 600 dpi | https://aim.rlp.cz/data/icao_mapa/2026_ICAO_600.pdf | 200, Last-Modified 08 Apr 2026 | 99,198,326 |
| Last year's name | https://aim.rlp.cz/data/icao_mapa/2025_ICAO_300.pdf | 404 | - |
| Directory | https://aim.rlp.cz/data/icao_mapa/ | 403 | - |
| Terms of use | https://aim.rlp.cz/?lang=en&p=terms-of-use | 200 | 6,706 |
| GEN 3.2 | https://aim.rlp.cz/ais_data/aip/data/valid/g3-2.pdf | 200 | 1,838,377 |

**Format (300 dpi sample inspected).** PDF 1.5 made with Corel PHOTO-PAINT, one
page, 2948.3 x 1984.3 pt = **1040 x 700 mm**. The page is **one raster image,
12284 x 8268 px** - exactly 300 dpi. No vector content, no text layer. The
600 dpi file was not downloaded (one sample per source); by its name it should
be 24568 x 16536 px: UNVERIFIED. **Not georeferenced**: no `/GPTS`, no WKT.
The sheet prints its projection in the header (Lambert conformal conic, WGS84,
with two standard parallels; the figures were not legible in the preview:
UNVERIFIED) and has a labelled graticule every 30 minutes on all four edges, so
it can be registered from the graticule. The legend sits in the upper right
inside the neatline, over Poland, and a sheet index at lower left; both would
need masking.

**Edition, cycle, discovery.** WEF 19 MAR 2026, released 10 Apr 2026; one
edition a year, with the year in the file name and the previous year's file
removed. Hand amendments between editions are listed in GEN 3.2.8 and are not
in the file. **Script discovery:** parse the home page for
`data/icao_mapa/<YYYY>_ICAO_(300|600).pdf`, or try the current year and fall
back one.

**Access.** Open, no click-through. The home page warns that use of the site is
subject to its terms.

**Licence.** Terms of use (URL above, published 15 May 2012): the site is for
personal needs; it prohibits commercial use and prohibits providing the site's
content, or any part of it, as part of another product or service, commercial
or not, without ANS CR's prior consent. The chart's own imprint adds that
reproduction of the aeronautical information on it is possible only after prior
permission of ANS CR. Redistribution of derived tiles: **prohibited without
prior consent**.

**Verdict: USABLE WITH CAVEATS.** Free and open, a clean 300 or 600 dpi scan of
the real chart. Caveats: raster only; needs registration from the graticule;
consent needed to publish.

## Slovenia

**Publisher and series.** Kontrola zracnega prometa Slovenije (Slovenia
Control). "VFR aeronautical chart of the Republic of Slovenia 1:250 000" - the
national equivalent; **Slovenia publishes no 1:500 000 chart** (GEN 3.2's list
of charts available is empty, and no WAC index is published). **One sheet**
with a separate reverse side.

**URLs (verified).**

| What | URL | Status | Bytes |
|---|---|---|---|
| Index page | https://aim.sloveniacontrol.si/aim/products/vfr-charts/ | 200 | 79,803 (Slovenian version measured) |
| Front | https://aim.sloveniacontrol.si/aim/VFR/VFR%20Charts/VFR%20chart%202026%20-%20front.pdf | 200, Last-Modified 08 Jun 2026 | 14,005,110 |
| Back | https://aim.sloveniacontrol.si/aim/VFR/VFR%20Charts/VFR%20chart%202026%20-%20back.pdf | 200 | 1,915,284 |
| Legal information | https://aim.sloveniacontrol.si/aim/legal-information/ | 200 | 82,251 |
| eAIP issue list | https://aim.sloveniacontrol.si/aim/eAIP/Operations/history-en-GB.html | 200 | 28,144 |
| eAIP GEN 3.2 | https://aim.sloveniacontrol.si/aim/eAIP/Operations/2026-09-03-AIRAC/html/eAIP/LJ-GEN-3.2-en-GB.html | 200 | 22,301 |
| eAIP GEN 0.1 | same folder, `LJ-GEN-0.1-en-GB.html` | 200 | 19,318 |
| Old page, now a pointer | https://www.sloveniacontrol.si/informacije/Strani/VFR-Karta.aspx | 200 | 81,092 |

`/aim/en/products/vfr-charts/` is 404; the English page has no language prefix.

**Format (front sample inspected).** PDF 1.7, one page, 2863.0 x 1984.2 pt =
**1010 x 700 mm**, full bleed (no collar; title and scale bar sit in a box at
lower right inside the map). Hybrid: one raster base of 8040 x 5599 px (about
**202 dpi**) plus a vector overlay of 31,755 paths; the lettering is outlined,
so only 10 text runs remain. **Not georeferenced.** Graticule crosses and edge
ticks are drawn; the projection is not named in the extractable text:
UNVERIFIED.

**Edition, cycle, discovery.** Edition 2026, published 08 Jun 2026; GEN 3.2
says it is published once a year and amended by new edition only. Known errors
are listed on the index page and corrected in the online version. **Script
discovery:** parse the index page for `/aim/VFR/VFR Charts/VFR chart <YYYY> - front.pdf`.

**Access.** Open.

**Licence.** Legal information page: all rights reserved. eAIP GEN 0.1 section
5: the publication is copyright protected, and change, reproduction or
distribution is not allowed without Slovenia Control's permission. The chart is
outside the AIP, so that policy reaches it only by analogy. Redistribution of
derived tiles: **prohibited without permission** (unclear at best).

**Verdict: USABLE WITH CAVEATS.** Free, open, current. Caveats: 1:250 000, not
1:500 000, so it is a finer layer over a small country; needs registration;
permission needed.

## Albania

**Publisher and series.** ALBCONTROL, AIS Department, with the State Authority
for Geospatial Information (ASIG). "Aeronautical Chart - ICAO 1:500 000".
**One sheet**, Albania with margins of Montenegro, Kosovo, North Macedonia and
Greece, roughly 39.5-42.75 N, 18.3-21.6 E (read off the graticule). GEN 3.2
says it is published instead of the WAC 1:1 000 000.

**URLs (verified).**

| What | URL | Status | Bytes |
|---|---|---|---|
| Index page | https://www.albcontrol.al/aip/ | 200 | 387,576 |
| Chart PDF | https://www.albcontrol.al/wp-content/uploads/2026/09/AERONAUTICAL-CHART-01-OCT-2026.pdf | 200, Last-Modified 24 Sep 2026 | 17,448,948 |
| Chart JPEG | https://www.albcontrol.al/wp-content/uploads/2026/09/AERONAUTICAL-CHART-01-OCT-2026.jpg | 200 | 17,444,780 |
| eAIP GEN 3.2 | https://www.albcontrol.al/al/aip/06-AUG-2026-A/2026-08-06-AIRAC/html/eAIP/LA-GEN-3.2-en-GB.html | 200 | 44,198 |
| eAIP GEN 0.1 | same folder, `LA-GEN-0.1-en-GB.html` | 200 | 57,064 |

**Format (sample inspected).** PDF 1.4 from Qt / QGIS, one page, 1684 x 2384 pt
= 594 x 841 mm (A1 portrait), holding **one raster image of 7015 x 9933 px**
(300 dpi). Raster only.

**Georeferencing: present but wrong.** The PDF has a geospatial viewport (EPSG
4326) covering the whole page, but its `GPTS` span only 40.0427..39.8387 N,
20.4221..20.5662 E - a 0.2 x 0.14 degree box for a map that spans over three
degrees. It looks like a leftover from a QGIS layout item. **Ignore it** and
register from the printed graticule (Lambert Conformal Conic, crosses every 30
minutes).

**Edition, cycle, discovery.** Aeronautical information 01 OCT 2026,
topographic information 10 MAR 2025; reissued within the year alongside AIRAC
amendments. Parse the index page for
`wp-content/uploads/\d{4}/\d{2}/AERONAUTICAL-CHART-.*\.pdf`.

**Access.** Open.

**Licence.** Nothing attached to the file. AIP GEN 0.1 section 5 reserves all
rights and forbids reproduction without ALBCONTROL's prior written permission.
GEN 3.2 says AIP charts are free of charge in digital form. Redistribution of
derived tiles: **prohibited without written permission**. Contact:
ais@albcontrol.al.

**Verdict: USABLE WITH CAVEATS.** Free, open, very current. Caveats: raster;
embedded georeference must be discarded; permission needed. The sheet also
covers south-western Kosovo, which has no chart of its own.

## Bosnia and Herzegovina

**Publisher and series.** BHANSA, AIS BiH. "VFR Chart with recommended VFR
routes Bosnia and Herzegovina 1:500 000". **One sheet**, about 42.5-45.5 N,
15.5-19.67 E. No 1:250 000 or 1:1 000 000 VFR chart (WAC index: NIL).

**URLs (verified).**

| What | URL | Status | Bytes |
|---|---|---|---|
| Index (home page tile) | https://www.bhansa.gov.ba/en | 200 | 158,400 |
| Chart PDF | https://www.bhansa.gov.ba/storage/media/vfr-karta-effdate-3-sep-2026-1788434477zyzR7.pdf | 200, Last-Modified 03 Sep 2026 | 9,736,615 |
| eAIP issue list | https://eaip.bhansa.gov.ba/updates.json | 200 | - |
| eAIP GEN 3.2 | https://eaip.bhansa.gov.ba/2026-08-06-AIRAC/html/eAIP/LQ-GEN-3.2-en-GB.html | 200 | 15,410 |

The chart is not in the eAIP; ENR 6 holds six en-route and index charts.

**Format (sample inspected).** PDF 1.7 from Autodesk Civil 3D, one page,
2268 x 2154 pt = **800 x 760 mm**. Hybrid: 267,401 paths and 5,509 text runs
(airspace, grid, labels) over a raster relief base whose largest piece is
5393 x 5296 px (about 170 dpi if it spans the map: not measured). **No embedded
georeferencing**, but the two `/Measure` dictionaries are rectilinear with
176.39 units per point, which is exactly 1:500 000 in metres, and the sheet
prints its projection: Bessel 1841, Gauss-Krueger, central meridian 18, scale
factor 0.9999, with the 7-parameter shift to WGS84. Exact EPSG code: UNVERIFIED.

**Edition, cycle, discovery.** Effective 03 SEP 2026; amended by new edition
only. Parse the home page for `storage/media/vfr-karta-effdate-.*\.pdf` (the
name ends in a random suffix).

**Access.** Open.

**Licence.** Site footer and eAIP GEN 0.1 section 5 reserve all rights and
forbid reproduction or database storage without prior written permission.
Redistribution of derived tiles: **prohibited without written permission**.

**Verdict: USABLE WITH CAVEATS.** Free, open, current, vector line work.
Caveats: no embedded georeference; Bessel datum needs a shift; permission.

Also checked: BHDCA https://www.bhdca.gov.ba/index.php/en/ (200, 191,774) - no
chart, AIP or VFR link on the home page.

## Hungary

**Publisher and series.** HungaroControl, with HM Zrinyi Nonprofit Kft. (the
defence mapping company) as joint author. "ICAO 1:500 000 scale chart", offered
as a **single-sheet PDF** and as a **printable A4 atlas of 34 pages**.

**URLs (verified, HEAD only).**

| What | URL | Status | Bytes |
|---|---|---|---|
| Index page | https://ais-en.hungarocontrol.hu/vfrmanual/ (Hungarian: https://ais.hungarocontrol.hu/vfrmanual) | 200 | 1,955,131 |
| Single sheet | https://storage.hungarocontrol.hu/media/1132/ICAO_500k_2025.pdf | 200, application/pdf, Last-Modified 13 Jun 2025 | 68,467,353 |
| Atlas | https://storage.hungarocontrol.hu/media/1133/ICAO_Atlasz_2025.pdf | 200, Last-Modified 13 Jun 2025 | 94,741,256 |
| Terms of use | https://ais-en.hungarocontrol.hu/articles/icao-terms-of-use | 200 | 52,028 |
| eAIP index | https://ais.hungarocontrol.hu/aip/ | 200 | 94,699 |

**Format.** PDF. **Not inspected**: the terms say that downloading the chart is
acceptance of them, and accepting terms was outside this research's rules.
Vector or raster, georeferencing, page size: all UNVERIFIED. At 68 MB for one
sheet it is probably a high-resolution raster or a hybrid.

**Edition, cycle, discovery.** Airspace and data effective 17 APR 2025; files
dated June 2025, so annual and currently a year old. **Script discovery:**
parse the index page for `storage.hungarocontrol.hu/media/<id>/ICAO_500k_<YYYY>.pdf`;
the numeric id is not predictable.

**Access.** Open URL, but behind a **click-through**: each download button has
a checkbox declaring that the terms have been read and understood. The link is
present in the page source regardless.

**Licence.** A dedicated licence (URL above). It states that the chart is
published because a ministerial decree (21/2019) requires it, grants a
non-exclusive, non-transferable right to display, store, print and use the
chart for one's own purposes as an aeronautical information product, and
excludes everything else, naming adaptation, publication, making available,
distribution, transmission to third parties and recording in a database.
Redistribution of derived tiles: **prohibited**, explicitly.

**Verdict: NOT USABLE as-is.** It is free and digital, but the only way to
obtain it is to accept a licence that forbids exactly this use. It would need a
separate written agreement with HungaroControl and HM Zrinyi.

## Cyprus

**Publisher.** Department of Civil Aviation (DCA), AIS. The only free VFR area
chart is the **"Local VFR Chart"** in the Local VFR Manual. No ICAO 1:500 000,
1:250 000 or 1:1 000 000 VFR chart was found.

**URLs (verified).**

| URL | Status | Bytes |
|---|---|---|
| https://www.mcw.gov.cy/mcw/dca/ais/ais.nsf/index_en/index_en?OpenDocument (AIS home) | 200 | 26,406 |
| http://vrfmanual.dca.mcw.gov.cy/menu.html (host name really is "vrfmanual"; plain HTTP only) | 200 | 17,016 |
| http://vrfmanual.dca.mcw.gov.cy/charts/VFR_CHART_LCCC.pdf (island-wide) | 200 | 1,184,955 |
| http://vrfmanual.dca.mcw.gov.cy/charts/VFR_CHART_LCLK.pdf (Larnaka) | 200 | 1,487,049 |
| http://vrfmanual.dca.mcw.gov.cy/charts/VFR_CHART_LCPH.pdf (Pafos) | 200 | 1,983,895 |
| http://airac.dca.mcw.gov.cy | does not resolve | - |
| https://ln5.sync.com/dl/49a5d3cb0 (AIP zip, AIRAC AMDT 003/26) | 200 | 2,679 (viewer page, not the file) |

**Format (sample inspected).** PDF 1.7, one page, A4 landscape. Vector: 18,757
paths, 1,362 text runs. Labelled 1:500 000 but drawn across about 220 mm, so
nearer 1:1 000 000 as delivered. Schematic (airspace, routes, reporting points,
flat tints), not a topographic chart. **Not georeferenced**; the graticule is
unlabelled and no projection is stated.

**Edition.** Last update 30 APR 2019, unchanged in seven years. The AIP is
distributed as a zip on a third-party file-sharing service with the key in the
URL fragment, so curl cannot fetch it; whether it holds any VFR area chart is
UNVERIFIED.

**Access.** VFR manual open. **Licence.** DCA copyright notice, all rights
reserved; no reuse terms; the site's disclaimer link is 404. Redistribution:
**not permitted without asking**.

**Verdict: NOT USABLE for the target series.** A weak fallback at best:
schematic, 2019, not georeferenced, all rights reserved.

---

# Part 2 - Countries with nothing free, and what was checked

## Poland

**Publisher and series.** Polish Air Navigation Services Agency (PANSA / PAZP),
AIS. "Lotnicza Mapa Polski ICAO 1:500 000" (the "VFR map"), **six sheets**:
Gdansk, Olsztyn, Poznan, Warszawa, Wroclaw, Krakow; airspace GND to FL 95. Sold
folded or laminated, as single sheets or a set, and as a custom-centred wall
print (88 x 56.5 cm).

**Finding: paper only, and sold.** The product page says, in answer to repeated
requests, that a digital edition of the chart has **not** been introduced for
sale; everything AIS sells is on the order form.

| What | URL | Result |
|---|---|---|
| Product page | https://ais.pansa.pl/lotnicza-mapa-polski/ | 200, 73,007 bytes; the only images are 1024 px preview fragments (`.webp`) |
| Old map URL | https://ais.pansa.pl/mapy/ | 404 |
| AIP index | https://ais.pansa.pl/publikacje/aip-polska/ | 200, 56,088; links eAIP IFR, eAIP VFR, MIL eAIP valid 03 SEP - 30 SEP 2026 |
| eAIP VFR issue list | https://docs.pansa.pl/ais/eaipvfr/defaultInt_offline_2026-09-03.html | 200, 3,546 |
| eAIP VFR issue | https://docs.pansa.pl/ais/eaipvfr/AIRAC%20AMDT%20VFR%2009-26_2026_09_03/index-v2.html | 200, 19,972 |
| eAIP VFR menu data | .../v2/js/datasource.js | 200, 372,536; ENR holds ENR 0, 1 and 2 only - **there is no ENR 6** |
| eAIP VFR chart list | .../eAIP/GEN%201.6-en-GB.html | 200; aerodrome charts 1:2 500 to 1:25 000 and Visual Operation Charts 1:50 000, one per aerodrome; no area chart |
| Copyright rules | https://ais.pansa.pl/publikacje/zasady-ochrony-praw-autorskich/ | 200, 55,934 |
| Developers page | https://www.pansa.pl/dla-deweloperow/ | 404 |

The edition is ambiguous on the page: its title says edition 2026 and its
images were uploaded in May 2026, while the body still describes the twentieth
edition, available from 12 May 2025 with data of 17 April 2025.

**Licence.** AIS products are protected by copyright and database law and may
be used only by downloading, displaying or printing them unchanged for
operational purposes; any other use, commercial in particular, needs PANSA's
consent. Redistribution: **prohibited without consent**.

**Verdict: NOT USABLE** - not published digitally; paper is paid. Note for the
eAIP pattern: the IDS-style eAIP keeps its pages under `<issue>/eAIP/` with
spaces in the names, and the menu lives in `v2/js/datasource.js`.

## Croatia

**Publisher.** Croatia Control (Hrvatska kontrola zracne plovidbe), AIM/AIS. A
"VFR Manual" and a "VFR chart" exist; the chart's scale and format are
UNVERIFIED.

**Finding: registration and ordering required.** The AIM service page states
that the links to the eAIP and to the VFR Manual and VFR chart were deleted on
31 Dec 2025 and that access is possible exclusively through the AIM Portal with
obligatory registration and ordering. It also notes that these two products are
**not** in the European AIS Database.

| What | URL | Result |
|---|---|---|
| AIM service page | https://www.crocontrol.hr/en/services/aeronautical-information-management/ | 200, 103,333 |
| AIM Portal | https://aim.crocontrol.hr/ | 200, 34,234; an Angular application shell, content behind sign-in |
| AIC A 002/2024 | https://www.crocontrol.hr/app/uploads/2026/03/LD_Circ_2024_A_002_en-1.pdf | 200, 122,145; eAIP and VFR Manual on the portal, registration required, yearly subscription ordering |
| Publications page | https://www.crocontrol.hr/mediji/publikacije/ | linked from the home page; corporate publications, not opened |

**Licence.** The service page reserves all rights in the AIP and the VFR Manual
and forbids reproduction or database storage without prior written permission.
**Verdict: NOT USABLE** under the no-login rule. Whether the portal charges for
the VFR chart is UNVERIFIED.

## Lithuania

**Publisher.** AB Oro navigacija. "VFR Aeronautical Chart - ICAO 1:500 000
LITHUANIA".

**Finding: every official host refuses scripted requests.** `ans.lt`,
`www.ans.lt`, `www.oronavigacija.lt` (including the eAIP under `/a1/aip/`) and
`maps.ans.lt` all answer **403 with a Cloudflare "Just a moment..." challenge**,
to curl with a browser user agent and to WebFetch alike. It was not worked
around.

| What | URL | Result |
|---|---|---|
| E-shop product | https://ans.lt/en/eshop/vfr-chart-1-500-000 | 403, 5,681 (challenge page) |
| E-shop category | https://www.ans.lt/en/eshop/vfr-chart | 403, 5,655 |
| News item | https://www.oronavigacija.lt/en/news/new-vfr-chart | 403, 5,695 |
| eAIP GEN 3.2 | https://www.oronavigacija.lt/a1/aip/03_11Jun2026/2026-06-11-000000/html/eAIP/EY-GEN-3.2-en-US.html | 403, 5,882 |
| Online chart viewer | https://maps.ans.lt/portal/apps/webappviewer/index.html?id=8c0191d8d2ab429a86b42355534fae3e | 403, 5,873 |
| Its portal item | https://maps.ans.lt/portal/sharing/rest/content/items/8c0191d8d2ab429a86b42355534fae3e?f=json | 403, 5,900 |
| Third-party mirror of the AIP | https://aleksotas.eik.lt/aip/ | 200, 3,020, but it is now an aerodrome weather page; the mirrored AIP is gone |
| Regulator | https://tka.lt/ | 403, 5,312 |
| Archived shop page (1 Feb 2023) | Wayback copy of `oronavigacija.lt/en/eshop/vfr-chart-1-500-000` | 200, 41,348: paper chart, ninth edition, effective 24 Mar 2022, EUR 16.35 |

**From search-result snippets only (UNVERIFIED):** the 13th edition took effect
19 Mar 2026; the chart is not part of the AIP; an electronic version in jpg,
png, pdf and tif is offered through the e-shop (a product named "VFR chart -
siusti internetu", i.e. download); and an "Online VFR aeronautical chart"
exists as an ArcGIS web application on `maps.ans.lt`. The price of the
electronic version was not visible anywhere reachable. If it turns out to be
zero it would still need a shop account.

**Verdict: NOT USABLE.** Sold through an e-shop, and unreachable by a script.
Worth a manual look by the user in a browser: the ArcGIS viewer may expose a
tile service as Slovakia's does, and the electronic chart may be free.

## Serbia and Montenegro

**Publisher and series.** SMATSA llc, one AIP and one VFR AIP for both states.
"Aeronautical Chart - ICAO 1:500000" in **three sheets**: Part 1 Beograd, Part
2 Nis, Part 3 Podgorica; all dated 22 JAN 26.

**Finding: paid, not published digitally.** Both GEN 3.2 tables price it at
12.00 EUR a part. It is in ENR 6 of neither publication.

| What | URL | Result |
|---|---|---|
| eAIP start page | https://www.smatsa.rs/upload/aip/published/start_page.html | 200, 2,207; valid from 3 SEP 26 |
| eAIP GEN 3.2 | https://www.smatsa.rs/upload/aip/published/03-Sep-2026-A/2026-09-03-AIRAC/html/eAIP/LY-GEN-3.2-en-GB.html | 200, 230,570 |
| eAIP ENR 6 | same folder, `LY-ENR-6-en-GB.html` | 200, 13,752; 23 PDFs, all en-route or index charts at 1:1 000 000 to 1:2 500 000 |
| VFR AIP start | https://smatsa.rs/upload/vfraip/published/start_page.html | 200, 2,334 |
| VFR AIP GEN 3.2 | https://smatsa.rs/upload/vfraip/published/pdf/gen/VFR_LY_GEN_3_2_en.pdf | 200, 949,750; same three parts, same price |
| VFR AIP ENR index | https://smatsa.rs/upload/vfraip/published/htm/enr.htm | 200; index charts only |
| AIS information | https://smatsa.rs/en/ans/ais/info/ | 200, 13,662; products ordered by subscription form |
| Serbian CAD | https://cad.gov.rs/strana/20421/vfr-aip-zbornik-vazduhoplovnih-informacija-za-letenje-po-vizuelnim-pravilima | 200, 106,650; a pointer to `smatsa.rs/aip/` and `smatsa.rs/vfr-aip/` |
| Montenegrin CAA | https://www.caa.me/ | 200, 52,343; links to the SMATSA eAIP and VFR AIP only |

Free VFR material that does exist: per-aerodrome VFR procedure charts and
Visual Operation Charts at 1:200 000 to 1:600 000 in AD 2. They are small-area
charts, not a series.

**Licence.** Copyright in aeronautical information products is reserved to
SMATSA (VFR AIP GEN 0.1 section 5). **Verdict: NOT USABLE** - 12 EUR a sheet,
no digital edition. Montenegro's southern third is partly on the Albanian
sheet.

## North Macedonia

**Publisher.** M-NAV for the Civil Aviation Agency.

**Finding: the chart does not exist yet.** AIP GEN 3.2 lists "Aeronautical
chart ICAO 1:500000" as NIL, in the future tense.

| What | URL | Result |
|---|---|---|
| eAIP start | https://ais.m-nav.info/eAIP/Start.htm | 200, 9,923; AIRAC AMDT 04/2026, 03 SEP 2026 |
| GEN 3.2 | https://ais.m-nav.info/eAIP/current/pdf/gen/LW_GEN_3_2_en.pdf | 200, 107,545 |
| Menu data | https://ais.m-nav.info/eAIP/current/en/tree_items.js | 200, 10,032; no VFR chart entries |
| News, 7 Dec 2023 | https://mnavigation.m-nav.info/?p=9946&lang=en | 200; a first working version of a VFR map was shown to stakeholders; no download |
| CAA | https://www.caa.gov.mk/ | 200, 255,507; home page only, nothing relevant |

`ais.m-nav.info` answers 406 to a bare `Mozilla/5.0` user agent; a full browser
string works. **Licence.** GEN 0.1.5 reserves all rights. **Verdict: NOT
USABLE** - not published. Re-check GEN 3.2 in a year.

## Kosovo

**Publisher.** Air Navigation Services Agency (ANSA / KANS, formerly ASHNA);
the eAIP is titled for the Civil Aviation Authority of Kosovo.

**Finding: no VFR chart is published.** GEN 3.2 names a World Aeronautical
Chart 1:1 000 000 among the series "produced", but the list of charts actually
available holds only aerodrome, obstacle, area, SID, STAR, approach and
restricted-area charts (4.30 EUR each); the WAC index is NIL, topographical
charts NIL. There is no 1:500 000 chart in the list. **ENR 6 reads "To be
developed".**

| What | URL | Result |
|---|---|---|
| eAIP issue list | https://kans-ks.org/eAIP/default.html (`www.ashna-ks.org/eAIP/` redirects here) | 200, 10,397; current AIRAC AMDT 09/2026, 03 Sep 2026 |
| Issue frameset | https://kans-ks.org/eAIP/AIRAC%20AMDT%2009-2026_2026_09_03/index.html | 200, 1,631 |
| GEN 3.2 | .../AIRAC%20AMDT%2009-2026_2026_09_03/eAIP/BK-GEN%203.2-en-GB.html | 200, 55,894 |
| ENR 6 | .../eAIP/BK-ENR%206-en-GB.html | 200, 4,062 |
| GEN 0.1 | .../eAIP/BK-GEN%200.1-en-GB.html | 200, 26,701; no copyright statement found in it |
| CAA | https://caa.rks-gov.net/ | 200, 46,628; an AIP category page only |

Pattern for a script: the index links use a **backslash** and spaces
(`AIRAC AMDT 09-2026_2026_09_03\index.html`); pages are under `<issue>/eAIP/`
with the prefix `BK-` and a space in the section name.

**Verdict: NOT USABLE** - not published. The Albanian sheet covers the
south-west of the country.

## Greece

**Publisher.** Hellenic Aviation Service Provider (HASP), AIS site
`aisgr.hasp.gov.gr` (formerly `aisgr.hcaa.gr`).

**Finding: unreachable, and no 1:500 000 chart in ENR 6.**

| URL | Result |
|---|---|
| https://aisgr.hasp.gov.gr/ | 403, 373 bytes, Akamai "Access Denied" |
| https://aisgr.hcaa.gr/ | 403, 367 bytes |
| https://www.hasp.gov.gr/ | no response |
| https://hcaa.gov.gr/en | 200, 165,316; no AIS or chart links |
| https://www.gys.gr/hmgs-products.html (Hellenic Military Geographical Service) | 200, 8,079; no aeronautical chart mentioned |

From archived copies only (UNVERIFIED against the live site): the home page is
a user check holding a reCAPTCHA; the eAIP pattern is
`aisgr.hasp.gov.gr/aipgr_incl_amdt_<NNYY>_wef_<DDmonYYYY>/cd/ais/...`; ENR 6
lists three items (ATS routes, free route airspace, aerodromes index) and no
1:500 000 chart. GEN 3.2 could not be read, so who publishes a Greek 1:500 000
chart, if anyone, is unknown.

**Verdict: NOT USABLE** - bot wall plus CAPTCHA, and no chart in the AIP's
chart section.

## Bulgaria

**Publisher and series.** BULATSA. "Aeronautical chart 1:500 000", edition 13.0
announced 14 May 2026; about one edition a year. A 2021 notice says the chart
is free and electronic-only.

**Finding: free, but behind a login.** It lives in the B-FLIP v.2 portal, whose
four endpoints under
`https://b-flip.bulatsa.com/api/service-aup/aeronauticalChart500000/` (`json`,
`image`, `pdf`, `kmz`) all answer **403, length 0** anonymously; the portal
redirects a browser to a Keycloak sign-in with a "Register" option.

| URL | Result |
|---|---|
| https://www.bulatsa.com/en/media-center/news/publication-of-aeronautical-chart-1500-000-new-edition-2/ | 200, 154,611 |
| https://b-flip.bulatsa.com/publications/aeronautical-chart | 200, 60,367 (application shell) |
| https://b-flip.bulatsa.com/api/service-aup/aeronauticalChart500000/pdf | 403 |
| Bulgarian CAA https://www.caa.bg/en | 403, 5,257 |

Format per the application bundle: PDF and KMZ. Vector or raster, and
georeferencing: UNVERIFIED. **Licence:** not visible. **Verdict: NOT USABLE**
under the no-login rule. If the user registers personally this becomes a manual
drop-in like the wall planning chart, and the KMZ would be the easier input.

## Moldova

**Publisher.** MoldATSA, AIM site `aim.moldatsa.md`.

| URL | Result |
|---|---|
| https://www.moldatsa.md/ , https://aim.moldatsa.md/ | 403, Cloudflare challenge (`Cf-Mitigated: challenge`) |
| https://www.caa.md/ | 200, 163,682; nothing relevant |

From an archived copy only (UNVERIFIED): the AIM site has "AIM Registration"
and "Sign in", and treats `eaip`, `vfr-charts`, data sets, AIC and SUP as
products needing an authenticated user; registration uses a CAPTCHA. So a "VFR
charts" section exists, contents unknown. **Verdict: NOT USABLE** - bot wall,
then login.

## Turkey

**Publishers.** DHMI publishes AIP Turkey; Harita Genel Mudurlugu (HGM, the
national mapping agency) publishes the air chart series.

| URL | Result |
|---|---|
| https://ssd.dhmi.gov.tr/ (AIP Turkey) | 200, 107,225; content needs a subscription password and an image CAPTCHA |
| https://ssd.dhmi.gov.tr/Documents/AISPR_TR.pdf | 200, 661,326; web AIP at 28 EUR a month, 153 EUR a year |
| https://www.harita.gov.tr/urun/1500000-olcekli-raster-turkiye-ozel-hava-haritasi/27 | 200, 194,637; 1:500 000 special air chart, GeoTIFF, RGB, 300 dpi, LZW, 10-140 MB a sheet, LCC or geographic WGS84, 150 TL a sheet |
| https://www.harita.gov.tr/urunler/indirilebilir-urunler/14 (free downloads) | 200, 896,383; only a general airports reference map |
| DGCA https://web.shgm.gov.tr/ | 200, 90,938; nothing relevant |

HGM also lists 1:250 000 JOG-A and 1:250 000 low-altitude (TFC) charts, sold.
**Licence:** copyright and reuse fees apply. **Verdict: NOT USABLE** - both
official sources charge. HGM's GeoTIFFs are technically what the pipeline
wants, should the no-payment rule ever change.

## Ukraine

**Publisher and series.** UkSATSE, "AIS of Ukraine". "Aeronautical chart of
Ukraine scale 1:500 000 (ICAO)", **8 sheets**.

| URL | Result |
|---|---|
| https://www.aisukraine.net/titul_en.php | 200, 11,893 |
| https://www.aisukraine.net/pdf_docs/maps/maps_en.htm (the chart page) | 302 to an authentik login page |
| https://www.aisukraine.net/_eaip/current/ | 302 to `/_eaip/2026/airac_amdt_0526/`, then to the login page |
| https://www.aisukraine.net/services/eng/el_prod2.htm (prices 2026) | 200, 4,296; chart by website access USD 18.00 a sheet, 8 sheets as ISO USD 144.00 |
| https://uksatse.ua/ , https://uksatse.aero/ | do not resolve |
| https://avia.gov.ua/ | 403 |

**Licence.** Footer: all rights reserved. **Verdict: NOT USABLE** - paid, login
required; the eAIP itself is not publicly readable. Ukrainian airspace has been
closed to civil traffic since February 2022, so currency is doubtful anyway.

## Belarus

**Publisher.** Belaeronavigatsia. AIP GEN 3.2 lists **no** 1:500 000 chart
series; WAC index NIL. A separate AIP VFR exists behind a login.

| URL | Result |
|---|---|
| https://www.ban.by/ru/sbornik-aip/amdt | 200, 32,850; issue list |
| https://www.ban.by/AIP/Belarus260709/pdf/UM_GEN_3_2_en.pdf | 200, 212,757 |
| https://www.ban.by/AIP/Belarus260709/graphics/eAIP/ENR%206.1.pdf | 200, 558,775; en-route chart 1:1 500 000, not the target |
| https://www.ban.by/en/aeronautical-information-aip/vfr | 200; login form, zip download for subscribers |
| https://www.ban.by/attachments/article/470/Subscription%20pricing%202026.pdf | 200, 135,248; AIP VFR EUR 63 new, EUR 81 annual |
| Department of Aviation `caa.gov.by` | does not resolve |

**Licence.** Footer asks for a link to the source when site materials are used;
nothing on charts. **Verdict: NOT USABLE** - no such series in the public AIP;
the VFR AIP is paid. Whether it contains a 1:500 000 chart is UNVERIFIED.

## Georgia

**Publisher and series.** Sakaeronavigatsia. "Aeronautical Chart - ICAO
1:500 000", "Georgia 2020 Edition", sheet 2324BC2325AD, effective 03 DEC 2020,
**one sheet**, Transverse Mercator. GEN 3.2 says it is also available in
digital format, GeoTIFF and Geospatial PDF, and leaves the price cell empty.

**Finding: the download page is empty.** Checked twice on 2026-09-27, several
hours apart: https://ais.airnav.ge/en/aeronautical-chart answers 200 (22,119
bytes) and its whole body reads that the aeronautical chart is temporarily not
available. No file links in either language version. (A HEAD request to the
same URL returns 500; GET works.)

| URL | Result |
|---|---|
| https://ais.airnav.ge/en/aeronautical-chart | 200, 22,119; "temporarily not available" |
| https://airnav.ge/eaip/history-en-GB.html | 200, 18,475 |
| https://airnav.ge/eaip/2026-07-09-000000/html/eAIP/UG-GEN-3.2-en-GB.html | 200, 76,542 |
| https://airnav.ge/eaip/2026-07-09-000000/html/eAIP/UG-ENR-6-en-GB.html | 200, 9,516; index charts only |
| https://airnav.ge/storage/files/misc/AIP%20(including%20AIRAC%20AMDT%2003_26).zip | 200, 104,848,499; over the 100 MB limit, not downloaded; the chart is stated not to be part of the AIP |
| https://ais.airnav.ge/en/terms-of-use-2 | 200, 22,859; a disclaimer, silent on reuse |
| Wayback Machine | "temporarily offline" on both attempts |
| GCAA `www.gcaa.ge` | does not resolve |

**Licence.** Footer: all rights reserved; reuse not addressed. **Unclear.**

**Verdict: NOT USABLE today.** The best prospect among the eastern countries:
if the page returns, it offers exactly the formats the pipeline wants. It would
be a 2020 edition. Re-check periodically, and check the Wayback Machine for a
past copy of the page to learn the file URL pattern.

## Armenia

**Publisher.** ARMATS. GEN 3.2 says the 1:500 000 chart is not contained in the
AIP and may be purchased from ARMATS AIS; sheets, edition and price are not
stated.

| URL | Result |
|---|---|
| https://armats.am/en/category/eaip/ | 200, 52,782; current issue 02-26 (09 JUL 2026) |
| https://armats.am/wp-content/uploads/html-uploads/02-26-09JUL2026/html/eAIP/UD-GEN-3.2-en-GB.html | 200, 30,464 |
| .../html/eAIP/UD-ENR-6-en-GB.html | 200, 4,455; en-route chart only, index charts "under preparation" |
| https://aviation.am/ (Civil Aviation Committee) | 200, 2,957; an empty page |

**Verdict: NOT USABLE** - purchase only, nothing digital offered.

## Azerbaijan

**Publisher.** AZANS ("Azeraeronavigation" Air Traffic Department of AZAL);
regulator the State Civil Aviation Agency.

**Finding: no public official AIP or chart source was found.** GEN 3.2 of the
Azerbaijani AIP could not be read, so it is not known whether a 1:500 000 chart
exists.

| URL | Result |
|---|---|
| `azans.az`, `ais.az` | the zones exist (SOA at Cloudflare DNS) but have **no A record**; `www.azans.az` is NXDOMAIN |
| https://www.caa.gov.az/ | 200, 53,290; two regulation PDFs (an AIS regulation and an AIM manual), no charts |
| https://www.asec.az/about/azans | 200, 22,477; no AIP or chart links |
| https://www.azal.az/ | 403 |
| https://aim.az/ | 200, but an unrelated marketing site |
| https://e-aip.azurefd.net/ | 200, 19,080 - this is **Israel's** eAIP, not Azerbaijan's (a search lead that turned out wrong) |
| `aip.rossiya-airlines.com/Azerbaijan/AMDT/2016-01-07-AIRAC/...` | 404; a third-party mirror, gone |
| https://aip.aero/az/en/ (third party, not official) | 200; says the official portal may need registration and a paid subscription, and links only caa.gov.az |

**Verdict: NOT USABLE on current evidence.** The AIP is probably reachable only
through the European AIS Database, which needs an account.

---

# Notes for the pipeline

- **PDF georeferencing has to be parsed by hand here.** Inflate the object
  streams (`/Type /ObjStm`, FlateDecode), find each `/Type /Viewport` with its
  `/BBox` and `/Measure`, read `/GPTS` (lat lon pairs) against `/LPTS`, and the
  `/GCS` WKT. Latvia, Estonia and Romania all follow this ArcGIS pattern.
  Several files hold more than one viewport; choose by page area.
- **The map area is the viewport's BBox**, which is the analogue of the
  reviewed map-area manifests: title blocks, legends and tables share the page
  in Latvia and Romania.
- **The pdfium 32767 px limit applies.** Latvia's page is 1410 mm wide: at the
  scale a z11 or z12 build needs it passes 32767 px, so it must be drawn in
  blocks as `render_pdfs.py` already does.
- **Native resolution, for choosing max zoom.** A 1:500 000 sheet at 300 dpi is
  42.3 m/px, the same as a sectional; Czech 600 dpi would be 21.2 m/px.
  Romania's relief is 150 dpi (85 m/px) under vector line work; Slovenia's
  1:250 000 base at about 202 dpi is about 31 m/px.
- **Datums.** Bosnia is Gauss-Krueger on Bessel 1841 and needs the printed
  7-parameter shift; Estonia is L-EST97 on GRS80; the rest are WGS84.
- **Discovery is by index page everywhere.** No source has a stable "current"
  URL; every file name carries a date, a year or a random suffix. The index
  pages and patterns are given per country above.
- **Bot walls met**: Lithuania and Moldova (Cloudflare challenge), Greece
  (Akamai plus reCAPTCHA), Bulgaria's and Turkey's regulators. North
  Macedonia's server only wants a full browser user-agent string.

# Left unverified

- Hungary: everything about the file's content (not downloaded, because
  downloading is acceptance of its terms).
- Czech Republic: pixel size of the 600 dpi file; the standard parallels.
- Slovakia: the update cycle of the tile cache; the terms for the TOPU base
  map; whether the printed chart is offered as a file behind the login.
- Slovenia: the projection of the 1:250 000 sheet.
- Lithuania: edition, formats and price of the electronic chart, all from
  search snippets.
- Bulgaria, Moldova, Croatia: what sits behind the logins.
- Greece: GEN 3.2.
- Azerbaijan: whether a chart exists at all.
- Licence positions are read from published terms; none was confirmed with a
  publisher.
