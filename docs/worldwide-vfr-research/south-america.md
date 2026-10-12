# World-wide VFR research: South America

Researched 2026-09-27. Every HTTP status and size below was observed on that
date with `curl` (browser user agent) unless marked UNVERIFIED or NOT CHECKED.
Nothing was logged into, registered for, or submitted.

Licence sentences are **paraphrased in English** with a pointer to where they
sit, except for one verbatim quotation (Brazil). Read the source before relying
on any of them.

## Summary

| Country | Series | Scale | Format | Georeferenced | Licence verdict | Overall verdict | Key URL |
|---|---|---|---|---|---|---|---|
| Brazil | WAC (46 sheets) | 1:1,000,000 | GeoTIFF (RGB, 300 dpi) and vector GeoPDF | Yes (GeoTIFF EPSG:4326; PDF LCC/WGS84) | Unclear, leaning permitted (CC BY 4.0 badge vs. restrictive 2019 policy) | **USABLE WITH CAVEATS** | https://geoaisweb.decea.mil.br/ |
| Brazil | CNAV (91 sheets, partial coverage, 1985-2026) | 1:500,000 | Vector GeoPDF | Yes (UTM or LCC, WGS84) | Same as above | USABLE WITH CAVEATS (patchy, many sheets 30+ years old) | https://aisweb.decea.mil.br/?i=cartas&p=visuais |
| Brazil | CAP / CIAP | 1:250,000 | On request only | n/a | n/a | NOT USABLE (request form, must state purpose) | same |
| Argentina | WAC / ICAO 1:500,000 | 1:1M / 1:500k | Not published ("in development") | n/a | n/a | **NOT USABLE** (nothing to download) | https://ais.anac.gob.ar/aip |
| Argentina | VFR chart below TMA Baires, TMA Cordoba (2 sheets) | 1:500,000 | GeoPDF (vector + raster strips) | Yes (LCC, WGS84) | Unclear (no terms found) | USABLE WITH CAVEATS (two terminal areas only) | https://ais.anac.gob.ar/aip |
| Chile | SAF aeronautical charts (6 + 24 + 80 sheets) | 1:1M, 1:500k, 1:250k | TIFF / GeoTIFF, sold | Yes (paid option) | All rights reserved | **NOT USABLE** (paid) | https://www.saf.cl/preguntas/ |
| Colombia | WAC / "CNO COLFAC" (3 sheets) | 1:1,000,000 | PDF wrapping one 13000 x 9053 raster | No | **Prohibited** without written permission (notice printed on chart) | **NOT USABLE** without permission | https://eaip-colombia.atnaerocivil.gov.co/eaip/ |
| Ecuador | WAC 2951, WAC 2953 (2 sheets); ANC (5 sheets) | 1:1M; 1:500k | Sold as a set | Unknown | n/a | **NOT USABLE** (paid, USD 40) | https://www.ais.aviacioncivil.gob.ec/ifis3/aip/GEN%203.2 |
| Uruguay | none produced | - | - | - | - | NOTHING FOUND | https://www.dinacia.gub.uy/ais/aip-uruguay |
| Paraguay | none (WAC index "NIL") | - | - | - | - | NOTHING FOUND | https://www.dinac.gov.py/v3/index.php/ais/aip-paraguay |
| Bolivia | unknown | - | AIP behind login | - | - | NOT USABLE (login) | http://ais.naabol.gob.bo/ |
| Peru | unknown | - | eAIP behind bot protection | - | - | NOT VERIFIED (blocked) | https://eaip-peru.corpac.gob.pe/ |
| Venezuela | WAC | 1:1,000,000 | Not online; obtained from IGVSB / SNA | - | - | NOT USABLE (no download) | https://www.inac.gob.ve/eaip/history-en-GB.html |
| Guyana | unknown | - | AIP not online | - | - | NOTHING FOUND | http://www.gcaa-gy.org/guyana-aip.html |
| Suriname | unknown | - | No chart downloads found | - | - | NOTHING FOUND | https://cadsur.sr/ais/ |
| French Guiana | Carte VFR Guyane (1 sheet) | 1:740,000 | Paper, sold | No | n/a | **NOT USABLE** (paid) | https://www.sia.aviation-civile.gouv.fr/ |

