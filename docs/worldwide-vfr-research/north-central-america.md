# World-wide VFR research: Canada, Mexico, Central America, Caribbean

Research date: 2026-09-27. Research was stopped early by the coordinator (session
usage limit), so some states were only reached by a web search and not by a
direct request. Those are marked **NOT CHECKED**. Anything stated but not
confirmed by a request I made myself is marked **UNVERIFIED**.

No accounts were created, no forms submitted, no terms accepted. Samples are in
`scratchpad/research/samples/`, working files in `scratchpad/research/nca/`.

## Summary

| Country / area | Series | Scale | Format | Georeferenced | Licence verdict | Overall verdict | Key URL |
|---|---|---|---|---|---|---|---|
| Caribbean (Bahamas, Cuba, Jamaica, Caymans, Hispaniola, PR, VI, Leewards, Windwards to about St Vincent) | FAA Caribbean VFR Aeronautical Charts 1 and 2 | 1:1,000,000 | GeoTIFF in zip (also PDF) | Yes, LCC / NAD83 | US government work, no access constraints; permitted | **USABLE** | https://aeronav.faa.gov/visual/09-03-2026/Caribbean/ |
| Puerto Rico, Virgin Islands | FAA Puerto Rico-VI TAC | 1:250,000 | GeoTIFF in zip | Yes | Permitted | **USABLE**, already in the `tac` series | https://aeronav.faa.gov/visual/09-03-2026/tac-files/Puerto_Rico-VI_TAC.zip |
| Canada south of ~49 N (west) / ~48.3 N (east); Yukon and BC next to Alaska; Mexico north of 24-32 N; Bahamas north of 24 N | FAA sectionals | 1:500,000 | GeoTIFF in zip | Yes | Permitted | **USABLE**, already in the `sectionals` series | https://aeronav.faa.gov/visual/09-03-2026/sectional-files/ |
| Canada | NAV CANADA VNC (51 sheets), VTA (7 sheets) | 1:500,000, 1:250,000 | Paper only from the publisher | n/a | Proprietary, reproduction prohibited | **NOT USABLE** (paid, no digital product) | https://products.navcanada.ca/shop-vfr/VFR-Navigation-Charts-VNC/ |
| Canada | open.canada.ca / NRCan | n/a | 1957 atlas plate only | No | OGL-Canada | **NOT USABLE** (not a chart series) | https://open.canada.ca/data/en/dataset/4e7bad54-07ba-5a95-8d6e-06dda1ae0644 |
| Mexico | AFAC "Cartas Aeronauticas" WAC (12) and 1:250,000 (about 30) | 1:1,000,000, 1:250,000 | PDF; 8 of 12 WAC are 1500 px thumbnails | No | No statement on page; unclear | **NOT USABLE** as published (resolution) | https://www.gob.mx/afac/acciones-y-programas/cartas-aeronauticas-251924 |
| Mexico | Same charts, hosted by FEMPPA (pilot federation) | 1:1,000,000, 1:250,000 | JPEG, about 4000 px | No (graticule printed) | Free, copyrighted, no reproduction for profit; non-commercial reuse unclear | **USABLE WITH CAVEATS** (about 245 m/px, 2016 data, third-party host, manual georeferencing) | https://femppa.mx/cartas-de-navegacion-1/ |
| Guatemala, Honduras, El Salvador, Nicaragua, Belize | COCESNA eAIP | none published | n/a | n/a | n/a | **NOTHING FREE** (no VFR chart exists or "in preparation") | https://www.cocesna.org/aipca/history.html |
| Costa Rica | Carta Aeronautica VFR Republica de Costa Rica | 1:500,000 | Paper, sold by IGN | n/a | n/a | **NOT USABLE** (USD 10, not in the AIP) | same eAIP, `ES-MR-GEN-3.2-es-ES.html` |
| Panama | Carta Aeronautica Republica de Panama | 1:500,000 | Paper, sold by AAC | n/a | n/a | **NOT USABLE** (USD 5 per sheet, not in the AIP) | https://www.aeronautica.gob.pa/ais-aip/ |
| Cuba | WAC 2585, 2586, 2587 | 1:1,000,000 | By request to ECNA | n/a | n/a | **NOT USABLE** (not downloadable) | https://aismet.avianet.cu/html/aip.html |
| Dominican Republic | WAC listed in GEN 3.2 | 1:1,000,000 | Not in AIP downloads | n/a | n/a | **NOTHING FREE** | https://aip.sna.gob.do/ |
| Eastern Caribbean states, Trinidad and Tobago | E/CAR AIP | none published | n/a | n/a | n/a | **NOTHING FREE** | https://caa.gov.tt/wp-content/uploads/2023/11/GEN3.2.pdf |
| Bermuda | Bermuda eAIP | none published | n/a | n/a | n/a | **NOTHING FREE** | https://www.airportauthority.bm/ais/aeronautical-info-publication.html |
| Curacao, Aruba, Bonaire, Sint Maarten, Saba, Statia | Dutch Caribbean eAIP | WAC 1:1,000,000 named as a series; a "VFR route overview" in ENR 6 | PDF in eAIP | NOT CHECKED | NOT CHECKED | **NOT CHECKED** past GEN 3.2 | https://dc-ansp.org/eAIS/eAIP/default.html |
| Jamaica | JCAA AIP | NOT CHECKED | Behind registration | n/a | n/a | **NOT CHECKED** (needs registration) | https://www.jcaa.gov.jm/aeronautical-information-management/ |
| Bahamas, Haiti, Cayman Islands, Barbados, Turks and Caicos, French Antilles | national AIPs | NOT CHECKED | | | | **NOT CHECKED** | see section 6 |

