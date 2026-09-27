# World-wide VFR research: Western and Northern Europe (official national sources)

Researched 2026-09-27, in two passes. Scope: official publishers only (ANSP,
CAA, national mapping agency, eAIP). OpenFlightMaps and other community charts
are out of scope here.

**Status: complete for all 20 countries, with four gaps**, each listed under
*Remaining gaps* at the end: the Icelandic PDF could not be inspected, Malta's
AIP page refused every request, the German chart list was not found in the
online AIP, and no sample was checked for an exact neatline.

Conventions used below:

- "Verified" means an HTTP request made in this session returned the status and
  size quoted. Anything else is marked UNVERIFIED or NOT CHECKED.
- Licence wording is **paraphrased**, not quoted, except for one short verbatim
  quote (Switzerland). Follow the URL given to read the exact sentence before
  relying on it.
- Verdicts are judged against the actual goal: *publishing derived map tiles on
  a public website*. A chart that is free to download but whose terms forbid
  redistribution is therefore "NOT USABLE as it stands", and says so, rather
  than "USABLE WITH CAVEATS". Reclassify those if permission is sought.
- Nothing was logged into, registered for or accepted. Two charts sit behind an
  accept-the-terms click (Iceland, Norway's M517) and were not fetched.

## Summary

| Country | Series | Scale | Format | Georeferenced | Licence for public tiles | Verdict | Key URL |
|---|---|---|---|---|---|---|---|
| Switzerland (+ Liechtenstein) | Aeronautical Chart ICAO Switzerland | 1:500,000 | Cloud-optimised GeoTIFF, RGB | Yes, EPSG:2056, 50 m/px | Permitted, attribution required | **USABLE** | https://data.geo.admin.ch/api/stac/v0.9/collections/ch.bazl.luftfahrtkarten-icao/items |
| Switzerland | Glider chart (Segelflugkarte) | 35 m/px (nominal scale UNVERIFIED) | Cloud-optimised GeoTIFF, RGB | Yes, EPSG:2056 | Permitted, attribution required | **USABLE** | https://data.geo.admin.ch/api/stac/v0.9/collections/ch.bazl.segelflugkarte/items |
| Denmark | ICAO ANC Denmark | 1:500,000 | GeoTIFF (palette) and **vector PDF** | Yes, both; custom LCC / WGS84 | Unclear, no terms found | **USABLE WITH CAVEATS** | https://aim.naviair.dk/charts/ |
| Denmark | ICAO ANC Copenhagen Area | 1:250,000 | GeoTIFF and PDF | Yes, custom LCC, 10.58 m/px | Unclear | **USABLE WITH CAVEATS** | https://aim.naviair.dk/charts/ |
| Faroe Islands | ICAO ANC Faroe Islands | 1:250,000 | GeoTIFF and PDF | Yes, custom LCC, 10.58 m/px | Unclear | **USABLE WITH CAVEATS** | https://aim.naviair.dk/charts/ |
| Austria | Luftfahrtkarte ICAO (2252-A) | 1:500,000 | PDF holding one raster image, 14704 x 10216 | **No** | Non-commercial use allowed; redistribution not addressed | **USABLE WITH CAVEATS** | https://www.austrocontrol.at/icao_karte |
| Spain | ENAIRE VFR500 | 1:500,000 | Zip of TIFF + TFW, and **vector PDF** | Yes, both; custom LCC / WGS84, 42.33 m/px | Prohibited without written authorisation | **NOT USABLE as it stands** (free download) | https://aip.enaire.es/AIP/CartasInsigniaImpresas-es.html |
| Netherlands | Aeronautical Chart ICAO The Netherlands | 1:500,000 | PDF holding one raster image, 12280 x 17208 | **No** | Prohibited without written permission | **NOT USABLE as it stands** (free download) | https://www.lvnl.nl/diensten/aip/downloads |
| Norway | Norway VFR Aeronautical Chart ICAO | 1:500,000 | ArcGIS dynamic MapServer (export image) | Yes, custom LCC / WGS84 | Prohibited without written permission | **NOT USABLE as it stands** (free to view) | https://avigis.avinor.no/agsmap/rest/services/ICAO_500000_ExB/MapServer |
| Norway | M517-AIR (military VFR) | 1:250,000 | NOT CHECKED (behind click-through) | NOT CHECKED | Prohibited (no copying for distribution) | **NOT USABLE** | https://partner.avinor.no/en/ais/m517/ |
| Iceland | Iceland Aeronautical Chart ICAO | 1:500,000 | Georeferenced PDF; vector or raster NOT CHECKED | Yes per publisher | Prohibited (private or corporate use only) | **NOT USABLE as it stands** (free, click-through) | https://www.avians.is/en/c-preflight-information/kort |
| France | SCAN OACI / carte OACI-VFR | 1:500,000 | WMTS JPEG tiles z6-z11 | Yes (Web Mercator tiles) | Prohibited; public digital use needs a paid licence | **NOT USABLE** | https://data.geopf.fr/private/wmts |
| Germany | ICAO-Karte | 1:500,000 | Paper; viewer inside a registered portal | n/a | Prohibited (no derived works, no third-party websites) | **NOT USABLE** | https://ais.dfs.de/pilotservice/service/information/disclaimer/disclaimer.jsp |
| Italy | OACI-CAI (10 sheets) | 1:500,000 | Paper; AIP charts behind login | n/a | Not published free | **NOT USABLE** | https://www.aeronautica.difesa.it/pubblicazioni-aeronautiche/ |
| Belgium | LowAir (M-534) | 1:250,000 | Paper | n/a | Not published free | **NOT USABLE** (paid) | https://shop.ngi.be/nl/low-air/ |
| Luxembourg | none of its own | | | | | **NOTHING FOUND** | https://ana.gouvernement.lu/ |
| Portugal | ANC-ICAO Porto, Lisboa, Madeira; Azores | 1:500,000; Azores 1:1,000,000 | Paper, or digital on a USB drive | NOT CHECKED | Not published free | **NOT USABLE** (paid) | https://ais.nav.pt/order-charts/ |
| Finland | ANC 1:500 000 | 1:500,000 | Paper, and inside a commercial app | n/a | Not published free | **NOT USABLE** (paid) | https://www.ais.fi/en/other-products-and-services |
| Sweden | Aeronautical Chart ICAO | 1:500,000 | Paper | n/a | Not published free | **NOT USABLE** (paid) | https://aro.lfv.se/content/eaip/default.html |
| United Kingdom | Aeronautical Charts ICAO; Topographical Air Charts | 1:500,000; 1:250,000 | Paper via stockists | n/a | Not published free | **NOT USABLE** (paid) | https://nats-uk.ead-it.com/cms-nats/opencms/en/Charts/vfr-charts/ |
| Ireland | VFR Aeronautical Chart | 1:500,000 | Paper, ordered by e-mail | n/a | Not published free | **NOT USABLE** | https://www.iaa.ie/commercial-aviation/airspace/aeronautical-charts |
| Malta | none identified | | | | | **NOTHING FOUND** (AIP page blocked) | https://maltats.com/aim/ |
| Greenland | none: no ANC is produced | | | | | **NOT USABLE** (does not exist) | https://aim.naviair.dk/media/files/fx5ay3ckjr5/BG_GEN_3_2_en.pdf |

**Ranking for the build:**

1. **Switzerland** is the only source that is clean on every count.
2. **Denmark with the Faroes** is free, georeferenced and vector, with no licence
   stated either way.
3. **Austria** is free for non-commercial use but is an ungeoreferenced raster.
4. **Spain, the Netherlands, Norway and Iceland** publish free charts and forbid
   reuse without written permission. Spain is the best of these technically.

---

## Switzerland (and Liechtenstein)

**Verdict: USABLE.**

- **Publisher:** Federal Office of Topography swisstopo, in cooperation with
  skyguide (collection id `ch.bazl.luftfahrtkarten-icao`, so FOCA/BAZL is the
  data owner).
- **Series:** Aeronautical Chart ICAO Switzerland 1:500,000. One sheet.
  Coverage bbox 5.339 E to 10.855 E, 45.540 N to 47.908 N, which contains all of
  Liechtenstein; no separate Liechtenstein publisher was looked for.
- **Second series:** Glider chart (Segelflugkarte), one sheet, 35 m/px. My
  recollection is that it is a 1:300,000 chart, but that is UNVERIFIED; the
  file's 254 dpi tag with 35 m pixels would imply 1:350,000.
- **Index (STAC API), verified 200:**
  - https://data.geo.admin.ch/api/stac/v0.9/collections/ch.bazl.luftfahrtkarten-icao/items
  - https://data.geo.admin.ch/api/stac/v0.9/collections/ch.bazl.segelflugkarte/items
- **Direct downloads, verified by HEAD:**
  - `https://data.geo.admin.ch/ch.bazl.luftfahrtkarten-icao/luftfahrtkarten-icao/luftfahrtkarten-icao_total_50_2056.tif`
    -> 200, 148,478,328 bytes, Last-Modified 2026-03-06.
  - `https://data.geo.admin.ch/ch.bazl.segelflugkarte/segelflugkarte/segelflugkarte_total_35_2056.tif`
    -> 200, 248,042,082 bytes, Last-Modified 2026-03-11.
- **Variants:** each chart ships as four files: `total` (the combined chart),
  `basemap`, `theme` (airspace and ATC information) and `obstacles`. `total` is
  the one to tile.
- **Format, read with GDAL over `/vsicurl/` (header reads only; neither file
  was downloaded, both being over the 100 MB sample limit):**
  - ICAO: GeoTIFF, COG layout, LZW, 3-band RGB, **8250 x 5200 px, 50 m/px**,
    CRS **CH1903+ / LV95 (EPSG:2056)**, origin (2443000, 1308500), internal
    overviews to 258 x 163.
  - Glider: same layout, **11300 x 7200 px, 35 m/px**, EPSG:2056.
  - Whether a collar or legend is inside the georeferenced extent was
    NOT CHECKED (no pixels were viewed).
- **Resolution in pipeline terms:** 50 m/px is coarser than the FAA sectionals'
  42.3 m/px, so native zoom is about z11 at this latitude.
- **Edition and update cycle:** STAC `properties.datetime` is
  **2026-03-19**; the description says the chart is normally revised annually.
- **Discovery by script:** the asset URLs are stable and carry no edition, so
  fetch the STAC item and compare `properties.datetime` (or the asset's
  `checksum:multihash`) with what was last built.
- **Access:** open, no registration, no key.
- **Licence:** swisstopo "Terms of use for free geodata and geoservices (OGD)",
  https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices
  (linked from the STAC collection as `rel: license`). The terms say the data
  "may be enriched and processed and also used commercially", and that use,
  distribution and making accessible are allowed. A source reference is
  mandatory, for example "(c) swisstopo". The STAC `license` field itself reads
  `proprietary`, which is just STAC's label for a non-SPDX licence.
- **Redistribution of derived tiles:** appears **permitted**, with attribution.

## Denmark, with the Faroe Islands

**Verdict: USABLE WITH CAVEATS** (licence not stated anywhere I looked).

- **Publisher:** Naviair, AIM.
- **Series and sheets:**
  - ICAO ANC 1:500,000 Denmark, one sheet, Edition 46.
  - ICAO ANC 1:250,000 Copenhagen Area, one sheet, Edition 45.
  - ICAO ANC 1:250,000 The Faroe Islands, one sheet, Edition 3.
- **Index page, verified 200 (12,528 bytes):** https://aim.naviair.dk/charts/
- **Direct downloads, all verified 200 by HEAD:**

  | File | Bytes |
  |---|---|
  | `/media/j1ybrcqb/edition-46_20260903-icao-anc-1-500000-denmark-geo-tiff.tif` | 37,048,512 |
  | `/media/43sh4hbk/edition-46_20260903-icao-anc-1-500000-denmark-pdf.pdf` | 37,500,877 |
  | `/media/etjhr5fe/edition-46_20260416-icao-anc-1-500000-denmark-printed-version-geo-tiff.tif` | 37,049,648 |
  | `/media/xamfremp/edition-46_20260416-icao-anc-1-500000-denmark-printed-version-pdf.pdf` | 37,015,208 |
  | `/media/a0povyem/edition-45_20260416-icao-anc-1-250000-copenhagen-area-geo-tiff.tif` | 21,680,126 |
  | `/media/pynh4m4z/edition-45_20260416-icao-anc-1-250000-copenhagen-area-pdf.pdf` | 9,050,456 |
  | `/media/fzlddgob/edition-3_20260122-icao-anc-1-250000-faroe-islands-geo-tiff.tif` | 11,111,000 |
  | `/media/1zknzfzc/edition-3_20260122-icao-anc-1-250000-faroe-islands-pdf.pdf` | 10,569,184 |

  All under `https://aim.naviair.dk`.
- **Two flavours of each chart.** "Printed version" is the paper edition as
  issued at its AIRAC date. "Digital Charts" is the same edition re-issued just
  before each AIRAC date with the hand amendments from AIP GEN 0.5 applied. The
  digital one (20260903 above) is the one to build from.
- **The PDF is true vector, and georeferenced.** Measured on the downloaded
  Denmark 1:500,000 PDF: one page of 1030 x 898 mm holding **226,485 path
  objects, 24,968 text objects and only 14 images, the largest 256 x 256 px**.
  It carries an ISO 32000 geospatial viewport over the whole page, with the
  projection as WKT and the four corner coordinates. Those corners match the
  GeoTIFF's corners, so **the GeoTIFF is this page rasterised at 400 dpi**.
  This is the IFR situation over again: render from the vector PDF at whatever
  scale the target zoom needs, and unlike the FAA's PDFs the registration is
  already in the file. The Copenhagen and Faroe PDFs were NOT CHECKED but come
  from the same production.
- **GeoTIFF format, from the downloaded sample and `/vsicurl/` header reads:**
  - Denmark 1:500,000: **palette-indexed** (1 band, 256 colours), PackBits,
    **16222 x 14144 px, 31.75 m/px**. CRS embedded, no EPSG code: Lambert
    Conformal Conic, standard parallels 54 deg 40' and 57 deg 20', central
    meridian 11 E, WGS84. Its CRS *name* is the misleading `GCS_WGS_1984`,
    though it is projected.
  - Faroe Islands: palette, **17783 x 14483 px, 10.583 m/px**, LCC with
    parallels 62.25 / 61.5, central meridian 6 deg 50' W, WGS84.
  - Copenhagen Area: palette, **14717 x 13933 px, 10.583 m/px**.
- **Map area, from a thumbnail of the PDF:** the sheet has a white collar, and
  the title and legend panel is printed over the **north-east corner** of the
  map, so the map area is L-shaped. A mask, not a rectangle.
- **Edition and update cycle:** Edition 46 effective AIRAC 16 APR 2026; digital
  re-issue for AIRAC 03 SEP 2026. Amended copies each AIRAC when there are
  changes.
- **Discovery by script:** the URLs are **not stable**. Each carries a random
  Umbraco media id (`/media/j1ybrcqb/`) plus edition and date in the file name,
  so parse the index page for `href` values and take the latest date per chart.
  The page marks unchanged charts "No changes" / "Ingen aendringer" and links
  the earlier file again.
- **Access:** open, no registration.
- **Licence:** **none found**, in four places looked:
  - the charts page and the AIM home page carry no terms;
  - GEN 3.2 of AIP Denmark, of the VFR Flight Guide and of AIP Faroe Islands
    (all verified 200) only name the paper reseller, AEROpartner;
  - the chart's own text has a copyright line for the Swedish base data only
    (Lantmateriet). A thumbnail shows an imprint block naming Naviair and the
    Danish Agency for Data Supply and Infrastructure, which was not read in
    full.
- **Redistribution of derived tiles:** **unclear.** Ask Naviair
  (aim@naviair.dk) before publishing.
- **Samples kept:** `samples/dk_icao500_ed46_20260903.tif` and
  `samples/dk_icao500_ed46_20260903.pdf`.

## Greenland

**Verdict: NOT USABLE, because the chart does not exist.**

- **Publisher:** Naviair, AIM (AIP Greenland).
- **Source, verified 200 (104,222 bytes):**
  https://aim.naviair.dk/media/files/fx5ay3ckjr5/BG_GEN_3_2_en.pdf, dated
  03 OCT 24, AIRAC AMDT 10/24.
- **Finding:** GEN 3.2 section 4 states that no Aeronautical Chart - ICAO (ANC)
  is being produced for AIP Greenland at present. The series that are produced
  are aerodrome, approach and landing charts only.
- **Discovery note:** Naviair's AIP documents are listed by a JSON API,
  `/umbraco/api/naviairapi/getnodesforparent?parentId=` and
  `/umbraco/api/naviairapi/getsearch?criterion=...`, both verified 200. That is
  the way to find any AIP page there; the site is otherwise script-driven.

## Austria

**Verdict: USABLE WITH CAVEATS.** Free for non-commercial use, but a raster with
no georeferencing, and the terms do not address redistribution.

- **Publisher:** Austro Control.
- **Series:** Luftfahrtkarte - ICAO 1:500,000 (2252-A) Osterreich. One sheet,
  front and back. The page notes the chart is not part of the AIP.
- **Index page, verified 200 (107,137 bytes):**
  https://www.austrocontrol.at/icao_karte
- **Direct downloads, verified 200** (relative to the page's
  `<base href="/jart/prj3/ac/main.jart">`):
  - Front: `https://www.austrocontrol.at/jart/prj3/ac/data/dokumente/ICAO500_20260319_v1-0_VS_rgb_digital_2026-03-19_1003848.pdf`
    -> 200, **25,882,706 bytes** as downloaded (the server sends no
    Content-Length), Last-Modified 2026-03-19.
  - Back: `.../data/dokumente/ICAO500_20260319_v1-0_RS_cmyk_2026-03-19_1003232.pdf`
    -> 200.
- **Format, measured on the downloaded front:** the PDF is a wrapper round
  **one raster image of 14704 x 10216 px**, with no vector paths and no text
  objects (producer "Adobe Acrobat Image Conversion Plug-in"). On a page of
  1245 x 865 mm that is 300 dpi, so **42.33 m/px** at 1:500,000 -- the same as
  the FAA sectionals.
- **Georeferencing: none.** No geospatial dictionary of any kind in the file.
- **Map area, from a thumbnail:** a full printed sheet. White collar with notes
  above and below, a title panel cut into the north-west corner of the map, and
  a neatline that follows the graticule, so it is tilted and curved rather than
  square to the pixels.
- **What registering it would take:** control points from the printed
  graticule, then the collar masked, as the sectionals were. The projection is
  NOT CHECKED (it will be on the sheet).
- **Edition and update cycle:** Ausgabe 2026, valid from 2026-03-19, version
  1.0. Annual. A change list against the previous year is published beside it.
- **Discovery by script:** parse the index page; the file name carries the
  edition date, a version and a numeric id.
- **Access:** open. The page shows a disclaimer as text; there is no tick-box or
  accept button in front of the download.
- **Licence:** on the same page. Paraphrased: Austro Control provides the PDF
  for non-commercial purposes; commercial use of the files or of the data in
  them is allowed only with Austro Control's express approval; requests for
  commercial reuse go to an address given on the page.
- **Redistribution of derived tiles:** **unclear.** A free public site is
  arguably non-commercial, but the terms grant use, not republication. Ask.
- **Not the chart:** "Onlinekarte VFR Austria" at https://maps.austrocontrol.at
  is an interactive vector map in Web Mercator that sits behind a "Continue to
  the Application" step. It was not entered.
- **Sample kept:** `samples/at_icao500_2026_front.pdf`.

## Spain

**Verdict: NOT USABLE as it stands.** Free, georeferenced, vector and easy to
script, but the site terms forbid reuse without ENAIRE's prior written
authorisation. Worth a permission request.

- **Publisher:** ENAIRE, Aeronautical Information Division (AIS).
- **Series:** Cartografia Aeronautica VFR500, 1:500,000, whole Spanish
  territory. The page says seven sheets; the download list has seven sheet
  pairs plus a Melilla zip.
- **Index page, verified 200 (24,023 bytes):**
  https://aip.enaire.es/AIP/CartasInsigniaImpresas-es.html
- **Direct downloads, all verified 200 by HEAD, under
  `https://aip.enaire.es/recursos/descargas/VFR500/`:**

  | Sheet | Zip (TIF + TFW) bytes | PDF bytes |
  |---|---|---|
  | `2025_GC_CANARIAS` | 11,899,187 | 3,577,831 |
  | `2025_LE1_NORTE` | 55,730,337 | 18,040,277 |
  | `2025_LE2_NORDESTE` | 37,333,895 | 12,676,705 |
  | `2026_LE3_ESTE` | 30,382,860 | 10,847,934 |
  | `2026_LE4_CENTRONORTE` | 48,098,435 | 24,905,409 |
  | `2026_LE5_CENTROSUR` | 64,120,392 | 34,882,031 |
  | `2026_LE6_SUR` | 44,710,730 | 19,411,525 |
  | `2026_MELILLA` | 965,957 | (none listed) |

  Also `VFR500_Index_Map.pdf` (1,489,344 bytes) and `VFR500_Changes.pdf`
  (144,141 bytes), both 200. About 293 MB of zips in total.
- **GeoTIFF format, from the downloaded Canarias sample:** the zip holds
  `2025_GC_CANARIAS.tif` and `.tfw`. **4-band RGBA**, LZW,
  **11811 x 5906 px, 42.333 m/px**. The CRS is embedded as well as the world
  file: a custom Lambert Conformal Conic named `ENR_Canarias` (parallels 24 and
  29, origin 26 N 17 W, WGS84), no EPSG code.
- **The PDF is vector, and georeferenced.** Measured on the Canarias PDF
  (made by ArcGIS Pro): **16,509 path objects, 1,290 text objects and 439
  images, the largest 1977 x 256 px**. The images are small tiles, which looks
  like a shaded base under vector aeronautical linework; that reading is
  UNVERIFIED. The file has **four geospatial viewports**, each with its own
  projection as WKT. Two were read: a key map and a Melilla inset, both in a
  peninsula LCC (`ENR_Peninsula`: parallels 37 and 42, origin 40 N 4 W). The
  main map's viewport was not singled out.
- **Layout, from a thumbnail:** the PDF page is 2008 x 508 mm with the map on
  the left half and the legend on the right. The GeoTIFF's 2:1 shape suggests it
  is the map half alone; NOT CHECKED by viewing the TIFF.
- **Edition and update cycle:** edition year is in the file name; at present
  three sheets are 2025 and four are 2026, so sheets are re-issued
  individually. Last-Modified on the 2026 zips is 2026-05-28.
- **Discovery by script:** parse the index page for
  `recursos/descargas/VFR500/*.zip`; the year prefix changes with each edition.
- **Access:** open, no registration.
- **Licence:** ENAIRE legal notice, https://www.enaire.es/aviso_legal, section 6
  (intellectual property), read directly. Paraphrased: ENAIRE holds the rights
  in the site and its content, and any reproduction, adaptation, modification,
  communication to the public or other exploitation is strictly prohibited
  unless ENAIRE has authorised it in writing beforehand. Section 11 adds that
  the AIP site is the official text and that some sections state their own uses
  and limitations; the charts page states none. The chart's own text credits
  the topographic base to the Instituto Geografico Nacional.
- **Redistribution of derived tiles:** **prohibited** without written
  authorisation.
- **Samples kept:** `samples/es_vfr500_2025_GC_CANARIAS.zip` (extracted to
  `samples/es_canarias/`) and `samples/es_vfr500_2025_GC_CANARIAS.pdf`.

## Netherlands

**Verdict: NOT USABLE as it stands.** Free PDF, but ungeoreferenced raster and
the terms forbid reproduction without LVNL's written permission.

- **Publisher:** LVNL (Air Traffic Control the Netherlands), AIS.
- **Series:** Aeronautical Chart ICAO 1:500,000 The Netherlands, Lambert
  conformal conic. One sheet, front and back. Edition 2026, valid from
  19 MAR 2026.
- **Index pages, verified 200:**
  - https://www.lvnl.nl/diensten/aip (49,365 bytes), which says the chart is
    available free of charge on the downloads page.
  - https://www.lvnl.nl/diensten/aip/downloads (43,503 bytes).
- **Direct downloads, verified by HEAD:**
  - `https://eaip.lvnl.nl/download/lvnl_icao_2026_FRONT.pdf` -> 200,
    29,051,898 bytes, Last-Modified 2026-03-19.
  - `https://eaip.lvnl.nl/download/lvnl_icao_2026_BACK.pdf` -> 200,
    3,485,364 bytes.
  - The previous year's name, `lvnl_icao_2025_FRONT.pdf`, is now **404**, so
    old editions are withdrawn.
- **Format, measured on the downloaded front:** made in InDesign. The map is
  **one raster image of 12280 x 17208 px**; around it are only 46 paths and 63
  text objects, which are the title block. On a page of 614 x 860 mm that is
  about 508 dpi, so roughly **25 m/px** at 1:500,000 -- finer than the FAA
  sectionals.
- **Georeferencing: none** in the file.
- **Map area, from a thumbnail:** the map bleeds to the page edge on all sides,
  with a title panel over the north-west corner and a scale bar down the west
  side. No white collar.
- **Edition and update cycle:** annual, in March. Corrections between editions
  are listed in eAIP GEN 3.2 section 8.
- **Discovery by script:** parse the downloads page; the year is in the file
  name.
- **Access:** open, no registration. Paper copies are sold by the KNVvL
  webshop.
- **Licence:** https://www.lvnl.nl/diensten/aip/copyright-en-disclaimer
  (verified 200). Paraphrased: all AIS publications are LVNL's property and no
  part may be reproduced in any form, electronic included, without LVNL's
  written permission; the site's content may not be copied, published or
  adapted without consent. The chart itself reserves copyright in the
  aeronautical information to LVNL and in the topographic base to the Kadaster.
- **Redistribution of derived tiles:** **prohibited** without written
  permission.
- **VFR chart viewer:** https://vfrchart.lvnl.nl/ (verified 200) is described
  as an interactive view of the amended chart, updated each AIRAC cycle
  (currently "effective date: 03 Sep 2026"). Its configuration shows it is
  assembled from seven dynamic ArcGIS map services under
  `https://geoservices.lvnl.nl/arcgis/rest/services/VFRchart/` (Aerodrome,
  Airspaces, FIS, Miscellaneous, Navaids, Obstacles, Routes), in EPSG:4326,
  not tile-cached, copyright text "LVNL 2020". It is **vector layers, not a
  chart raster**, so it would not reproduce the printed chart.
- **Sample kept:** `samples/nl_icao500_2026_front.pdf`.

## Norway

**Verdict: NOT USABLE as it stands.** Freely viewable and technically
harvestable, but the viewer's terms allow private use only.

- **Publisher:** Avinor (AIS).
- **Series:** Norway VFR Aeronautical Chart ICAO 1:500,000. Served as one
  seamless mosaic; sheet count not checked.
- **Index page, verified 200:** https://partner.avinor.no/en/ais/homepage/
  ("NORWAY AERONAUTICAL CHART ICAO 1:500 000 - See map here"), which links to
  the ArcGIS Experience
  https://experience.arcgis.com/experience/41465e716c9e4a458e168f81a8961a74.
- **Service behind it, verified 200:**
  `https://avigis.avinor.no/agsmap/rest/services/ICAO_500000_ExB/MapServer`
  - ArcGIS Server 11.3, capabilities `Query,Map,Data`.
  - **Dynamic, not tile-cached.** It is fetched through `/export`, at most
    4096 x 4096 px per request, in PNG, JPG or TIFF among others.
  - CRS: custom Lambert Conformal Conic, WGS84, central meridian 9 E, standard
    parallels 59 deg 40' and 69 deg 20'.
  - Full extent in that CRS: x -279,558 to 898,780, y 6,386,282 to 8,033,535.
  - Layers: a mosaic layer named after the edition, with Boundary, Footprint
    and Image sublayers.
  - Native raster resolution: NOT CHECKED.
- **Example request, verified 200, 1,419,805 bytes, image/png:**
  `.../ICAO_500000_ExB/MapServer/export?bbox=100000,6650000,164000,6714000&size=1024,1024&format=png24&f=image&dpi=96`
  The result was viewed: it is the real ICAO chart (Oslo/Gardermoen area), crisp
  at 62.5 m/px.
- **Edition and update cycle:** layer 0 is named **`AIRAC_19MAR26`** and the
  viewer reads "Effective date: 19-MAR-2026". A second service,
  `.../ICAO_500000/MapServer`, holds `AIRAC_20MAR25`, so the chart looks annual.
- **Discovery by script:** read `MapServer?f=json` and take the name of layer 0.
- **Access:** open, no registration, no key.
- **Licence:** the terms are in the viewer's own text widget. Paraphrased: all
  rights in the chart belong to Avinor, and any use other than the private use
  the terms describe is prohibited without Avinor's written permission.
- **Redistribution of derived tiles:** **prohibited** without written
  permission.
- **M517-AIR, 1:250,000:** the Air Force's military VFR chart, offered free at
  https://partner.avinor.no/en/ais/m517/ (verified 200). The download is a
  box.com link behind an "I agree to the above terms" click, so it was **not
  followed**. Its terms say it must not be changed or copied for distribution
  or commercial use. NOT USABLE.
- **Sample kept:** `samples/no_icao500_export_sample.png` (one 1024 px export).

## Iceland

**Verdict: NOT USABLE as it stands.** Free georeferenced PDF, but behind a
click-through disclaimer whose terms forbid redistribution.

- **Publisher:** Isavia ANS, now branded Avians.
- **Series:** Iceland Aeronautical Chart - ICAO, 1:500,000. Printed chart
  released January 2026; a PDF version is offered free.
- **Index page, verified 200:**
  https://ans.isavia.is/en/c-preflight-information/kort, which redirects to
  https://www.avians.is/en/c-preflight-information/kort.
- **Direct URL, verified by HEAD only:**
  `https://ans-isavia.cdn.prismic.io/ans-isavia/aeeBDsBOoF08xLd9_DIGITAL_AERONAUTICALCHART__2026.pdf`
  -> 200, 12,703,578 bytes, application/pdf, Last-Modified 2026-04-21.
- **Vector or raster: NOT CHECKED, and not checkable under the rules.** The
  page reveals the link only after ticking "I have read and accept the
  disclaimer". Reading any part of the file would be accepting those terms by
  the back door, so it was not fetched in either pass. Someone who is entitled
  to accept the disclaimer can settle this in a minute.
- **Format:** PDF, described by the publisher as georeferenced (usable in Adobe
  Reader and Avenza-style apps).
- **Edition and update cycle:** "Version 01.2026"; updated "as deemed
  necessary".
- **Discovery by script:** parse the page's embedded JSON for the
  `cdn.prismic.io` file link; the name carries the year and a random prefix.
- **Licence:** the disclaimer on the same page. Paraphrased: the chart is
  issued only for private or corporate use, and unauthorised distribution,
  reproduction or sale is prohibited.
- **Redistribution of derived tiles:** **prohibited** without authorisation.

## France

**Verdict: NOT USABLE.** The known lead is real but is not open data.

- **Publisher:** IGN, with aeronautical data from the SIA (DGAC).
- **Series:** SCAN OACI, the assembled and georeferenced raster of the four
  1:500,000 OACI-VFR sheets (941, 942, 943, 944), metropolitan France. The WMTS
  layer title is currently "carte OACI-VFR 2026".
- **Where it is served:** *not* on the public Geoplateforme endpoint. The
  public capabilities (`https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetCapabilities`,
  verified 200, 2,949,557 bytes) contain no OACI layer. The chart is on the
  restricted endpoint:
  `https://data.geopf.fr/private/wmts?SERVICE=WMTS&REQUEST=GetCapabilities&apikey=ign_scan_ws`
  -> verified 200, 279,705 bytes, layer
  `GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN-OACI`.
- **Format:** WMTS, `image/jpeg`, tile matrix set `PM_6_11` -- Web Mercator,
  **zoom 6 to 11 only**. The downloadable product is in Lambert-93
  (EPSG:2154).
- **Example tile:** `...&REQUEST=GetTile&LAYER=GEOGRAPHICALGRIDSYSTEMS.MAPS.SCAN-OACI&STYLE=normal&FORMAT=image/jpeg&TILEMATRIXSET=PM&TILEMATRIX=10&TILEROW=352&TILECOL=518`
  -> with `apikey=ign_scan_ws` 200, 33,852 bytes, image/jpeg; **without a key
  401**. The one tile fetched to verify this was deleted afterwards.
- **Edition and update cycle:** annual, each April. Metadata publication date
  2026-04-16.
- **Access:** an API key. `ign_scan_ws` is a shared transitional key that
  appears in public documentation and works, but the metadata says the proper
  route is a cartes.gouv.fr account, membership of the SCAN user community
  (company or association, SIRET number) and a personal key.
- **Licence:** "Conditions de licence" for SCAN 25, SCAN 100 and SCAN OACI,
  https://data.geopf.fr/annexes/ressources/documentation/conditions-de-licence.pdf
  (25 pages, amended 26 March 2026). Paraphrased:
  - The data are not free of rights. Private individuals are not authorised to
    download them, even for personal use.
  - The free licence covers professional or associative *end use* only.
  - Using the data in a digital product or service aimed at the general public,
    **free or paid**, needs a separate paid licence from IGN's sales units.
- **Redistribution of derived tiles:** **prohibited** without that paid
  licence.
- **Not checked:** whether the SIA itself publishes anything free at
  1:1,000,000 or 1:250,000; French overseas territories.

## Germany

**Verdict: NOT USABLE.** Sold on paper, and DFS's terms rule out derived works
and use on other websites in so many words.

- **Publisher:** DFS Deutsche Flugsicherung; sold through its subsidiary
  Eisenschmidt.
- **Series:** ICAO-Karte 1:500,000 Deutschland, a new edition every spring;
  the 2026 edition was published 19 March 2026. A glider edition (metric) and a
  night low-flying edition also exist. Sheet count: my recollection is eight,
  UNVERIFIED. DFS also mentions "V500" charts for other countries and
  Aeronautical Area Charts at 1:250,000.
- **Pages, verified 200:**
  - https://www.dfs.de/homepage/de/medien/ifr-vfr-informationen/vfr-informationen/informationen-zur-neuen-icao-karte-2026/
    (57,895 bytes)
  - https://www.eisenschmidt.aero/faq-icao-karte/
  - https://aip.dfs.de/basicVFR/ (AIP VFR, free online; redirects to a dated
    path, currently `BasicVFR/2026SEP17/`)
  - https://ais.dfs.de/pilotservice/service/information/disclaimer/disclaimer.jsp
    (11,898 bytes)