**Bottom line: Brazil is the only country in the region with a free,
georeferenced, country-wide VFR series.** It is also by far the largest
country, so the one usable source covers roughly half the continent.

---

## Brazil - DECEA / ICA (AISWEB and GeoAISWEB)

**Publisher.** Departamento de Controle do Espaco Aereo (DECEA), charts
produced by the Instituto de Cartografia Aeronautica (ICA).

### Series

Counts are from the table on the AISWEB visual-charts page, which listed 769
entries.

| Type | Name | Scale | Entries | Downloadable | Effective dates |
|---|---|---|---|---|---|
| WAC | Carta Aeronautica Mundial | 1:1,000,000 | 46 | Yes | 2024 (20), 2025 (23), 2026 (3) |
| CNAV | Carta de Navegacao Aerea Visual | 1:500,000 | 91 | Yes | 1985-1993 (59), 2008-2013 (11), 2020-2021 (14), 2025-2026 (7) |
| CINAV | Carta Imagem de Navegacao Aerea Visual | 1:500,000 | 39 | Yes | 1993-2010 |
| CAP | Carta Aeronautica de Pilotagem | 1:250,000 | 398 | **No link** | 1981-2026 |
| CIAP | Carta Imagem Aeronautica de Pilotagem | 1:250,000 | 146 | **No link** | 1992-2006 |
| REA / REH / REAST / REUL | Special VFR routes and corridors | various | 26 / 12 / 10 / 1 | Yes | 2003-2026 |

The WAC set is complete and current: the 46 sheet numbers on AISWEB match the
46 GeoTIFF names on GeoAISWEB one for one. CNAV coverage is **partial** and its
extent was NOT CHECKED (an index-map PDF exists, below). CAP and CIAP must be
requested through the SAC DECEA form stating the chart number, purpose,
institution, role and an e-mail address, so they are not openly available.

### URLs and verification

| What | URL | Status | Size |
|---|---|---|---|
| Visual charts index | https://aisweb.decea.mil.br/?i=cartas&p=visuais | 200 | 445,915 (GET) |
| WAC PDF example | https://aisweb.decea.mil.br/cartas/visuais/wac/sao-paulo_wac_20250807.pdf | 200 | 6,193,113 |
| WAC PDF, newest | https://aisweb.decea.mil.br/cartas/visuais/wac/corumba_wac_20260903.pdf | 200 | 12,370,718 |
| **WAC GeoTIFF example** | https://geoaisweb.decea.mil.br/src/geotiffs/WAC_3262_SAO_PAULO.tif | 200 | 174,612,467 |
| WAC GeoTIFF | https://geoaisweb.decea.mil.br/src/geotiffs/WAC_3434_RIO_DA_PRATA.tif | 200 | 198,835,512 |
| WAC GeoTIFF | https://geoaisweb.decea.mil.br/src/geotiffs/WAC_2825_CABO_ORANGE.tif | 200 | 180,299,339 |
| CNAV PDF, new style | https://aisweb.decea.mil.br/cartas/visuais/cnav/recife_cnav_20251225.pdf | 200 | 7,254,677 |
| CNAV PDF, old style | https://aisweb.decea.mil.br/cartas/visuais/cnav/6232_fev13.pdf | 200 | 2,379,827 |
| CINAV PDF | https://aisweb.decea.mil.br/cartas/visuais/cinav/6183_abr07.pdf | 200 | 27,043,266 |
| WAC index map | https://aisweb.decea.mil.br/download/?public=9a0c71a7-7ee9-4308-864d2d45ccc28e91.pdf&p=WAC | 200 | not sent |
| CNAV index map | https://aisweb.decea.mil.br/download/?public=7fb06530-e000-4e49-b935881f6c13947d.pdf&p=CNAV | 200 | not sent |
| GeoAISWEB page (lists every GeoTIFF) | https://geoaisweb.decea.mil.br/ | 200 | 187,300 |
| WMS capabilities | https://geoaisweb.decea.mil.br/geoserver/ows?service=WMS&version=1.3.0&request=GetCapabilities | 200 | 1,194,283 |
| Usage policy | https://ajuda.decea.mil.br/app/uploads/2019/04/Pol%C3%ADtica-de-Uso-POR.pdf | 200 | 144,367 |