**Bottom line.** The only free, georeferenced, redistributable VFR charts in
this region are the FAA's. Two FAA files are not yet taken by the repo and are
worth adding: `Caribbean_1_VFR.zip` and `Caribbean_2_VFR.zip`, both
1:1,000,000. Canada is paid only. Mexico has a free but low-resolution,
unreferenced, stale WAC set. No Central American or Caribbean state was found to
publish a free VFR chart.

---

## 1. FAA charts covering non-US territory

### 1.1 Caribbean VFR Aeronautical Charts (CAC 1 and 2) -- USABLE

- **Publisher:** Federal Aviation Administration, Aeronautical Information Services.
- **Series:** Caribbean VFR Aeronautical Chart (CAC). **Scale 1:1,000,000**
  (`Source_Scale_Denominator: 1000000` in the shipped metadata). **2 sheets.**
- **Index page:** https://www.faa.gov/air_traffic/flight_info/aeronav/digital_products/vfr/ (HTTP 200, 149,858 bytes).
- **Edition:** 09-03-2026, valid 2026-09-03 to 2026-10-28. Next edition 2026-10-29.
  **56-day cycle** (`Maintenance_and_Update_Frequency: Every 56 days`).
- **Discovery:** same as the existing series: the edition folder
  `https://aeronav.faa.gov/visual/<MM-DD-YYYY>/`, which for this edition lists
  `All_Files/ Caribbean/ Grand_Canyon_files/ Heli_files/ PDFs/ sectional-files/ tac-files/`.
  The charts are in **`Caribbean/`**, not in `sectional-files/`.

Verified with `curl -sIL` on 2026-09-27:

| URL (under `https://aeronav.faa.gov/visual/09-03-2026/`) | Status | Content-Length | Type |
|---|---|---|---|
| `Caribbean/Caribbean_1_VFR.zip` | 200 | 38,338,649 | application/x-zip-compressed |
| `Caribbean/Caribbean_2_VFR.zip` | 200 | 22,986,936 | application/x-zip-compressed |
| `PDFs/Caribbean_1_VFR.pdf` | 200 | 80,813,853 | application/pdf |
| `PDFs/Caribbean_2_VFR.pdf` | 200 | 48,630,571 | application/pdf |
| `All_Files/Caribbean.zip` | 200 | 61,325,563 | application/x-zip-compressed |

Zip contents (Caribbean 1 downloaded and unzipped; Caribbean 2 read from its
central directory and first local headers by ranged request):

| Zip | Members |
|---|---|
| `Caribbean_1_VFR.zip` | `Caribbean 1 VFR Chart.htm` (25,812), `Caribbean 1 VFR Chart.tfw` (92), `Caribbean 1 VFR Chart.tif` (40,626,590) |
| `Caribbean_2_VFR.zip` | `Caribbean 2 VFR Chart.htm` (25,809), `Caribbean 2 VFR Chart.tfw` (92), `Caribbean 2 VFR Chart.tif` (24,705,339) |

Georeferencing, from `gdal.Info` on the Caribbean 1 sample and from the
Caribbean 2 world file and metadata:

| | Caribbean 1 | Caribbean 2 |
|---|---|---|
| Size | 17953 x 16423 px | 17814 x 12255 px |
| Pixel size | 84.670 x 84.667 m | 84.649 x 84.652 m |
| Bands | 1 band, 8-bit palette (256 entries), LZW | same per metadata (300 dpi, 8-bit); not opened |
| CRS | Lambert Conformal Conic 2SP on NAD83; origin 21.708335 N, 78.679585 W; parallels 22.6667 and 17.3333 | LCC (parameters NOT CHECKED, file not downloaded) |
| Sheet bounds (whole image, collar included) | W 86.974, E 71.715, N 27.525, S 14.811 | W 74.851, E 60.227, N 22.254, S 12.717 |

Notes for the pipeline:

- 84.67 m/px is exactly twice the sectionals' 42.33, as expected for 1:1,000,000
  at 300 dpi. At 21 N a Web Mercator pixel is 142.7 m at z10 and 71.4 m at z11,
  so the sheets are **native about z10.8**; upsampled 2x they would reach about z11.8.
- Palette-indexed, so they need the same RGB expansion before warping as the
  sectionals.
- A map inside a paper collar with legend panels, like a sectional. The FAA
  metadata says only the area inside the neat line is georeferenced accurately,
  so map areas need detecting and reviewing (`detect_sectional_areas.py` is the
  likely detector; not tried).
- **Coverage gaps, from the bounding boxes above (UNVERIFIED against pixels):**
  Caribbean 2 stops at about 60.2 W and 12.7 N including its collar, so
  **Barbados (59.6 W), Grenada (12.1 N) and Trinidad and Tobago (10-11 N) are
  outside it**. Caribbean 1 stops at about 87 W, so **Belize, Guatemala, El
  Salvador and most of Honduras are outside it**; it reaches the Yucatan coast,
  the Bay Islands / north-east Honduras and north-east Nicaragua only.
  **Bermuda (32.3 N) is on no FAA chart found here.**
- The PDFs were not opened. For the sectionals the PDFs wrap the same rasters
  (CLAUDE.md); whether that holds for the Caribbean PDFs is **NOT CHECKED**.

**Access:** open, no login, no click-through.