- **Availability:** paper only. Two digital appearances, neither usable:
  - A search snippet says the chart can be viewed in DFS's AIS portal (WebAUP,
    and a "VFReBulletin" that needs free registration). The WebAUP map URL it
    gave is now **404**; the portal has register and login pages. Not entered.
  - Eisenschmidt offers one free PDF, the **Stuttgart sheet of the 2025
    edition**, issued because that sheet was reprinted. Its note limits it to
    flight preparation and asks for a prior enquiry before any use in physical
    or digital products. One outdated sheet; not downloaded.
- **Licence:** the AIS portal disclaimer. Paraphrased: chart and map material in
  the portal and in the AIP is protected; commercial use is not permitted;
  **creating derived works, and use on third-party websites in particular,
  needs DFS's written approval**; and operating the portal with automated tools
  is not permitted, AIXM downloads excepted.
- **Redistribution of derived tiles:** **prohibited** without written approval.
- **Not found:** a GEN 3.2 chart list. The online AIP VFR's GEN 3 has no such
  page in its contents, and the IFR AIP was NOT CHECKED.

## Italy

**Verdict: NOT USABLE.** The national 1:500,000 series is sold, and the AIP is
behind a login.

- **Publishers:** two.
  - **CIGA (Aeronautica Militare)** makes the official chart.
  - **ENAV** publishes the AIP.