The GeoTIFF server sends `Accept-Ranges: bytes` and a `Last-Modified` header.
The usage-policy link in the AISWEB footer points at `ajuda.decea.gov.br`,
which **did not resolve**; the same path on `ajuda.decea.mil.br` works.

### Format

**WAC GeoTIFF** (read remotely through `/vsicurl/`, header only; the file is
over the 100 MB sample limit so it was not downloaded):

- 7873 x 5250 px, 3-band RGB Byte, no alpha, apparently uncompressed.
- **EPSG:4326**, pixel 0.000761932 degrees both ways: about 84.8 m north-south,
  about 78.6 m east-west at 22 S. Native Web Mercator zoom about **10.85, so
  z11**.
- Corners (-50.0008, -20.0012) to (-44.0022, -24.0013): **already cropped to
  the 6 x 4 degree neatline**, with no collar, legend or margin. No map-area
  detection would be needed.
- Stripped (block 7873 x 256), seven internal overviews,
  `TIFFTAG_DATETIME=2025:06:09`, 300 dpi tag.
- Being already resampled to geographic coordinates means one resampling has
  happened before ours. Text is at 300 dpi of a 1:1M sheet.

**WAC PDF** (sample downloaded: `samples/br_wac_sao-paulo.pdf`):

- One page, 32.13 x 22.72 in, **true vector**: 79,420 path objects, 6,926 text
  objects, **no raster images**.
- ISO 32000 geospatial viewport (`/VP`, `/Measure`, `/GPTS`). Projection from
  the embedded WKT: Lambert Conformal Conic, central meridian -47, latitude of
  origin -22, standard parallels -20.667 and -23.333, WGS84.
- Whole sheet including collar and legend; the viewport `BBox` gives the map
  frame.
- This repo's GDAL build cannot open PDFs (its PDF driver reports no read
  backend), so the georeferencing was read out of the PDF dictionary directly.
  `render_pdfs.py`'s pdfium route would apply, with the affine derived from
  `GPTS`/`LPTS` rather than registered against a GeoTIFF.

**CNAV PDFs** (ranged reads only): vector, georeferenced, no raster images
seen in the sampled ranges. Old sheets were made in Bentley Map and are in
**UTM** (zone 22S and 20S seen); new sheets are from Esri ArcGIS Pro 3.2 and
carry two viewports. There are **no CNAV GeoTIFF downloads**; the GeoServer
exposes only 10 CNAV sheets as WMS layers.

**Tile service.** The GeoServer publishes `ICA:WAC_<number>_<NAME>` for all 46
sheets, plus CNAV, REA and REH layers. The capabilities document states fees
"none" and access constraints "none". Downloading the GeoTIFFs is simpler than
harvesting a WMS.

### Editions and discovery

- Sheets are reissued **individually** on AIRAC dates, not as a set. The page
  header read "AMDT 39/26".
- AISWEB's table gives amendment, publication date and effective date per
  sheet, and the PDF file name ends in the effective date (`_wac_YYYYMMDD`).
- GeoTIFF names are stable (`WAC_<number>_<NAME>.tif`), so a script should
  compare `Last-Modified` (or `TIFFTAG_DATETIME`) against what it holds. The
  sheet list can be scraped from the GeoAISWEB page, which names all 130 files
  under `src/geotiffs/`.
- **The GeoTIFF may lag the PDF.** Sao Paulo's GeoTIFF was last modified
  2025-08-11 for a PDF effective 2025-08-07, but whether every reissue gets a
  new GeoTIFF was NOT CHECKED.

### Access

Open. No registration, key or click-through for the PDFs, GeoTIFFs or WMS. The
**AISWEB API does need a key** (returns a parameter error without one), and the
policy says the API may be charged for commercial use. The API is not needed
for charts.

### Licence

Two statements, which do not agree:

1. The AISWEB footer carries a **Creative Commons BY 4.0** badge linking to
   http://creativecommons.org/licenses/by/4.0/.