**Licence:** the metadata shipped in each zip states `Access_Constraints: None`
and, under use constraints, that "Acknowledgement of the FAA would be
appreciated in products derived from these data" (FAA, `Caribbean 1 VFR
Chart.htm`). It adds that the FAA seal or initials may not be used to imply
endorsement. US federal government work. Redistribution of derived tiles
**appears permitted**, with attribution requested and no implied endorsement.

**Verdict: USABLE.** Free, georeferenced, current, same publisher and format as
the series already built. Scale is 1:1,000,000, not the 1:500,000 target.

### 1.2 Is it already in the repo? No.

Read from `E:\faa-tiles\scripts\chart_series.py` (not modified):

- `sectionals`: `index_url="https://aeronav.faa.gov/visual/"`,
  `files_path="sectional-files/"`, `zip_pattern=r".+\.zip"`,
  `tif_pattern=r".+\.tif"`, excluding the Mariana and Samoan inset GeoTIFFs.
- `tac`: `files_path="tac-files/"`, `zip_pattern=r".+_TAC\.zip"`,
  `tif_pattern=r".+ TAC\.tif"`.

The `sectional-files/` listing for 09-03-2026 holds **53 zips and no file with
"carib" in its name**; the Caribbean zips are in the sibling folder
`Caribbean/`, which no series reads. `source/sectionals/` on disk holds 55
GeoTIFFs and none is a Caribbean chart. So **the Caribbean charts are not
included**, and adding them needs a new `Series` with `files_path="Caribbean/"`
(for example `zip_pattern=r"Caribbean_\d_VFR\.zip"`,
`tif_pattern=r"Caribbean \d VFR Chart\.tif"`).

**`Puerto Rico-VI TAC.tif` is already included**: the `tac` patterns match
`Puerto_Rico-VI_TAC.zip` (200, 21,949,110 bytes) and its one GeoTIFF, and the
file is present in `source/tac/`.

### 1.3 How far the existing sectionals reach into Canada, Mexico and the Bahamas

Measured, not assumed: each sheet's reviewed map-area polygon from
`scripts/sectionals_areas.json`, densified along its edges, run through the
GeoTIFF's geotransform and reprojected to lon/lat. All sheets are 42.33-42.34 m/px.

| Sheet | West | East | South | North | Foreign territory reached |
|---|---|---|---|---|---|
| Seattle | -125.01 | -116.29 | 44.41 | 49.08 | BC, a strip just north of 49 N |
| Great Falls | -117.01 | -108.29 | 44.41 | 49.08 | BC / Alberta / Saskatchewan strip |
| Billings | -109.00 | -100.29 | 44.41 | 49.08 | Saskatchewan / Manitoba strip |
| Twin Cities | -101.01 | -92.29 | 44.41 | 49.09 | Manitoba / NW Ontario strip |
| Green Bay | -93.01 | -84.34 | 43.99 | 48.41 | Ontario north of Lake Superior |
| Lake Huron | -85.00 | -76.35 | 43.99 | 48.29 | Southern and central Ontario |
| Detroit | -85.00 | -76.66 | 39.99 | 44.26 | SW Ontario to Toronto |
| Montreal | -77.00 | -68.34 | 43.99 | 48.29 | Ottawa, Montreal, Quebec City |
| Halifax | -69.00 | -60.65 | 43.99 | 48.28 | New Brunswick, PEI, most of Nova Scotia |
| New York | -77.00 | -68.67 | 39.99 | 44.28 | little |
| Ketchikan | -139.01 | -129.27 | 51.99 | 56.24 | BC coast, Haida Gwaii |
| Juneau | -141.07 | -129.74 | 55.98 | 60.27 | NW BC, SW Yukon |
| Dawson | -145.02 | -130.76 | 63.96 | 68.29 | Central Yukon to 130.8 W |
| Point Barrow | -157.04 | -139.18 | 67.95 | 72.33 | Northern Yukon coast |
| Anchorage | -151.51 | -139.41 | 59.96 | 64.27 | SW Yukon fringe |
| Seward | -152.48 | -139.98 | 59.13 | 61.58 | SW Yukon fringe |
| Los Angeles | -121.98 | -114.57 | 32.00 | 36.14 | Tijuana-Mexicali border strip |
| Phoenix | -116.01 | -108.76 | 31.27 | 35.74 | Northern Baja / Sonora to 31.3 N |
| El Paso | -109.00 | -102.46 | 28.00 | 32.26 | Chihuahua to 28 N |
| San Antonio | -103.00 | -96.37 | 28.00 | 32.26 | Coahuila fringe |
| Brownsville | -103.00 | -96.60 | 24.00 | 28.26 | Coahuila, Nuevo Leon, Tamaulipas to 24 N |
| Miami | -83.00 | -76.36 | 24.00 | 28.15 | NW Bahamas (Grand Bahama, Abaco, Andros, Nassau) |

So the existing `tileset-sectionals` already covers a border strip of Canada
about 0.1 degree deep in the west and up to 3-4 degrees deep in Ontario, Quebec
and the Maritimes; the parts of Yukon and BC that fall on Alaskan sheets;
Mexico down to 24 N in the north-east and 28-32 N further west; and the
north-west Bahamas. **How completely the FAA depicts aeronautical detail on the
foreign side was not inspected (UNVERIFIED).**

---

## 2. Canada -- NOT USABLE (paid only)

### 2.1 NAV CANADA VNC and VTA

- **Publisher:** NAV CANADA.
- **Series:** VFR Navigation Chart (VNC), **1:500,000**, **51 sheets**
  (AIR5000 Toronto to AIR5050 Alert; AIR5099 Alaska Highway is retired).
  VFR Terminal Area Chart (VTA), **1:250,000**, **7 sheets** (Toronto, Vancouver,
  Winnipeg, Montreal, Calgary, Ottawa, Edmonton).
- **Pages checked (all HTTP 200):**
  - https://www.navcanada.ca/en/aeronautical-information/visual-flight-rules-vfr-publications.aspx (64,655 bytes)
  - https://www.navcanada.ca/en/aeronautical-information/purchase-information.aspx (64,248)
  - https://www.navcanada.ca/en/vfrchartlist.pdf (195,018, application/pdf) -- the chart list, headed as NAV CANADA proprietary
  - https://products.navcanada.ca/shop-vfr/VFR-Navigation-Charts-VNC/ (280,368)
  - https://products.navcanada.ca/shop-electronic-products/ (30,074)
  - https://www.navcanada.ca/en/terms-of-use.aspx (101,834)
- **Format:** printed paper, sold by single order or subscription and through
  distributors. The store lists each VNC at **$16.50**.
- **No digital VNC/VTA product exists in the store.** The "Shop Electronic
  Products" category holds only: Electronic Canada Air Pilot, Electronic Canada
  Flight Supplement (eCFS), Electronic Canada Water Aerodrome Supplement,
  ICAO Type A charts, Restricted Canada Air Pilot, plus "CDs" and "PDFs for
  Download" headings. No GeoTIFF, GeoPDF or tile service was found.
- **Canada Flight Supplement:** the digital eCFS is a **paid subscription,
  $16.50 per region** (7 regions). It is an aerodrome directory, not a chart
  series, so it would not help even if free.
- **Edition and cycle:** per-sheet, irregular. Busy southern sheets about yearly
  (Toronto ed. 44 May 2026, next Jun 2027); northern sheets every 2 to 10 years
  (Alert ed. 7 Sep 2026, next Sep 2036). A script could read
  `vfrchartlist.pdf` for edition numbers, but there is nothing to download.
- **Access:** purchase. Digital VNC/VTA reach users only through licensed
  third-party apps (ForeFlight, FltPlan Go), per search results -- UNVERIFIED in
  detail, and paid or licence-bound either way.
- **Licence:** https://www.navcanada.ca/en/terms-of-use.aspx. All rights
  reserved. The terms forbid copying, reproducing or publishing site content
  without NAV CANADA's prior written permission, and allow one downloaded copy
  for personal non-commercial home use. A separate clause allows non-commercial
  reproduction of "certain" aeronautical publication information with source
  attribution; nothing indicates that covers the VNC/VTA, which are not on the
  site at all. The VFR page states NAV CANADA owns all intellectual rights in
  the data. Redistribution of derived tiles: **prohibited without written
  permission**.
- **Verdict: NOT USABLE.** Paid, paper only from the publisher, proprietary.

### 2.2 open.canada.ca and Natural Resources Canada

Searched the open.canada.ca CKAN API
(`https://open.canada.ca/data/api/3/action/package_search?q=...`, HTTP 200):