- **Series:** OACI-CAI (Carta Aeronautica d'Italia), 1:500,000, **10 sheets**
  (F1 to F10), elevations in feet, updated annually. The catalogue lists
  edition "34 CIGA", 2024. The same page lists the military LFC-ITA (1:500,000,
  7 sheets) and JOG-AIR (1:250,000), and digital CADRG/ASRP versions of those.
- **Page, verified 200 (415,347 bytes):**
  https://www.aeronautica.difesa.it/pubblicazioni-aeronautiche/
- **Availability:** sold. The page publishes a price list of maximum prices for
  authorised resellers
  (`.../wp-content/uploads/2025/05/CARTO_Listino_prezzi_20250513.pdf`, not
  opened) and quotation request forms for individuals and businesses.
- **ENAV AIP:** `https://onlineservices.enav.it/enavWebPortalStatic/AIP/AIP/enr/enr6/ENR6.htm`
  returns **302 to `auth.enav.it`**, so a login is required. A search snippet
  says registration is free and that ENR 6 holds VFR charts as PDF; that was
  **not checked**, as it needs an account.
- **Licence:** NOT CHECKED (moot, nothing free to download).

## Belgium

**Verdict: NOT USABLE** (sold, not published free).

- **Publishers:** skeyes (AIM Belgium) for the AIP; the National Geographic
  Institute (NGI/IGN) for the VFR chart.
- **Series:** LowAir, **1:250,000** (military designation M-534), Lambert 2008,
  covering Belgium and part of the border regions, airspace shown up to
  4500 ft. **Edition 35, 2026**, annual. The 2026 edition is printed west on
  the front and east on the back. There is no Belgian 1:500,000 ICAO chart in
  the AIP's chart list, and GEN 3.2 states the 1:1,000,000 WAC is not available
  for Belgium or Luxembourg.
- **Pages, verified 200:**
  - GEN 3.2: https://ops.skeyes.be/html/belgocontrol_static/eaip/eAIP_Main/html/eAIP/EB-GEN-3.2-en-GB.html
    (31,604 bytes)
  - ENR 6: `.../eAIP/EB-ENR-6-en-GB.html` (20,395 bytes). Its charts are
    en-route and index charts only; none is a VFR topographic chart.
  - NGI shop: https://shop.ngi.be/nl/product/lowair-geplooid/ (136,750 bytes).
- **Availability:** paper, from the NGI webshop, price class EUR 19.00 to
  37.00. No digital download was found.
- **Licence:** "(c) 2026 NGI-IGN, all rights reserved" on the shop page.
- **Warning for scripts:** skeyes' firewall answered the first request of the
  session with **403 "Too many requests"** and a 15 to 30 minute pause; a retry
  later succeeded. The address is probably shared.

## Luxembourg

**Verdict: NOTHING FOUND.**

- Luxembourg has no AIP of its own: its aerodromes are in the AIP Belgium and
  Luxembourg (skeyes).
- The Administration de la navigation aerienne site,
  https://ana.gouvernement.lu/ (verified 200, 98,252 bytes), has no charts or
  AIS section among its links.
- The Belgian LowAir chart covers "part of the border regions"; whether that
  includes all of Luxembourg was NOT CHECKED.
- In practice Luxembourg would be covered by a neighbour's sheet, none of which
  is usable (Belgium, Germany, France).

## Portugal

**Verdict: NOT USABLE** (paid).

- **Publisher:** NAV Portugal, Aeronautical Information Service.
- **Series:** ANC-ICAO 1:500,000 Portugal Mainland, two sheets, Porto (2318)
  and Lisboa (2347); 1:500,000 Madeira Archipelago (2418/2419); and
  **1:1,000,000** Azores Archipelago (2350/2351).
- **Pages, verified 200:**
  - GEN 3.2 (7,444 bytes):
    https://ais.nav.pt/wp-content/uploads/AIS_Files/eVFR_Current/eVFR_Online/eAIP/html/eAIP/LP-GEN-3.2-en-GB.html
  - Order page (77,581 bytes): https://ais.nav.pt/order-charts/
- **Prices, from the order page:**

  | Chart | Print | Digital (USB drive) |
  |---|---|---|
  | Portugal mainland (2318/2347) | EUR 30 | EUR 60 |
  | Azores archipelago (2350/2351) | EUR 25 | EUR 50 |
  | Madeira archipelago (2418/2419) | EUR 25 | EUR 50 |

- **Availability:** an order form (name, tax number, address, captcha) and
  payment by bank transfer. The digital format is **a USB drive sent by post**,
  not a download. Its file format is not stated.
- **Licence:** "(c) 2023 NAV Portugal" on the page; terms NOT CHECKED (moot).
- **Free but not the target:** the VFR Manual (eVFR) is free online and holds
  visual approach and aerodrome charts only.

## Finland

**Verdict: NOT USABLE** (sold, not published free).

- **Publisher:** Fintraffic ANS, Aeronautical Information Service.
- **Series:** ANC 1:500 000, eight sheets, all dated 16 APR 2026: Helsinki West
  (2103D), Helsinki East (2103C), Vaasa (2103A), Kuopio (2103B), Oulu (2091D),
  Rovaniemi (2091A), Ivalo (2052C), Southern Finland (2103CD).
- **Pages, verified 200:**
  - https://www.ais.fi/en/other-products-and-services
  - https://www.ais.fi/eaip/currently_effective/eAIP/EF-GEN%203.2-en-GB.html
    (1,969,418 bytes), section 6.
- **Availability:** sold by Karttakauppa
  (https://www.karttakauppa.net/c/tuotteet/ilmailukartat) and distributed in
  electronic form inside the Air Navigation Pro app. No ANC file is linked from
  the eAIP.
- **Licence:** https://www.ais.fi/en/about-website. Paraphrased: Fintraffic ANS
  owns the copyright; aeronautical *data* may be refined further without fee or
  agreement, but use of maps elsewhere must always be agreed separately.

## Sweden

**Verdict: NOT USABLE** (sold, not published free).

- **Publisher:** LFV.
- **Series:** Aeronautical Chart ICAO 1:500,000, Lambert conical, seven sheets,
  information date 20 MAR 2025: Malmo, Goteborg, Stockholm, Gavle, Sundsvall,
  Lulea, Kiruna.
- **Pages, verified 200:**
  - eAIP entry: https://aro.lfv.se/content/eaip/default.html
  - GEN 3.2: `https://aro.lfv.se/content/eaip/AIP%20AMDT%201-2026_2026_08_07/eAIP/ES-GEN%203.2-en-GB.html`
    (33,035 bytes).
- **Availability:** GEN 3.2 section 3 names Kartforlaget 1985 AB as the source.
  No digital download is offered.
- **Not the chart:** LFV eCharts / Dronechart (https://daim.lfv.se/echarts/) is
  an interactive vector view of AIP data for drone pilots.

## United Kingdom

**Verdict: NOT USABLE** (sold, not published free).

- **Publisher:** NATS Aeronautical Charts and Data, under licence from the CAA.
- **Series:** Aeronautical Charts ICAO 1:500,000, and Topographical Air Charts
  of the United Kingdom 1:250,000 (Transverse Mercator, to 5000 ft). Sheet
  counts were not read off the page; my recollection of 3 and 8 is UNVERIFIED.
- **Pages, verified 200:**
  - https://nats-uk.ead-it.com/cms-nats/opencms/en/Charts/vfr-charts/
  - https://nats-uk.ead-it.com/cms-nats/opencms/en/Charts/vfr-charts/Resources/
  - GEN 3.2, from the 2025-03-20 AIRAC (an old cycle; the current one was
    NOT CHECKED).
- **Availability:** paper charts through six named stockists. The only free
  downloads are chart amendments, frequency reference cards, a VFR obstacle
  list and a CSV/KMZ of unlicensed aerodromes -- data, not charts.

## Ireland

**Verdict: NOT USABLE** (not published digitally).

- **Publisher:** Irish Aviation Authority; the AIP is published by AirNav
  Ireland.
- **Series:** VFR Aeronautical Chart 1:500,000, ANC/500, **Edition 13**, sheet
  2172 ABCD, dated 06 AUG 2026, covering the Shannon FIR. One sheet.
- **Pages, verified 200:**
  - https://www.iaa.ie/commercial-aviation/airspace/aeronautical-charts
  - https://www.airnav.ie/AIRAC_SEPT_2026/2026-09-03-AIRAC/html/eAIP/EI-GEN-3.2-en-IE.html
- **Availability:** an encapsulated folded paper chart, ordered by e-mail. The
  IAA page has **no download link**. A search snippet claimed the chart is free
  to download from that page; that is not what the page says now.
- **Stale links:** AirNav's eAIP path changes every cycle; take it from
  https://www.airnav.ie/air-traffic-management/aeronautical-information-management.

## Malta

**Verdict: NOTHING FOUND**, with the main source unreadable.

- **Publishers:** Transport Malta (Civil Aviation Directorate) publishes the
  AIP; Malta Air Traffic Services (MATS) runs AIM.
- **Pages:**
  - https://maltats.com/aim/ -> verified 200 (78,565 bytes). It describes the
    AIP as supplied free to foreign authorities and by **paid subscription** to
    everyone else, and links no charts.
  - https://www.transport.gov.mt/aviation/air-navigation-services-aerodromes/aeronautical-information-publication-3764
    -> **403** to every request, from two different clients. NOT CHECKED as a
    result.
- **Series:** none identified. No official Maltese 1:500,000 or 1:250,000 VFR
  chart turned up in any search; the only charts found for Malta are from a
  commercial publisher. Whether AIP Malta's GEN 3.2 lists one is NOT CHECKED.

---

## Remaining gaps

| Gap | Why | What would close it |
|---|---|---|
| Iceland PDF: vector or raster | Behind an accept-the-disclaimer tick-box | Someone entitled to accept it opens the file |
| Malta AIP GEN 3.2 | Transport Malta's page returns 403 | A browser visit |
| Germany's sheet list | Not in the online AIP VFR's contents | The IFR AIP's GEN 3.2, or DFS's shop |
| Exact neatlines and collars | Thumbnails only, no measurement | The detection work each series needs anyway |
| Italy ENR 6 charts | Behind a login | An account holder checks what ENR 6 holds |
| UK sheet counts and current GEN 3.2 | Read from an old cycle | Re-read the current cycle |

## Notes for whoever picks this up

- **Permission requests are the main lever.** Spain, the Netherlands, Norway and
  Iceland each publish a free chart and forbid reuse without written
  permission; Denmark states nothing; Austria allows non-commercial use without
  saying whether that covers republication. Six e-mails could turn one usable
  country into seven.
- **Two sources are vector PDFs with the registration already inside:** Denmark
  and Spain. They fit the existing `render_pdfs.py` approach and would skip the
  `detect_pdf_windows.py` registration step the FAA's PDFs needed. GDAL in this
  venv has **no PDF driver**, so the viewport has to be read another way; the
  corner coordinates and WKT are plain text in the file.
- **Two sources are rasters with no registration at all:** Austria and the
  Netherlands. They need control points before anything else.
- **Custom LCC projections everywhere.** Denmark, the Faroes, Spain and Norway
  each embed their own Lambert Conformal Conic with no EPSG code. GDAL read all
  of them correctly from the GeoTIFFs.
- **Working files** are in the session scratchpad under `research/ewn/` (saved
  index pages, capabilities, licence texts, helper scripts) and
  `research/samples/` (the samples named above, plus a `_thumb.jpg` of each
  PDF).
- **Shared scratch directory hazard:** running Python with `research/` as the
  working directory failed once because a file there shadowed the standard
  library's `inspect` module. Run with `python -P`, or from another directory.