2. The *Politica de Uso* (2019, URL above) is narrower. Section 10 opens by
   prohibiting any use not regulated or authorised by the policy, then says:
   "A impressão e distribuição do conteúdo total ou parcial, sem fins
   comerciais, são permitidas" - non-commercial printing and distribution of
   all or part of the content is allowed. The same section lets users with
   authorised API access store the data and distribute it over the Internet.
   Section 12 reserves copyright to the Union / DECEA. Section 4 says the
   services are free. Section 8 says no registration is needed for products
   other than flight plans and the API.
3. **Section 13(b) treats the use of robots, spiders, crawlers or similar
   extraction tools, or anything imposing excessive load, as a violation.**
   That bears directly on an automated fetch stage.

**Redistribution of derived tiles: unclear, leaning permitted** for a
non-commercial site with attribution. The CC BY badge would settle it, but it
is a footer image rather than a statement in the policy, and the policy's text
is older and tighter. Worth an e-mail to DECEA (SAC) before publishing.

### Verdict: USABLE WITH CAVEATS

Georeferenced, neatline-cropped, current, complete and free. Caveats: the
licence ambiguity; the anti-crawler clause (fetch slowly, with conditional
requests); and size, 46 uncompressed files of 175-200 MB, roughly 8.5 GB.

---

## Argentina - ANAC

**Publisher.** Administracion Nacional de Aviacion Civil, Departamento
Informacion Aeronautica.

### What exists

AIP GEN 3.2 (AMDT AIRAC 2/2024, 28 Nov 2024) lists the *World Aeronautical
Chart - ICAO 1:1,000,000* and *Aeronautical Chart - ICAO 1:500,000*, but for
both the list of available charts says to see an index graphic that is **"in
development"**, and the two index pages are blank placeholders. No sheet of
either series is in the AIP. Search results describe older CAA (1:1M) and CAAT
(1:500k) series; those were NOT found for download.

What the AIP does hold at 1:500,000:

| Chart | AIP ref | Amendment | URL |
|---|---|---|---|
| VFR chart below TMA Cordoba | ENR 6.9 | 01/26, 11 Jun 2026 | https://ais.anac.gob.ar/descarga/aip-69e0c63aa2607 |
| VFR chart below TMA Baires | ENR 6.10 | 01/26, 11 Jun 2026 | https://ais.anac.gob.ar/descarga/aip-69e0c66807e4e |

### URLs and verification

| What | URL | Status | Size |
|---|---|---|---|
| AIP index | https://ais.anac.gob.ar/aip | 200 (GET); **HEAD returns 405** | 10,306 |
| Section lists | https://ais.anac.gob.ar/aip/gen , `/aip/enr` , `/aip/ad` | 200 only with `X-Requested-With: XMLHttpRequest`; 404 without | 65,451 / 189,333 / 6,180,901 |
| GEN 3.2 | https://ais.anac.gob.ar/descarga/aip-6700449c6d157 | 200 | 270,647 |
| ENR 6.10 TMA Baires | https://ais.anac.gob.ar/descarga/aip-69e0c66807e4e | 200 | 2,754,406 |
| ENR 6.9 TMA Cordoba | https://ais.anac.gob.ar/descarga/aip-69e0c63aa2607 | 200 | 36,237,673 |

The server **ignores `Range`** and rejects `HEAD`, so sizes come from GET
response headers.

### Format

Sample `samples/ar_enr6-10_vfr_tma_baires.pdf`: one page, 31.5 x 18.9 in, made
in Esri ArcMap 10.9.1. 6,957 paths, 5,392 text objects and 61 image strips of
6141 x 86 px (a raster background of about 6141 x 5246 px cut into bands).
**Georeferenced**: LCC, central meridian -57, standard parallels -32.66 and
-35.33, WGS84, with corners at about 35.83 S - 33.86 S, 59.67 W - 56.79 W. The
georeferencing dictionary is inside a compressed object stream, so a plain
byte search of the file misses it.

### Editions and discovery

Download ids (`aip-<hex>`) change with each amendment, so a script must read
the `/aip/enr` listing (with the AJAX header) and match on the "ENR-6.9" and
"ENR-6.10" labels. AIRAC cycle.

### Access and licence

Open, no login. **No terms of use were found** on the AIS site; its footer
names ANAC only. GEN 3.1 section 3.7 says publications are obtained from the
website around the clock. Whether argentina.gob.ar's general terms apply was
NOT CHECKED. **Redistribution: unclear.**