| Query | Hits | Relevant |
|---|---|---|
| `aeronautical chart` | 3 | NRCan "Aeronautical Charts"; NWT "Transportation"; TC "Drone Flight School" |
| `VFR navigation chart` | 17 | same NRCan item; the rest hydrographic, ice, bathymetry |
| `VNC aeronautical` | 0 | -- |
| `aeronautical` | 12 | same NRCan item; "Civil Airports, Aerodromes, and Time Zones" (atlas plate); Quebec "Airport" (vector points) |

The one hit, **"Aeronautical Charts" (NRCan, id
4e7bad54-07ba-5a95-8d6e-06dda1ae0644)**, is a single plate from the 3rd Edition
(1957) Atlas of Canada showing small samples of the chart types of the day. It
is JPG/PDF under the Open Government Licence - Canada. Example file
https://ftp.geogratis.gc.ca/pub/nrcan_rncan/raster/atlas_3_ed/eng/other/referencemaps/007.jpg
(HTTP 200, 2,154,856 bytes, image/jpeg). It is an illustration, not a chart
series, and not georeferenced.

**Verdict: NOT USABLE.** No current or historical aeronautical chart series is
published as open data. (NRCan's open topographic data could serve as a base
map, but that is not an aeronautical chart and is outside this brief.)

---

## 3. Mexico

### 3.1 AFAC "Cartas Aeronauticas" (gob.mx) -- NOT USABLE as published

- **Publisher:** Agencia Federal de Aviacion Civil (AFAC); the charts are
  credited on their face to SCT - DGAC - SENEAM.
- **Series:** "WAC" visual charts at **1:1,000,000, 12 sheets** (Guadalajara,
  Culiacan, Tuxtla Gutierrez, Nuevo Laredo, Monterrey, Mexico, Mexicali, Merida,
  Hermosillo, Chihuahua, Ciudad Juarez, Acapulco) covering the whole country;
  and **1:250,000** charts around cities, about 30 sheets.
  **No 1:500,000 series was found.**
- **Index page:** https://www.gob.mx/afac/acciones-y-programas/cartas-aeronauticas-251924 ,
  published 4 Sep 2020 per WebFetch. **`curl` receives a bot-challenge page
  ("Challenge Validation", 1,905 bytes, HTTP 200) instead of the content**, so a
  script cannot parse this index without a browser. I did not attempt to get
  past it. The link list below came from WebFetch.
- **Direct files** are served without a challenge, but **HEAD returns 404 while
  GET returns 200/206**, so verify with a ranged GET, not `curl -I`.

| File (under `https://www.gob.mx/cms/uploads/attachment/file/`) | GET status | Size | Last-Modified |
|---|---|---|---|
| `669681/guadalajara.pdf` | 200 | 277,367 | 2021-09-23 |
| `669680/culiacan.pdf` | 206 | 257,221 | 2021-09-23 |
| `669685/tuxtla-gtz.pdf` | 206 | 248,356 | 2021-09-23 |
| `669674/nuevo-laredo.pdf` | 206 | 6,380,313 | 2021-09-23 |
| `669684/monterrey.pdf` | 206 | 312,297 | 2021-09-23 |
| `669683/mexico.pdf` | 206 | 306,657 | 2021-09-23 |
| `669672/mexicali.pdf` | 206 | 7,745,621 | 2021-09-23 |
| `669682/merida.pdf` | 206 | 230,409 | 2021-09-23 |
| `669671/hermosillo.pdf` | 206 | 7,622,569 | 2021-09-23 |
| `669678/chihuahua.pdf` | 206 | 314,538 | 2021-09-23 |
| `669670/cd-juarez.pdf` | 206 | 4,562,614 | 2021-09-23 |
| `669679/acapulco.pdf` | 206 | 492,726 | 2021-09-23 |
| `669705/250-mexico.pdf` | 206 | 812,020 | 2021-09-23 |
| `669693/250-cancun-cozumel.pdf` | 206 | 295,168 | 2021-09-23 |
| `669715/250-tijuana.pdf` | 206 | 369,417 | 2021-09-23 |

- **Format, from the sample `guadalajara.pdf`:** one A4 landscape page
  (841.89 x 595.28 pt) holding **a single 1500 x 888 px JPEG**, no text, no
  vector, producer "PDF Reducer". That is roughly 440 m/px for a sheet this
  size -- a thumbnail. `250-mexico.pdf` is the same kind of file (1500 x 2141
  px image, read from its header by ranged request). **Eight of the twelve WAC
  files are this small.**
- The other four (`nuevo-laredo`, `mexicali`, `hermosillo`, `cd-juarez`, 4.6-7.7
  MB) are full-size pages: `mexicali.pdf` has a 2795 x 1969 pt page (38.8 x 27.3
  in), created in Adobe Illustrator CS5.1 on 2017-06-05. **Whether their content
  is vector or an embedded raster is NOT CHECKED** (only the first and last
  64 KB were read; one sample per source).
- **Georeferenced:** no. The sample has no geospatial PDF dictionaries and GDAL
  does not open it as a raster.
- **Edition:** files dated 2017 (creation) and 2021-09-23 (upload). No update
  cycle stated. Nothing for a script to discover.
- **Access:** open for the files; index page behind a bot challenge.
- **Licence:** WebFetch found no price, copyright or reuse statement on the
  page, only the standard gob.mx line making the supplying agency responsible
  for the information. Redistribution: **unclear**.
- **Verdict: NOT USABLE** as published: two thirds of the national set is
  thumbnail resolution, nothing is georeferenced, and the data is 2016-2017.

### 3.2 The same charts hosted by FEMPPA -- USABLE WITH CAVEATS

- **Host:** Federacion Mexicana de Pilotos y Propietarios de Aeronaves, a pilot
  association, **not the publisher**. The charts are the SCT - DGAC - SENEAM ones.
- **Index pages (HTTP 200):** https://femppa.mx/cartas-de-navegacion-1/ (63,772
  bytes, the 1:1,000,000 set) and https://femppa.mx/cartas-de-navegacion-1-250000/
  (70,558 bytes, the 1:250,000 set).
- **1:1,000,000, 12 JPEGs,** all HTTP 200 under
  `https://femppa.mx/wp-content/uploads/2017/06/`:
  `Acapulco3500px.jpg` 3,535,344; `CdJuarez-1M-oct-2016.jpg` 2,587,501;
  `Chihuahua-1M-oct-2016.jpg` 6,578,852; `Hermosillo.jpg` 3,319,092;
  `Merida.jpg` 3,297,815; `Mexicali.jpg` 2,817,328; `Mexico.jpg` 5,164,136;
  `Monterrey.jpg` 6,128,168; `Nuevo-Laredo.jpg` 3,545,371; `Tuxtla_Gtz.jpg`
  3,916,994; `culiacan.jpg` 4,561,178; `guadalajara.jpg` 4,738,075.
- **1:250,000, 30 JPEGs** under the same folder (`250_mexico.jpg` is HTTP 200,
  7,922,526 bytes, 3800 x 3138 px). These are area charts around individual
  cities, not a contiguous series.
- **Sample inspected:** `Mexico.jpg`, **4000 x 2353 px, RGB, 72 dpi tag**. The
  map body spans about 100.3 W to 92.7 W and 18 N to 22.3 N, so roughly
  **245 m/px, native about z9**. It is a genuine ICAO-style visual chart: hill
  shading, hypsometric tints, airports, navaids, restricted areas, a legend
  panel on the left and a scale bar above. Place names and frequencies are
  legible at full size; the smallest type is soft.
- **Georeferenced:** no. A one-degree graticule with labelled ticks is printed
  on the map, so each sheet could be registered by hand from graticule
  intersections. Projection is not stated on the part I read (LCC is likely;
  UNVERIFIED).