A third party (argiepilot.com) already converts ANAC's PDFs to MBTiles for
ForeFlight, citing ANAC's AIP as the source.

### Verdict

**NOT USABLE for national coverage** - the WAC and 1:500,000 series are not
published. The two TMA VFR charts are USABLE WITH CAVEATS (licence unclear,
two terminal areas only).

---

## Chile - DGAC / SAF

**Publisher.** Visual charts are not DGAC's. AIP-Chile GEN 3.2 section 2.4
(AMDT 62, 28 Nov 2024) says the 1:1,000,000, 1:500,000 and 1:250,000 visual
charts are produced and distributed by the **Servicio Aerofotogrametrico
(SAF)** of the Chilean Air Force.

### Series (SAF's own FAQ)

| Scale | Sheets | Years | Coverage |
|---|---|---|---|
| 1:1,000,000 | 6 | 2022 | whole country |
| 1:500,000 | 24 | 2020-2024 | whole country |
| 1:250,000 | 80 | 2020-2024 | whole country |

The product page counts 116 charts in total including Antarctic sheets at
1:1M and 1:2M.

### URLs and verification

| What | URL | Status | Size |
|---|---|---|---|
| AIP home | https://aipchile.dgac.gob.cl/ | 200 | 18,151 |
| AIP GEN 3.2 | https://aipchile.dgac.gob.cl/dasa/aip_chile_con_contenido/ais/1%20GEN%20Parte%201/GEN%203%20Servicios/bGEN%203.2-1%20Cartas%20Aeronauticas.pdf | 200 | 39,598 |
| SAF cartography | https://www.saf.cl/productos/cartografia/ | 200 | 90,771 |
| SAF FAQ with prices | https://www.saf.cl/preguntas/ | 200 | 107,004 |

The lead `aipchile.gob.cl` **does not resolve**; the host is
`aipchile.dgac.gob.cl`.

### Format, access, licence