- **Edition:** isogonic lines are dated August 2016; two file names say
  "oct-2016". The page says updated 2015 and tells the reader to consult the AIP
  or a current source. **No update cycle; effectively a one-off.**
- **Access:** open, no login.
- **Licence:** stated on both pages: free copies, copyrighted, and "queda
  prohibida su reproduccion total o parcial con fines de lucro" (FEMPPA page,
  quoting the publisher). So reproduction for profit is prohibited;
  non-commercial reproduction is not expressly granted. Redistribution of
  derived tiles on a public non-commercial site: **unclear, leaning permitted
  for non-commercial use**; the host is also not the rights holder.
- **Verdict: USABLE WITH CAVEATS.** Whole-country coverage at 1:1,000,000, but
  about 245 m/px (three times coarser than the FAA Caribbean charts), ten years
  old, needs manual georeferencing of 12 sheets, non-commercial terms only, and
  a third-party host that could remove the files. Low priority.

### 3.3 SENEAM AIP Mexico and INEGI -- NOT CHECKED

- `https://aipmexico.seneam.gob.mx/` and
  `https://aipmexico.seneam.gob.mx/AIP/doc/GEN/GEN_3/GEN_3.2.pdf` both returned
  **HTTP 503** ("No server is available") when tried. GEN 3.2 would list the
  official chart series and prices. **NOT CHECKED.**
- `https://www.gob.mx/seneam/acciones-y-programas/publicacion-pia-aip` returned
  the same bot-challenge page as the AFAC page. **NOT CHECKED.**
- INEGI was **NOT CHECKED** directly. A secondary source says the visual charts
  were produced by SCT with INEGI's collaboration; INEGI's own open products are
  topographic, not aeronautical (UNVERIFIED).
- A blog (recursosdeaviacion.com) re-hosts scans of old US-government WAC and
  TPC sheets over Mexico. Those are the ONC/TPC family, which belongs to the
  world-wide source another researcher is covering. Not pursued here.

---

## 4. Central America

### 4.1 COCESNA eAIP (Guatemala, Belize, Honduras, El Salvador, Nicaragua, Costa Rica)

- **Publisher:** COCESNA (Corporacion Centroamericana de Servicios de
  Navegacion Aerea), one eAIP for all six states.
- **Index:** https://www.cocesna.org/aipca/history.html (HTTP 200, 31,526
  bytes). Currently effective issue **03 SEP 2026** (NON AIRAC AMDT 58/26,
  published 06 AUG 2026); next 01 OCT 2026. Roughly a 28-day cycle.
- **Current issue base:**
  `https://www.cocesna.org/aipca/AIP_2658/Eurocontrol/COCESNA/2026-09-03-NON%20AIRAC/html/`
  -- `index-es-ES.html` (200), `eAIP/ES-menu-es-ES.html` (200, 353,860 bytes).
  A script discovers it by taking the first link under "Currently Effective
  Issue" on `history.html`.
- **Access:** open, no login. (`https://www.cocesna.org/aipca/` itself returns a
  PHP fatal error; use `history.html`.)
- **Example verified:** `eAIP/Maps/MN_ENR_6.1_ATS_ROUTE_LOW.pdf`, HTTP 200,
  594,540 bytes, application/pdf -- an en-route chart, not a VFR chart.
- **ENR 6** (`eAIP/ES-CS-ENR-6.1-es-ES.html`, 200) links 23 PDFs: ATS route
  charts (lower/upper), RNAV routes, airspace classification, prohibited /
  restricted / danger areas, navaids, volcano and bird-migration index charts,
  FIR and sector charts, Guatemala's limits and sport areas, a Costa Rica CTA
  area chart. **No 1:500,000 or 1:1,000,000 visual chart.**

GEN 3.2 per state (`eAIP/ES-<XX>-GEN-3.2-es-ES.html`, all HTTP 200):

| State | Code | What GEN 3.2 says about VFR en-route charts |
|---|---|---|
| Guatemala | MG | No visual en-route series. Lists aerodrome, approach, SID/STAR, area charts (TMA La Aurora 1:1,000,000; TMA Tikal 1:500,000), index charts at 1:2,000,000-1:2,500,000, danger-area charts. Charts are free to view and download in the eAIP. |
| Honduras | MH | WAC 1:1,000,000 **not available**; 1:500,000 **in preparation**. |
| El Salvador | MS | List of available charts: **in preparation**. WAC index: **NIL**. |
| Nicaragua | MN | No 1:500,000 or WAC entry found; series listed are aerodrome, approach, index and visual approach charts. |
| Belize | MZ | WAC 1:1,000,000 index: **in preparation**. Listed charts are for MZBZ only, dated 27 JUN 17. |
| Costa Rica | MR | **A 1:500,000 chart exists**: "Carta Aeronautica Republica de Costa Rica", produced by DGAC with the Instituto Geografico Nacional. Listed at **USD 10.00**, to be bought from the IGN; it is not one of the charts that form part of the AIP. Only its sheet index (`GEN_3.2_ACI`, 28 DEC 23) is in the eAIP. |

**Licence:** COCESNA's eAIP terms were **NOT CHECKED**; moot, as there is no
chart to take.

**Verdict:** Guatemala, Honduras, El Salvador, Nicaragua, Belize -- **nothing
free, because no VFR chart is published at all**. Costa Rica -- **NOT USABLE**,
the chart is paid and paper. Whether Costa Rica's IGN / SNIT geoportal serves
the chart as a layer is **NOT CHECKED**.

### 4.2 Panama -- NOT USABLE (paid)