Sold as laminated print, digital without georeferencing, or digital
georeferenced (TIFF / GeoTIFF). Unit prices, each plus VAT: CLP 33,875
laminated, **CLP 28,622 digital, CLP 33,610 georeferenced digital**. Ordered by
e-mail to ventas@saf.cl or at the sales office. The SAF site footer reserves
all rights. No free download was found; SAF's IDE portal
(https://portalide.saf.cl/home, 200) is a JavaScript application whose layers
were NOT CHECKED.

The AIP itself offers free PDFs of visual approach charts and visual routes
(ENR 7), which are not the target series. Chile's national digital library
holds historical SAF charts, NOT CHECKED further as they are not current.

### Verdict: NOT USABLE - the charts are sold.

---

## Colombia - Aerocivil / Fuerza Aerea Colombiana

**Publisher.** Published in Aerocivil's eAIP; the sheets themselves are the
Colombian Air Force's *Carta de Navegacion Operacional* ("CNO COLFAC"),
edition 1.

### Series

World Aeronautical Chart 1:1,000,000 in **3 sheets** (north, centre, south)
covering the whole country, at eAIP ENR 6.7. No 1:500,000 or 1:250,000 series
appears in ENR 6.

### URLs and verification

| What | URL | Status | Size |
|---|---|---|---|
| eAIP issue list | https://eaip-colombia.atnaerocivil.gov.co/eaip/ | 200 | 5,008 |
| ENR 6.7 page | https://eaip-colombia.atnaerocivil.gov.co/eaip/A%2072-26_2026_07_09/eAIP/ENR%206.7-es-CO.html | 200 | 9,407 |
| North | `.../A%2072-26_2026_07_09/documents/Root_WePub/Colombia/CHARTS/ENR/ENR%206/ENR_6_0/AMDT66/Carta%20aeron%C3%A1utica%20mundial%20norte%201%201.000.000.pdf` | 200 | 17,532,928 |
| Centre | same path, `centro` | 200 | 19,311,138 |
| South | same path, `sur` | 200 | 17,923,744 |

All three had `Last-Modified` 6 Jul 2026. The URL in Aerocivil's 2023
announcement (an `AIRAC AMDT 65-23` folder) now returns 404.

### Format

Sample `samples/co_wac_centro.pdf`: a PDF made by Acrobat's image-conversion
plug-in, wrapping **one 13000 x 9053 px raster** on a 43.33 x 30.18 in page
(300 dpi). **No georeferencing of any kind.** The sheet includes collar,
legend and logos. A 1-degree graticule is printed, so it could be registered by
hand. The projection was NOT read off the sheet.

### Editions and discovery

The AIP page stamp reads ENR 6.7-5, AIRAC effective 16 Apr 2026, A 71/26, but
the **chart content is much older**: the sheet states its aeronautical data
(DAFIF/NGA and own sources) is valid to June 2019, isogonic lines are for 30
Jun 2019, and the base map is IGAC 1:100,000 data of 2011-2017. To discover the
current issue, read the "Currently Effective Issue" link on the issue list
(then `A 72-26_2026_07_09`), then the PDF links on the ENR 6.7 page.

### Access and licence

Open, no login. Aerocivil's announcement of 11 Aug 2023 describes the document
as freely accessible to everyone in the industry. **But the chart itself
carries a legal notice**: the information is licensed to or owned by the
Colombian Air Force and protected by copyright, and its reproduction, copying,
retransmission or inclusion by digital means is prohibited without the Air
Force's prior written authorisation, citing Ley 23 de 1982. Aerocivil's own
copyright policy (https://www.aerocivil.gov.co/publicaciones/4382/, 200) is a
PDF that was NOT read.

**Redistribution: prohibited** without written permission.

### Verdict: NOT USABLE without written permission from the Fuerza Aerea
Colombiana. Free to download, not free to republish; also ungeoreferenced and
seven years stale.

---

## Ecuador - DGAC

**Publisher.** Direccion General de Aviacion Civil, Gestion de Informacion
Aeronautica - Cartografia.

### Series (AIP GEN 3.2)

| Series | Scale | Sheets | Notes |
|---|---|---|---|
| World Aeronautical Chart - ICAO | 1:1,000,000 | 2 | WAC 2951 (mainland, 2 N - 5.5 S, 82 W - 75 W) and WAC 2953 Galapagos |
| Aeronautical Chart - ICAO (ANC) | 1:500,000 | 5 | Tulcan, CAE 2, Nueva Loja, Machala, CAE 5 (Galapagos) |

Both are described as Lambert Conformal Conic.

### URLs and verification

| What | URL | Status | Size |
|---|---|---|---|
| AIP GEN 3.2 | https://www.ais.aviacioncivil.gob.ec/ifis3/aip/GEN%203.2 | 200 | 104,962 |
| AIP ENR 6 | https://www.ais.aviacioncivil.gob.ec/ifis3/aip/ENR%206 | 200 | 82,591 |
| AIC A 001/2026, prices | https://www.ais.aviacioncivil.gob.ec/ifis3/aip/AIC%2001-26 | 200 | 92,706 |

### Access and licence

GEN 3.2.3 says the charts are obtained from the central AIM cartography
office. AIC A 001/2026 (1 Jan 2026) prices the **set of WAC 2951 and WAC 2953
at USD 40**, paid in advance by bank transfer. The 1:500,000 sheets have no
listed price and no download. ENR 6 holds en-route charts only. No direct
download URL exists to verify.

### Verdict: NOT USABLE - sold, not downloadable.

---

## Uruguay - DINACIA

AIP GEN 3.2 (AIRAC AMDT 03, 9 Jul 2026) lists twelve chart series produced and
**none is a WAC, a 1:500,000 or a 1:250,000 visual chart**. The nearest are
visual approach charts at 1:350,000 for eight aerodromes.

| What | URL | Status | Size |
|---|---|---|---|
| AIP index | https://www.dinacia.gub.uy/ais/aip-uruguay | 200 | 44,962 |
| GEN 3 (English) | https://www.dinacia.gub.uy/sites/default/files/aip/2026-07/Gen3%20ing.pdf | 200 | 2,077,646 |
| ENR 6 | https://www.dinacia.gub.uy/sites/default/files/aip/2026-07/Enr6%20esp.pdf | 200 | 17,876,394 |

ENR 6 (sample `samples/uy_enr6.pdf`, 26 pages, vector) holds en-route, area and
index charts. It has PDF viewports but no `GPTS` was found, so it is treated as
not georeferenced. A search-engine summary said copying is prohibited without
authorisation; that was NOT verified against the site.

### Verdict: NOTHING FOUND. Uruguay publishes no chart of the target type.

---

## Paraguay - DINAC

The AIP is one archive: https://www.dinac.gov.py/downloads/AMDT_AIRAC_01_2026.rar
(200, 44,131,270 bytes, `Last-Modified` 10 Jul 2026), linked from
https://www.dinac.gov.py/v3/index.php/ais/aip-paraguay (200). Sample
`samples/py_aip_amdt_airac_01_2026.rar`.

Its GEN 3.2 (28 Nov 2024) section 6, the index to the World Aeronautical Chart
1:1,000,000, reads **"NIL"**. Other charts are referred to the military
geographic service (DISERGEMIL), in person. ENR 6 is three scanned pages with
no text layer. The eAIP host `aixm.dinac.gov.py` did not accept connections.

### Verdict: NOTHING FOUND.

---

## Bolivia - NAABOL (formerly AASANA)

NAABOL's site links its AIP at http://ais.naabol.gob.bo/ (200, 8,342 bytes),
which is a **login form** (user code and password) with a notice about AIP
supplements. Nothing is readable without credentials, so no series, format or
licence could be established. How credentials are issued, and whether they are
free, was NOT CHECKED.

### Verdict: NOT USABLE - login required; contents UNVERIFIED.

---

## Peru - CORPAC

`eaip-peru.corpac.gob.pe` and `portalapp.corpac.gob.pe` answer every request
with **HTTP 307 and a JavaScript challenge** (`Server: Sucuri/Cloudproxy`).
That is bot detection, so it was not worked around, and a fetch script would
meet the same wall. The older `portal2.corpac.gob.pe` has an **expired TLS
certificate**. The gob.pe service page returned HTTP 418 to the fetch tool.

UNVERIFIED, from search-engine summaries only: the eAIP has a GEN 3.2 page
listing chart series, and the gob.pe page says AIP Digital credentials are
obtained by arranging a payment with the AIS office.

### Verdict: NOT VERIFIED. No free chart was found; the site cannot be read by
a script either way.

---

## Venezuela - INAC

eAIP issue list at https://www.inac.gob.ve/eaip/history-en-GB.html (200). GEN
3.2, read from the 28 Dec 2023 issue at
https://www.inac.gob.ve/eaip/2023-12-28/html/eAIP/SV-GEN%203.2-en-GB.html (200,
202,286 bytes), lists a **World Aeronautical Chart 1:1,000,000** series in
Lambert Conformal Conic (standard parallels 7 deg 35 min and 11 deg 55 min). It
says these are obtained from the AIS office at Maiquetia or from the Instituto
Geografico de Venezuela Simon Bolivar. The page links no chart files, and ENR 6
lists en-route, area and index charts only.

The issue list is headed as a specimen not for operational use, and shows the
2020 issue as current with the 2023 one as "next", so the site's upkeep is
doubtful. `www.igvsb.gob.ve` was NOT CHECKED.

### Verdict: NOT USABLE - the series exists but is not downloadable.

---

## Guyana - GCAA

http://www.gcaa-gy.org/guyana-aip.html (200, 24,044 bytes) publishes AICs as
PDFs and, for the AIP itself, only a contact e-mail and telephone number for
the AIM service. No AIP and no charts are online.

### Verdict: NOTHING FOUND.

---

## Suriname - CADSUR / CASAS

https://cadsur.sr/ais/ (200) has an AIP category and a post titled
"AIP-Suriname" (6 Jun 2025, 200, 128,446 bytes), but the static HTML carries no
document link; the page loads a PDF-viewer plug-in, so content may appear only
with JavaScript. No chart series could be identified. CASAS publishes the chart
regulations (CARS Part 15) but no charts were found there.

### Verdict: NOTHING FOUND (JavaScript-rendered content NOT CHECKED).

---

## French Guiana - SIA (France)

Covered by France's AIP CAR SAM NAM. GEN 3.2 (AIRAC 2026-08-06) at
https://www.sia.aviation-civile.gouv.fr/media/dvd/eAIP_03_SEP_2026/CAR-SAM-NAM/AIRAC-2026-08-06/html/eAIP/FR-GEN-3.2-fr-FR.html
(200, 56,472 bytes) lists a **"Carte VFR Guyane 1/740 000"** published by SIA,
alongside a 1:3,500,000 en-route chart. ENR 6 holds the airspace and en-route
charts only; the VFR chart is not in the eAIP.

A reseller lists it as a 2024 paper edition at EUR 17.41
(https://boutique.aero/marques/22-sia). The SIA shop search returned no product
for "guyane", so SIA's own price and any digital edition are UNVERIFIED. The
IGN/SIA OACI 1:500,000 series covers metropolitan France only.

Note the eAIP folder name (`eAIP_03_SEP_2026`) and the AIRAC folder inside it
(`AIRAC-2026-08-06`) differ; the latter comes from the arguments to `init()` in
`home.html`.

### Verdict: NOT USABLE - a single paid paper chart at a non-standard scale.

---

## Countries where nothing free was found

| Country | What was checked | Finding |
|---|---|---|
| Argentina | AIP index, GEN 3.1, GEN 3.2, full ENR list, AD list | WAC and 1:500k "in development"; only two TMA VFR charts |
| Chile | AIP GEN 3.2, SAF product page, SAF FAQ, SAF IDE portal landing page | Sold by SAF |
| Colombia | eAIP issue list, ENR 6 menu, ENR 6.7, one sheet | Free download, republication prohibited |
| Ecuador | AIP GEN 3.2, ENR 6, AIC A 001/2026 | Sold, USD 40 |
| Uruguay | AIP index, GEN 3 (50 pages), ENR 6 (26 pages) | No such series produced |
| Paraguay | AIP page, full AIP archive (GEN 3, ENR 6) | WAC index "NIL" |
| Bolivia | NAABOL catalogue page, AIS portal | Login wall |
| Peru | eAIP, CORPAC portal, old portal, gob.pe page | Bot protection, expired certificate; unverified |
| Venezuela | eAIP issue list, menu, GEN 3.2 | Series exists, not online |
| Guyana | GCAA AIP page | AIP not online |
| Suriname | CADSUR AIS home, AIP category, AIP post | No document links in static HTML |
| French Guiana | SIA site map, eAIP GEN 3.2 and ENR 6, SIA shop search, reseller | Paid paper chart, 1:740,000 |

## Not checked

- Brazil: CNAV coverage extent; whether every WAC reissue gets a new GeoTIFF;
  whether GeoAISWEB has terms of its own (none were seen in its page source).
- Argentina: general terms of argentina.gob.ar; IGN Argentina.
- Any US-government coverage of the region (ONC / TPC / JNC scans, FAA
  Caribbean charts) - outside this brief, but the only realistic filler for
  the countries above. Those would be decades old.

## Notes for the pipeline

- **Brazil's WAC GeoTIFFs need no detection stage.** They are cropped to the
  neatline and in EPSG:4326, so the series is fetch, then tile. `max_zoom` 11
  matches the source (native z10.85).
- The vector PDFs are the higher-quality route, as with the FAA IFR charts,
  and unlike those they carry their own georeferencing. They would need the
  collar masked using the viewport `BBox`.
- Sheets abut on a 6 x 4 degree grid in geographic coordinates; whether
  neighbours overlap was NOT CHECKED.
- Fetch politely. AISWEB's policy names crawlers as a violation and the files
  are large.
- Argentina's server rejects HEAD and ignores Range; Peru's is unreachable to
  scripts. Neither matters unless those sources become usable.

## Sample files

In `scratchpad/research/samples/`: `br_wac_sao-paulo.pdf` (6.2 MB),
`ar_enr6-10_vfr_tma_baires.pdf` (2.8 MB), `co_wac_centro.pdf` (19.3 MB),
`uy_enr6.pdf` (17.9 MB), `py_aip_amdt_airac_01_2026.rar` (44.1 MB). One per
source, all under 100 MB. The Brazilian GeoTIFF was inspected remotely by
ranged reads and not downloaded.