- **Publisher:** Autoridad Aeronautica Civil (AAC), AIS Panama.
- **Index:** https://www.aeronautica.gob.pa/ais-aip/ (HTTP 200, 64,732 bytes).
  The whole AIP is free PDF, no login.
- **Series:** "Carta Aeronautica VFR 1:500,000 -- Carta Aeronautica Republica de
  Panama", Lambert Conformal Conic with standard parallels 07 and 20 degrees,
  aeronautical information dated **MAR 2025**, **USD 5.00 per sheet**. Sheet
  count not stated in the text I read.
- **Evidence:** `.../1. GEN/GEN 3 SERVICIOS.pdf` (HTTP 200, 4,239,487 bytes),
  GEN 3.2 sections 3 to 5: charts are obtained by paying the listed price at
  the Publications Section.
- **Not in the free AIP:** `.../2. ENR/ENR 6 CARTAS DE EN RUTA.pdf` (HTTP 200,
  35,068,278 bytes, 25 pages) holds en-route, sector, airspace, prohibited-area
  and radio-facility charts only.
- **Verdict: NOT USABLE.** Exists at the target scale but is paid and paper.

---

## 5. Caribbean states

### 5.1 Cuba -- NOT USABLE

- **Publisher:** Empresa Cubana de Navegacion Aerea (ECNA), AIS Cuba.
- **AIP:** https://aismet.avianet.cu/html/aip.html (HTTP 200, 204,016 bytes),
  free PDF, no login; certificate did not validate (`curl -k` needed).
- **Series:** World Aeronautical Chart ICAO **1:1,000,000, 3 sheets**: Santiago
  de Cuba (2585), La Habana (2586), Pinar del Rio (2587), all dated 27 NOV 25.
- **Evidence:** `https://aismet.avianet.cu/assets/data/pdf/AIP/GEN_3.2.pdf`
  (HTTP 200, 1,471,373 bytes), sections 3.2.3 to 3.2.5: acquisition requests go
  to ECNA's AIS publications office. No price is printed.
- **Not downloadable:** the AIP page links 189 PDFs; the only en-route charts
  are `ENR_6.1-1_TIRO`, `ENR_6.1-2_RETIRO`, `ENR_6.1-3` (310,717 bytes),
  `ENR_6.1-5` (262,214), `ENR_6.1-11` (220,817). None is the WAC.
- An unofficial copy of one sheet sits on a flight-simulation site,
  `https://cu.ivao.aero/download/charts/OrienteWAC.pdf` (HTTP 200, 2,299,007
  bytes, last modified 2023-06-16). Not downloaded or inspected; third party, no
  licence, not a basis for a public tileset.
- **Verdict: NOT USABLE.** The FAA Caribbean 1 chart covers Cuba.

### 5.2 Dominican Republic -- nothing free

- **AIP:** https://aip.sna.gob.do/ (HTTP 200, 42,005 bytes), free, no login.
- `https://aip.sna.gob.do/Datos/3GEN/gen_3-2.pdf` (HTTP 200, 1,123,830 bytes)
  names "World Aeronautical Chart 1:1,000,000" among the series and prints a WAC
  index page, with non-AIP charts produced by the Instituto Cartografico
  Militar and obtained from IDAC or the ICM. No price found.
- The only ENR 6 downloads are `enr_6-1-1.pdf` and `enr_6-1-2.pdf` (not opened;
  en-route charts by their numbering -- UNVERIFIED).
- A search result reports IDAC, IGN and ICM agreeing to *develop* visual
  navigation cartography, which implies none is current (UNVERIFIED).
- **Verdict: nothing free.** Covered by FAA Caribbean 1 and 2.

### 5.3 Eastern Caribbean AIP and Trinidad and Tobago -- nothing free

- **Publisher:** Trinidad and Tobago Civil Aviation Authority, which publishes
  the Eastern Caribbean (E/CAR) AIP for Anguilla, Antigua and Barbuda, British
  Virgin Islands, Dominica, Grenada, Montserrat, St Kitts and Nevis, Saint
  Lucia, St Vincent and the Grenadines, and Trinidad and Tobago.
- `https://caa.gov.tt/wp-content/uploads/2023/11/GEN3.2.pdf` (HTTP 200, 792,832
  bytes): the series published are aerodrome, parking, obstacle, instrument
  approach, terrain awareness and "other" charts. **No visual en-route chart and
  no WAC.**
- `https://caa.gov.tt/notices-to-operators-notification/trinidad-tobago-charts/`
  (HTTP 200) links 24 PDFs, among them a Piarco CTR area chart and upper route
  chart; none is a VFR en-route chart.
- The full eAIP is obtained through an acquisition form (not submitted).
- **Verdict: nothing free.** FAA Caribbean 2 covers the islands down to about St
  Vincent; **Grenada, Barbados and Trinidad and Tobago have no free chart at
  all** from any source found here.

### 5.4 Bermuda -- nothing free

- eAIP: https://www.airportauthority.bm/eaip/27-Nov-2025-A/history-en-GB.html
  (HTTP 200), free. `.../2025-11-27-AIRAC/html/eAIP/TX-GEN-3.2-en-GB.html`
  (HTTP 200, 3,681 bytes) lists aerodrome, procedure, visual approach and
  en-route charts for the one airport, and refers to the UK's 1:1,000,000 WAC
  series for the area.
- **Verdict: nothing free.** Not on any FAA VFR chart found here either.

### 5.5 Dutch Caribbean (Curacao, Aruba, Bonaire, Sint Maarten, Saba, Sint Eustatius) -- NOT CHECKED past GEN 3.2

- eAIP: https://dc-ansp.org/eAIS/eAIP/default.html (HTTP 200), free. Current
  issue AIRAC AMDT 02-26, effective 06-08-2026; next 01-10-2026.
- `.../AIRAC%20AMDT%2002-26_2026_08_06/eAIP/GEN%203.2-en-US.html` (HTTP 200,
  144,741 bytes) names "World Aeronautical Chart - ICAO 1:1 000 000" among the
  series produced; the list of charts actually available, with a price column,
  was only partly read.
- `.../eAIP/ENR%206-en-US.html` (HTTP 200) includes a chart titled "VFR ROUTE
  CURACAO FIR OVERVIEW" next to the en-route and area charts. **Not opened.**
- **Verdict: NOT CHECKED.** Worth a second look; the islands are small and lie
  at 12-12.6 N and 18 N, the southern three outside FAA Caribbean 2.

### 5.6 Jamaica -- NOT CHECKED (registration required)

- https://www.jcaa.gov.jm/aeronautical-information-management/ sends users to a
  registration portal (`aim.jcaa.aero/client/register`) for publications. Not
  registered, per the rules. Covered by FAA Caribbean 1.

### 5.7 Puerto Rico and US Virgin Islands -- USABLE (FAA)

- FAA Puerto Rico-VI TAC at 1:250,000 (already in the `tac` series) and FAA
  Caribbean 2 at 1:1,000,000. There is no FAA sectional for Puerto Rico.

---

## 6. Countries where nothing free was found, and what was checked

| Country / territory | Checked | Result |
|---|---|---|
| Canada | NAV CANADA VFR page, purchase page, chart list PDF, online store (VFR and electronic categories), terms of use; open.canada.ca CKAN search (4 queries) | VNC/VTA paid paper only; eCFS paid; open data has only a 1957 atlas plate. FAA sectionals cover the border strip. |
| Guatemala | COCESNA eAIP GEN 3.2 and ENR 6 | No VFR en-route chart published. |
| Belize | COCESNA eAIP GEN 3.2 | WAC "in preparation". |
| Honduras | COCESNA eAIP GEN 3.2 | WAC not available, 1:500,000 "in preparation". |
| El Salvador | COCESNA eAIP GEN 3.2 | Chart list "in preparation", WAC NIL. |
| Nicaragua | COCESNA eAIP GEN 3.2 and ENR 6 | No VFR en-route chart listed. |
| Costa Rica | COCESNA eAIP GEN 3.2 | 1:500,000 chart exists, USD 10, paper, from IGN. IGN geoportal NOT CHECKED. |
| Panama | AAC AIP GEN 3 and ENR 6 PDFs | 1:500,000 chart exists, USD 5 per sheet, paper. |
| Cuba | ECNA AIP page and GEN 3.2 | 3 WAC sheets by request only. |
| Dominican Republic | IDAC AIP index and GEN 3.2 | WAC named, not downloadable. |
| Anguilla, Antigua and Barbuda, BVI, Dominica, Grenada, Montserrat, St Kitts and Nevis, Saint Lucia, St Vincent, Trinidad and Tobago | E/CAR AIP GEN 3.2, TTCAA charts page | No VFR chart series. |
| Bermuda | Bermuda eAIP GEN 3.2 | No VFR chart. |
| Jamaica | JCAA AIM page (via WebFetch) | AIP behind registration. NOT CHECKED further. |
| Bahamas | web search only | **NOT CHECKED.** No official AIP URL found. FAA Miami sectional and Caribbean 1 cover it. |
| Haiti | web search only (OFNAC publishes an AIP PDF) | **NOT CHECKED.** |
| Cayman Islands | web search only (AIP PDFs free on caymanairports.com) | **NOT CHECKED** for a VFR chart. |
| Barbados | web search only | **NOT CHECKED.** |
| Turks and Caicos | not searched | **NOT CHECKED.** |
| Guadeloupe, Martinique, St Martin, St Barthelemy | web search only | **NOT CHECKED** at the SIA. Search results show only a commercial 1:250,000 chart (Editerra / Air Million, about EUR 12), which is paid. |
| Mexico (official AIP) | aipmexico.seneam.gob.mx | HTTP 503 at the time. **NOT CHECKED.** |

## 7. Recommendations

1. **Add the two FAA Caribbean charts.** New series reading `Caribbean/` in the
   same edition folder; same 56-day cycle, same GeoTIFF layout (palette, LCC,
   collar) as the sectionals at half the resolution. About 61 MB to download.
2. **Nothing to do for the FAA border coverage** -- it is already in
   `tileset-sectionals`. The table in 1.3 says how far it reaches.
3. **Do not plan on Canada.** No free source exists; the only route would be a
   written licence from NAV CANADA.
4. **Mexico is a judgement call.** The FEMPPA-hosted WAC set is the only
   whole-country VFR chart available without payment, but it is coarse, dated
   2016, unreferenced and licensed for non-profit use only. If it is used, ask
   AFAC/SENEAM for the full-resolution originals and written permission first.
5. **Follow-ups left open:** the Dutch Caribbean "VFR route overview" chart and
   chart list; the four full-size AFAC PDFs (vector or raster); AIP Mexico GEN
   3.2 once the server is back; the SIA's AIP for the French Antilles; the
   Bahamas, Haiti, Cayman, Barbados and Turks and Caicos AIPs.
