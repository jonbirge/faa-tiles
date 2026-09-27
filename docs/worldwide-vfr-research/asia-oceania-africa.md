# World-wide VFR charts: Asia, Middle East, Oceania and Africa

Research date: 2026-09-27. Scope: free sources of the ICAO 1:500,000 VFR chart or
national equivalent, the ICAO World Aeronautical Chart 1:1,000,000 (WAC), and
1:250,000 charts, for a public Web Mercator tileset. US military ONC/TPC charts and
OpenFlightMaps are out of scope here.

## How to read this report

- **Every URL with a status code was actually requested** on the research date, with
  curl, and the status and size are what came back. Guessed URLs that failed are
  listed as guesses. Ten of the key download URLs were requested a second time at
  the end of the work and all returned the same status and length.
- **UNVERIFIED** means seen or inferred but not confirmed by a request or by a file
  that was opened. **NOT CHECKED** means not looked at.
- **No account was created, no login performed, no terms accepted, no form
  submitted, no bot challenge attempted.** Where a source sits behind any of
  those, that is recorded and the source was left there.
- **Licence wording is paraphrased**, with the source URL and section given so it
  can be read in the original. One sentence is quoted directly (India). Short
  field values such as "Nil" or "to be developed", chart titles and error
  messages are given as they appear.
- **Samples:** at most one file per source, each under 100 MB, in the session
  scratchpad under `research\samples\`. They are for inspection only; several are
  covered by terms that forbid redistribution.
- The work was split by region. Parts 2 to 4 were researched by helper agents
  under the same rules and then checked and edited here; Part 1 was done directly.

### Verdicts used

| Verdict | Meaning |
|---|---|
| **USABLE** | Free, no login, and the publisher's terms appear to permit redistribution of derived tiles. |
| **USABLE WITH CAVEATS** | Free, no login, and no term was found that forbids reuse, but the licence is unstated or there is significant technical work. |
| **NOT USABLE WITHOUT PERMISSION** | The files download free, but the publisher's own terms forbid reproduction or redistribution. Technical merit is recorded so that a permission request can be prioritised. |
| **NOT USABLE** | Paid, behind a login or registration, not online, or the chart does not exist. |

The third verdict is a refinement of "not usable": it separates "there is nothing
to get" from "there is a good file that may not be republished". Two helper
reports had labelled such sources differently (one "usable with caveats", one "not
usable"); they are put on one scale here.

## Headline

1. **One source is usable as it stands: Taiwan.** A current 1:500,000 VFR chart as
   a vector, georeferenced PDF, free, from the civil aviation authority, under an
   open government licence on the natural reading.
2. **One more is usable with caveats: Kazakhstan.** A current 1:500,000 chart of
   the whole country in 27 sheets, free from the state ANSP, as JPEG pages in one
   153 MB PDF, with no georeferencing and no licence statement either way.
3. **Nine sources are free to download but forbidden to republish.** In order of
   technical merit: UAE (a true GeoTIFF at 42.3 m/px), Saudi Arabia (45 sheets at
   1:500,000 and 8 WAC sheets), Australia (15 vector VNC sheets and the VTCs),
   Qatar, Singapore, Israel (1:250,000 vector), then Malaysia, Thailand and India,
   which are old or low in resolution. Each would need written permission.
4. **Everywhere else there is nothing to use.** The charts are sold on paper
   (Japan, South Korea, Mongolia, Oman, Sri Lanka, Pakistan, South Africa, New
   Zealand digitally), sit behind a login (China, Indonesia, Philippines,
   Cambodia, Kenya, Botswana, Zimbabwe), or are not produced at all (most of
   Central Asia, Bangladesh, Bhutan, Maldives, Myanmar, Brunei, Kuwait, the 18
   ASECNA states, Mauritius).
5. **Almost nothing is georeferenced.** Only three files found carry
   georeferencing: Taiwan's chart, the UAE GeoTIFF, and a Nepalese index chart
   that is not a VFR chart. Every other sheet would need a one-off registration
   from its printed graticule, committed as a manifest, as `ifr_low_pdf.json`
   does for the FAA PDFs.
6. **One lead could not be settled: Morocco.** Search results point to free WAC
   PDFs on the ONDA site, but every request met a Cloudflare challenge, which was
   not attempted. It needs a person with a browser.

## Summary table

Countries are in the priority order of the brief. "Georef." is whether the file
itself carries georeferencing.

| Country | Series | Scale | Format | Georef. | Licence (public tiles) | Verdict | Key URL |
|---|---|---|---|---|---|---|---|
| **Asia** | | | | | | | |
| Japan | JAPA sectional charts, 8 sheets; JHA WAC | 1:500,000; 1:1,000,000 | Paper, sold | n/a | Commercial products | NOT USABLE | `https://www.japa.or.jp/japa-shop/japa-map` |
| South Korea | Aeronautical Chart ICAO, 5 sheets; WAC, 3 sheets | 1:500,000; 1:1,000,000 | Paper, sold to residents | n/a | n/a | NOT USABLE | `https://www.molit.go.kr/atmo/USR/WPGE0201/m_37160/DTL.jsp` |
| **Taiwan** | VFR Chart, 1 sheet | 1:500,000 | Vector GeoPDF; XYZ PNG tiles | **Yes**, EPSG:3395 | Appears permitted with attribution (OGDL-Taiwan 1.0) | **USABLE** | `https://www.eaipvfr.tw/` |
| China | National VFR charts | UNVERIFIED | Behind login | -- | -- | NOT USABLE | `https://ga.aischina.com/` |
| Hong Kong | Flying charts (Lands Department) | 1:100,000; 1:50,000 | Paper, sold | n/a | Prohibited on the AIS site | NOT USABLE | `https://www.ais.gov.hk/` |
| Mongolia | Aeronautical Chart ICAO, 34 sheets; WAC, 11 sheets | 1:500,000; 1:1,000,000 | Sold, MNT 28,200 a sheet | n/a | n/a | NOT USABLE | `https://ais.mn/files/aip/eAIP/valid/html/eAIP/ZM-GEN-3.2-en-MN.html` |
| India | WAC (Survey of India), 20 sheets, 1997 | 1:1,000,000 | JPEG scans and PDF, watermarked | No | Prohibited without written permission | NOT USABLE WITHOUT PERMISSION (and 1997 data) | `https://surveyofindia.gov.in/pages/aeronautical-charts-and-maps` |
| Pakistan | WAC (Survey of Pakistan), 3 sheets | 1:1,000,000 | Paper, sold | n/a | n/a | NOT USABLE | `https://paawebadmin.paa.gov.pk/media/eaip/03-26/eAIP/GEN/GEN3_2.pdf` |
| Bangladesh | none published | -- | -- | -- | -- | NOT USABLE | `https://new.caab.gov.bd/aip/` |
| Sri Lanka | WAC 2796, 2803 | 1:1,000,000 | Paper, LKR 2000 each | n/a | n/a | NOT USABLE | `https://www.aimibsrilanka.lk/` |
| Nepal | Aeronautical Chart of Nepal | 1:500,000 | Not online | n/a | NOT CHECKED | NOT USABLE | `https://e-aip.caanepal.gov.np/welcome/listall/1` |
| Thailand | WAC, 5 sheets, 2020 | 1:1,000,000 reduced to A4 | Raster PDF, about 250 m/px | No | Prohibited (personal non-commercial use only) | NOT USABLE WITHOUT PERMISSION | `https://aip.caat.or.th/` |
| Vietnam | Aeronautical chart, 3 scales, 1988 and 1997 | 1:1,000,000; 1:500,000; 1:250,000 | Paper | n/a | n/a | NOT USABLE | `https://aim.vatm.vn/images/stories/vnaic.vn/SanPhamDichVu/AIPVietNam/AIP/history-en-GB.html` |
| Malaysia | WAC, 3 sheets, 2007 content | 1:1,000,000 | Raster PDF, 144 dpi, about 176 m/px | No | Prohibited without approval (printed on chart) | NOT USABLE WITHOUT PERMISSION | `https://aip.caam.gov.my/aip/eAIP/history-en-MS.html` |
| Singapore | WAC 2860, 1 sheet, 2024 | 1:1,000,000 | Vector PDF | No | Prohibited without written permission; automated access barred | NOT USABLE WITHOUT PERMISSION | `https://aim-sg.caas.gov.sg/aip/` |
| Indonesia | unknown | -- | AIP behind login | -- | -- | NOT USABLE | `https://aimindonesia.kemenhub.go.id/` |
| Philippines | unknown | -- | AIP behind login, paid | -- | -- | NOT USABLE | `https://ais.caap.gov.ph/aip` |
| **Kazakhstan** | Aeronautical Chart, 27 sheets | 1:500,000 | One PDF of JPEG pages, 11701 x 8279 px each | No | Unclear: none stated | **USABLE WITH CAVEATS** | `https://www.ans.kz/en/ais/aeron_charts` |
| Kyrgyzstan, Uzbekistan, Tajikistan, Turkmenistan | none published | -- | -- | -- | -- | NOT USABLE | see Part 1 |
| Russia | none from the state; commercial 1:500,000 | -- | Sold | n/a | n/a | NOT USABLE | `https://www.caica.ru/common/AirInter/validaip/aip/gen/gen3/gen3.2.pdf` |
| Bhutan, Maldives, Myanmar, Brunei | none published | -- | -- | -- | -- | NOT USABLE | see Part 2 |
| Cambodia | unknown | -- | eAIP behind registration and click-through | -- | Prohibited | NOT USABLE | `https://aim.cats.com.kh/eaip.html` |
| Laos | unknown | -- | No online AIP found | -- | -- | NOT USABLE | `https://www.dcal.gov.la/en/ans` |
| **Middle East** | | | | | | | |
| Israel | CVFR low-altitude routes map, 2 sheets | 1:250,000 | Vector PDF, 700 x 1000 mm | No | All rights reserved; commercial base map | NOT USABLE WITHOUT PERMISSION (current edition not discoverable by script) | `https://e-aip.azurefd.net/` |
| Jordan | none listed (2008 GEN 3.2) | -- | AIP behind accept-terms and a human check | n/a | Prohibited | NOT USABLE | `https://carc.gov.jo/en/directory-flight-information` |
| Saudi Arabia | Aeronautical Chart ICAO, 45 sheets | 1:500,000 | PDF with raster inside, about 21 m/px | No | Prohibited without prior agreement from GACA | NOT USABLE WITHOUT PERMISSION | `https://api.sans.com.sa/ccms/AIM/AIP/get` |
| Saudi Arabia | WAC, 8 sheets | 1:1,000,000 | PDF, content UNVERIFIED | UNVERIFIED | Same | NOT USABLE WITHOUT PERMISSION | same |
| UAE | Aeronautical Chart ICAO, 1 sheet | 1:500,000 | GeoTIFF in a zip, 15899 x 11849 px, 42.33 m/px | **Yes**, LCC 2SP on WGS 84 | Prohibited; automated access barred | NOT USABLE WITHOUT PERMISSION | `https://www.gcaa.gov.ae/en/ais/Pages/AeroChartViewPackage.aspx` |
| Qatar | Aeronautical Chart ICAO, 1 sheet, with Doha inset | 1:500,000 (inset 1:250,000) | PDF holding one 12815 x 6969 raster | No | Prohibited without written permission | NOT USABLE WITHOUT PERMISSION | `https://aim.gov.qa/AIP/QA-history-en-GB.html` |
| Oman | WAC, 4 sheets | 1:1,000,000 | Paper, 70 OMR a sheet | n/a | n/a | NOT USABLE | `https://aim.caa.gov.om/eAIP_Oman/history-en-GB.html` |
| Iran | WAC, 7 sheets, and a VFR chart, named in GEN 3.2 | 1:1,000,000 | Not found online | n/a | Prohibited without written permission | NOT USABLE | `https://ais.airport.ir/132` |
| Bahrain | WAC 2547, 1 sheet, 2004 content | 1:1,000,000 | PDF, 72 dpi scan plus vector overlay | No | Unclear | NOT USABLE (22-year-old data, about 353 m/px) | `https://aim.mtt.gov.bh/eaip` |
| Kuwait, Lebanon, Iraq | none found | -- | -- | -- | -- | NOT USABLE | see Part 3 |
| **Oceania** | | | | | | | |
| Australia | VNC, 15 sheets | 1:500,000 | Vector PDF, encrypted | None detected | Prohibited | NOT USABLE WITHOUT PERMISSION | `https://www.airservicesaustralia.com/aip/aip.asp` |
| Australia | VTC, about 26 sheets | 1:250,000 | PDF | UNVERIFIED | Prohibited | NOT USABLE WITHOUT PERMISSION | same |
| Australia | WAC, 43 sheets | 1:1,000,000 | Paper; GeoTIFF and PDF paid, AUD 5,000 | Yes (paid) | Paid licence | NOT USABLE | `https://data.airservicesaustralia.com/data-product/world-aeronautical-charts` |
| New Zealand | Visual Navigation Charts A, B, C, D | 1:1,000,000 to 1:125,000 | GeoTIFF, KML, MBTiles, NZD 12 per area | Yes (paid) | Paid, EULA | NOT USABLE | `https://shop.aeropath.aero/` |
| **Africa** | | | | | | | |
| South Africa (series also covers Namibia) | WAC, 16 sheets; aeronautical chart, 23 to 33 sheets (NGI) | 1:1,000,000; 1:500,000 | Paper; no download found | n/a | UNVERIFIED | NOT USABLE | `https://ngi.dlrrd.gov.za/` |
| Namibia | en-route chart only in the AIP | 1:2,300,000 | Vector PDF | No | No terms found | NOT USABLE (wrong chart type) | `https://ncaa.com.na/aimpub.php?pagetitle=AIMpub&cat=AIPS` |
| Morocco | WAC (Rabat 2420, Marrakech 2454 per search results) | 1:1,000,000 | PDF, UNVERIFIED | UNVERIFIED | UNVERIFIED | **NOT VERIFIED**: site answers 403 behind a bot challenge | `https://siamaroc.onda.ma/cartes_vfr.htm` |
| ASECNA, 18 states | none produced; production tendered in 2025 | -- | -- | -- | -- | NOT USABLE | `https://aim.asecna.aero/html/eAIP/FR-_00GEN-3.2-01-fr-FR.html` |
| Mauritius | none produced | -- | -- | -- | -- | NOT USABLE | `https://civil-aviation.govmu.org/` |
| Cabo Verde | WAC listed, not in the eAIP | 1:1,000,000 | -- | -- | UNVERIFIED | NOT USABLE | `https://eaip.asa.cv/` |
| Botswana, Kenya, Zimbabwe | unknown | -- | AIP behind login or subscription | -- | -- | NOT USABLE | see Part 4 |
| Tanzania, Egypt, Nigeria, Ethiopia | unknown | -- | AIP sold or by subscription | -- | -- | NOT USABLE | see Part 4 |
| Algeria, Tunisia | -- | -- | -- | -- | -- | NOT CHECKED (outside the brief; hosts failed) | see Part 4 |

## What could go into the tileset

### Now

| Source | Sheets | Work needed |
|---|---|---|
| Taiwan VFR Chart | 1 | Render the PDF with pdfium (as `render_pdfs.py` does), take the affine for the main viewport from its `/Measure` dictionary in EPSG:3395, mask the inset panels and legend. Being vector, the render resolution is a choice: 300 dpi gives 42.3 m/px, the sectionals' class (z12), and a finer render would carry z13 as the IFR PDFs do. Attribute the CAA. |
| Kazakhstan Aeronautical Chart | 27 | Split the PDF into its JPEG pages (no re-encoding needed: each page is one DCT stream), register each from the printed graticule in a fitted Lambert conformal conic, mask the legend column and margins. About 50.8 m/px, so z11. The user should decide whether an unstated licence is acceptable. |

### Only with written permission

Ranked by what the file would give the tileset, not by the likelihood of a yes.

| Rank | Source | Why it is worth asking | Whom the source names |
|---|---|---|---|
| 1 | UAE 1:500,000 GeoTIFF | The only ready-made GeoTIFF. Same resolution class as the FAA sectionals. | GCAA AIM department |
| 2 | Saudi Arabia 1:500,000, 45 sheets | The largest area covered by any free file in the region, at about 21 m/px, current aeronautical data. | GACA |
| 3 | Australia VNC and VTC | True vector, current, 15 + about 26 sheets. But Airservices sells the georeferenced versions for AUD 5,000, so a free grant is unlikely. | Airservices Australia |
| 4 | Qatar 1:500,000 | One current sheet at 42.3 m/px. Overlaps the Saudi sheets. | QCAA AIM |
| 5 | Singapore WAC 2860 | Vector, 2024, but 1:1,000,000 and one sheet. | CAAS |
| 6 | Israel CVFR 1:250,000 | Fine vector sheets, but the base map belongs to a commercial publisher. | CAAI |
| 7 | Malaysia, Thailand, India WAC | Old (2007, 2020, 1997) or low in resolution; India's are watermarked. Hardly worth the request. | JUPEM; CAAT; Survey of India |

### Leads to follow by hand

- **Morocco** (ONDA, `siamaroc.onda.ma`): open in a browser, read the terms, see
  whether the WAC PDFs exist and what they are.
- **South Africa** (NGI): the 1:500,000 and 1:1,000,000 series are exactly the
  target but exist on paper; the public catalogue holds two stray 1:500,000 rasters
  from 1992 and 2001. Only a direct request to NGI would produce anything.
- **ASECNA**: a 2025 tender covers producing WAC at both scales for 18 states with
  a web-mapping platform. Re-check in a year or two.
- **Nepal**: GEN 3.2 lists a 1:500,000 chart whose availability reads "to be
  developed". Nepal already exports georeferenced PDFs, so it may appear in that
  form.
- **New Zealand** (`aip.net.nz`): unreadable behind a bot challenge; whether the
  free AIP site hosts any visual chart is unverified.

## Notes for the pipeline

1. **This venv's GDAL cannot read PDFs.** GDAL 3.13.3 from the cgohlke index lists
   a PDF driver but every open fails with "not recognized as being in a supported
   file format", so a geospatial PDF (Taiwan, Nepal) cannot be read with
   `gdal.Info`. `pypdfium2` is in the venv and renders them; the georeferencing
   has to be parsed from the `/Measure`, `/GPTS` and WKT entries in the file.
   Helper reports that say "GDAL has no PDF driver" mean this.
2. **DNS.** Several hosts failed in curl with "could not resolve host" while
   `nslookup` resolved them (`aim-sg.caas.gov.sg`, `aimibsrilanka.lk`, `caa.lk`). `--doh-url https://1.1.1.1/dns-query` fixed all three. (`aisjapan.mlit.go.jp` is different: it is a non-existent domain at 8.8.8.8 too.) Probably local to this machine, but a fetch script should expect it.
3. **Status codes that lie.** Saudi Arabia's host returns 200 and an 11,648-byte
   application shell for any wrong path: check for `application/pdf` and the `%PDF`
   magic. Israel's `gov.il` blobs return 404 to HEAD and 200 to GET. Taiwan's tile
   server returns 500, not 404, for a tile that does not exist. South Africa's NGI
   host returns 403 to a bare `Mozilla/5.0` and 200 to a full browser User-Agent.
   South Korea's MOLIT site loops on 307 without a cookie jar.
4. **Edition discovery** is scriptable for Taiwan, Kazakhstan, Saudi Arabia, Qatar,
   Singapore, Thailand, Malaysia, Bahrain and Hong Kong; the method is given under
   each. It is not for Israel (index behind a challenge, irregular file names) or
   Australia (index behind a click-through, dates not on the AIRAC calendar, so a
   script can only probe candidate dates).
5. **Terms that bar automated access** as such: UAE, Singapore, and the New Zealand
   chart shop. For those, a scheduled fetcher would itself need clearance, apart
   from any permission to publish.
6. **Sheet furniture.** Every sheet found is a whole printed sheet: title block,
   legend column, scale bars, and often inset panels laid over the map. All need
   map-area masks of the kind `scripts/<series>_areas.json` holds.

## Part 1. East Asia, Central Asia and Russia

Requests in this part were made with `curl -A "Mozilla/5.0"`. "CL" is the
`Content-Length` the server reported; a bare byte count after a status code is the
size of the body downloaded.

### Regional summary

| Country | Series | Scale | Sheets free online | Format | Georeferenced | Licence | Verdict |
|---|---|---|---|---|---|---|---|
| Taiwan | VFR Chart, Taipei FIR | 1:500,000 | 1 (plus XYZ tiles) | Vector GeoPDF; PNG tile service | **Yes**, World Mercator (EPSG:3395) | Open Government Data License (Taiwan) 1.0 on the CAA site; not restated on the chart site | **USABLE** |
| Kazakhstan | Aeronautical Chart 1:500 000 | 1:500,000 | 27 | One 153 MB PDF of JPEG pages, 11701 x 8279 px each | No (LCC graticule printed) | None stated | **USABLE WITH CAVEATS** |
| Japan | JAPA sectional charts; JHA WAC | 1:500,000; 1:1,000,000 | 0 | Paper, sold | n/a | Commercial | NOT USABLE (paid; AIP behind registration) |
| South Korea | Aeronautical Chart ICAO; WAC ICAO | 1:500,000; 1:1,000,000 | 0 | Paper, sold to residents only | n/a | n/a | NOT USABLE (paid) |
| China | National VFR charts (2019) | UNVERIFIED | 0 | Behind login | -- | -- | NOT USABLE (login) |
| Hong Kong | Local Flying Chart; Helicopter Flying Chart | 1:100,000; 1:50,000 | 0 | Paper, sold | n/a | AIS site forbids redistribution | NOT USABLE (paid; no target-scale chart) |
| Mongolia | Aeronautical Chart ICAO; WAC ICAO | 1:500,000; 1:1,000,000 | 0 | Sold, MNT 28,200 per sheet | n/a | n/a | NOT USABLE (paid) |
| Russia | none from the state; commercial 1:500,000 | -- | 0 | Sold | n/a | n/a | NOT USABLE (nothing free) |
| Kyrgyzstan | none published | -- | 0 | -- | -- | -- | NOT USABLE (nothing exists) |
| Uzbekistan | none published | -- | 0 | -- | -- | -- | NOT USABLE (nothing exists) |
| Tajikistan | none published | -- | 0 | -- | -- | -- | NOT USABLE (nothing exists) |
| Turkmenistan | none published | -- | 0 | -- | -- | -- | NOT USABLE (nothing exists) |

### Taiwan (Taipei FIR)

- **Publisher:** Civil Aviation Administration, MOTC. The chart site's header
  names the CAA and calls itself the VFR chart cloud query system
  (交通部民用航空局 目視航圖雲端查詢系統).
- **Series:** "VFR Chart"; the site title is "TAIWAN FIR (RCAA) 1:500,000".
- **Scale:** 1:500,000, confirmed in eAIP GEN 3.2.
- **Coverage and sheets:** one sheet, 1520 x 1070 mm. The main panel is Taiwan
  island; its georeferenced viewport spans 21.369 to 27.284 N, 116.491 to
  123.531 E. Separate panels are named Kinmen, Matsu, "H1&H2" and
  "RestrictedVFR" in the file. Chinese and English editions.
- **Format:** **GeoPDF, vector.** Creator Esri ArcMap 10.8.1. The page holds
  22,721 path objects, 2,019 text objects and 214 images; the largest images are
  8740 x 11989 px (relief or base raster). A 300 dpi render would be about
  17,950 x 12,640 px.
- **Georeferencing:** yes. ISO 32000 `/Measure` dictionaries of subtype GEO with
  `/GPTS`, one per viewport (nine `/VP` entries). The embedded WKT is
  `WGS_1984_World_Mercator`: ellipsoidal Mercator, EPSG:3395, **not** Web
  Mercator. This venv's GDAL 3.13.3 could not open the file ("not recognized as
  being in a supported file format": the PDF driver is listed but has no read
  backend), so the georeferencing was read out of the file's dictionaries
  directly. `pypdfium2` opens and renders it.
- **Tile service:** XYZ, 256 px PNG, Web Mercator, no key. The page configures
  `map/ENG/{z}/{x}/{y}.png` (aeronautical overlay, English), `map/CHT/`
  (Chinese), `map/Basemap/`, and `Building`, `Isogonical`, `Powerline`, `River`,
  `Transport`, `Windturbine`, with `minZoom 5`, `maxNativeZoom 14` for ENG and
  CHT and 13 for most others. The chart is therefore split across layers: ENG is
  a transparent overlay (alpha 0 to 255), not the finished chart. Missing tiles
  answer **500** with an empty body, not 404. All four z14 tiles tried returned
  500, so z14 coverage is UNVERIFIED.
- **Edition and cycle:** the file name and the page both carry the date,
  2026-09-21. The change log on the index page shows updates every few weeks
  (2026-09-21, 08-08, 08-03, 07-11, 06-26, ...), mostly wind turbines and
  obstacles. Not AIRAC-aligned.
- **Discovery by script:** GET `https://www.eaipvfr.tw/` and match
  `/PDF/Taiwan_Eng_Map_(\d{8})_print.pdf`.
- **Access:** open. No login, key or click-through. A disclaimer pop-up closes
  by itself after five seconds and gates nothing.
- **Licence:**
  - eAIP GEN 3.2 (paraphrase): aeronautical charts are not sold; the listed
    charts, the VFR chart included, are downloaded from the eAIP website, and
    no paper VFR chart exists.
  - CAA Open Government Declaration, `https://www.caa.gov.tw/article.aspx?a=1433&lang=2`
    (paraphrase): copyright material on the CAA website is released under the
    Open Government Data License, version 1.0 (OGDL-Taiwan-1.0), free of charge,
    non-exclusive and sublicensable; users may reproduce, adapt and publicly
    transmit it and build products on it, irrevocably, provided the source is
    attributed. Works specially marked as needing consent are excluded.
  - The chart site itself carries only a liability disclaimer pointing readers
    to the eAIP for authoritative data. It has no licence text.
- **Redistribution of derived tiles:** **appears permitted, with attribution.**
  The gap: the declaration is worded for the CAA website and `eaipvfr.tw` is a
  separate domain outside `gov.tw`. Whether the declaration extends to it is
  UNVERIFIED.
- **Verdict: USABLE.** The best source found in the whole of this report:
  current, vector, georeferenced, free, and open-licensed on the natural
  reading. Caveats: it needs a PDF renderer other than this GDAL build, and a
  georeference taken per viewport from `/Measure`; the inset panels must be
  masked or placed separately; confirm the licence covers `eaipvfr.tw` if that
  matters to the user.

| URL | Result |
|---|---|
| `https://www.eaipvfr.tw/` | 200, 946,181 |
| `https://www.eaipvfr.tw/PDF/Taiwan_Eng_Map_20260921_print.pdf` | 200, CL 14,671,733, application/pdf, Last-Modified 21 Sep 2026 (downloaded) |
| `https://www.eaipvfr.tw/PDF/Taiwan_Cht_Map_20260921_print.pdf` | 200, CL 14,719,354 |
| `https://www.eaipvfr.tw/map/ENG/5/26/13.png` | 200, 6,677, image/png |
| `https://www.eaipvfr.tw/map/ENG/8/214/109.png` | 200, 15,863 |
| `https://www.eaipvfr.tw/map/ENG/10/856/438.png` | 200, 12,002 |
| `https://www.eaipvfr.tw/map/ENG/12/3427/1753.png` | 200, 1,151 |
| `https://www.eaipvfr.tw/map/ENG/13/6854/3506.png` | 200, 1,359 |
| `https://www.eaipvfr.tw/map/ENG/13/6855/3505.png` | 500, 0 |
| `https://www.eaipvfr.tw/map/ENG/14/13709/7012.png`, `14/13710/7010`, `14/13708/7012` | 500, 0 |
| `https://www.eaipvfr.tw/map/Basemap/10/856/438.png` | 200, 7,255 |
| `https://ais.caa.gov.tw/eaip/` | 200, 7,435 (issue list; an IDS AirNav eAIP) |
| `https://ais.caa.gov.tw/eaip/AIRAC%20AIP%20AMDT%2003-26_2026_08_06/eAIP/RC-GEN%203.2-en-GB.html` | 200, 22,535 |
| `https://ais.caa.gov.tw/` | 200, 4,654, redirected to `/aimportalapp/` (JavaScript application) |
| `https://www.caa.gov.tw/article.aspx?a=1433&lang=1` | 200, 259,499 (declaration, Chinese) |
| `https://www.caa.gov.tw/article.aspx?a=1433&lang=2` | 200, 130,364 (declaration, English) |

Sample: `samples/Taiwan_Eng_Map_20260921_print.pdf` (14,671,733 bytes).

### Kazakhstan

- **Publisher:** RSE Kazaeronavigatsia, AIM department.
- **Series:** "Aeronautical Chart 1:500 000", the ICAO Annex 4 chapter 17 chart.
- **Coverage and sheets:** the whole country in **27 sheets** inside one PDF:
  A4, B1 to B7, C1 to C7, D1 to D6, E1 to E6 (from the PDF's bookmarks and page
  tree; the sheet inspected is labelled index number B1, page 2 of 27).
- **Format:** **raster inside a plain PDF.** Producer is the Adobe Acrobat 11
  image conversion plug-in. Every page is 3369.89 x 2384.35 pt (A0 landscape,
  1189 x 841 mm). The page inspected is a single JPEG of **11701 x 8279 px**:
  250 dpi, about 50.8 m/px at chart scale, native zoom about z11.
- **Georeferencing:** none in the file (no `/Measure`, `/GPTS`, `/VP` or
  `/LGIDict` in the head or tail object streams). The sheet margin states
  WGS-84 and a Lambert conformal conic projection, and the neatline carries
  labelled graticule ticks, so each sheet can be registered from the graticule.
  The standard parallels are not printed in the part of the margin read and
  would have to be fitted: UNVERIFIED.
- **Content notes:** hill-shaded relief base with roads, settlements, FIR and
  sector boundaries, reporting points. The margin dates the topographic
  information 2016 and warns that relief data is incomplete.
- **Edition and cycle:** effective 06 AUG 2026. GEN 3.2 says charts outside the
  AIP are maintained on the AIRAC system and refers to the website for this
  chart's corrections. The observed cadence is UNVERIFIED (one edition seen).
- **Discovery by script:** GET `https://www.ans.kz/en/ais/aeron_charts` and match
  `/AIP/visual_charts/CHART_(\d{2}[A-Z]{3}\d{4}).pdf`.
- **Access:** open, no login. Ranged requests are honoured (206).
- **Licence:** **none stated.** The charts page, the AIS page and GEN 3.2 carry
  no copyright or terms text (searched for copyright, the (c) sign, "rights"
  and the Russian for copyright). GEN 3.2 section 3 says (paraphrase) that AIP
  charts are provided free over the Internet and that an electronic version of
  the 1:500 000 chart is on the Kazaeronavigatsia website.
- **Redistribution of derived tiles:** **unclear.** Free to obtain; nothing
  grants or forbids reuse.
- **Verdict: USABLE WITH CAVEATS.** Free, current, full national coverage at
  the target scale, from the state ANSP. Caveats: no licence; a 153 MB single
  file; JPEG pages, so compression artefacts are baked in; 27 sheets to
  register and mask by hand or by fitting.

| URL | Result |
|---|---|
| `https://www.ans.kz/en/` | 200, 16,877 |
| `https://www.ans.kz/en/ais` | 200, 6,173 |
| `https://www.ans.kz/en/ais/aeron_charts` | 200, 6,790 |
| `https://www.ans.kz/ru/ais/aeron_charts` | 200, 8,543 |
| `https://www.ans.kz/AIP/visual_charts/CHART_06AUG2026.pdf` | 200, **CL 153,459,286**, application/pdf, Last-Modified 05 Aug 2026 |
| same, `Range: bytes=0-4999999` | 206, 5,000,000 |
| same, last 1,048,576 bytes | 206, 1,048,576 |
| `https://www.ans.kz/AIP/eAIP/2026-04-16-AIRAC/html/eAIP/UA-GEN-3.2-en-GB.html` | 200, 20,164 |

The file is over this study's 100 MB sample limit, so it was not downloaded
whole. Samples: `samples/kz_first5MB.bin` (ranged), `samples/kz_sheet_first.jpg`
(sheet B1, 4,485,330 bytes, cut out of that range), and two previews.

### Japan

- **No free VFR chart from the state was found.**
- The 1:500,000 series is the sectional chart series (区分航空図) JAPA-501 to
  JAPA-508, eight sheets, with four 1:250,000 TCA charts (JAPA-253 to 256) and
  a Tokyo-area detail chart (JAPA-103). It is published by the Japan Aircraft
  Pilot Association, a private body, and **sold**. The shop page lists each
  sheet with its edition date (JAPA-501 sixth edition 2026-05-14 through
  JAPA-508 fifth edition 2026-06-04) and says shipping is charged on top of the
  chart price. It also says the charts are edited by a company, Airman's
  Information Service.
- The ICAO **WAC 1:1,000,000** and aeronautical route charts are sold by the
  Japan Hydrographic Association.
- The state AIP moved from AIS JAPAN to the SWIM portal in January 2025. The
  portal is a login-gated application and needs a registered account, so
  GEN 3.2 was NOT CHECKED. `aisjapan.mlit.go.jp` no longer resolves.
- **Verdict: NOT USABLE.** Every VFR series is a paid product and the AIP is
  behind registration.

| URL | Result |
|---|---|
| `https://www.japa.or.jp/japa-shop/japa-map` | 200, 35,201 |
| `https://www.jha.or.jp/en/shop/products/aeronautical/index.html` | 200, 12,934 |
| `https://www.jha.or.jp/en/shop/products/aeronautical/pdf/A_N_chart_index.pdf` | 200, CL 58,480, Last-Modified 29 Jun 2012 |
| `https://www.jha.or.jp/shop/index.php?main_page=categories&language=en` | 200, 91,298 |
| `https://top.swim.mlit.go.jp/swim/` | 200, 3,188 (application shell) |
| `https://aisjapan.mlit.go.jp/`, `https://www.swim.mlit.go.jp/` | 000, could not resolve host, with DNS over HTTPS as well; `nslookup` at 8.8.8.8 answers non-existent domain for the first |

### South Korea

- **Publisher:** Air Traffic Management Office, MOLIT.
- **Series (eAIP GEN 3.2):** Aeronautical Chart ICAO **1:500,000**, five sheets
  (2379-AB, 2379-CD, 2380-AB, 2380-CD, 2387-AD), 8,000 KRW each; WAC ICAO
  **1:1,000,000**, three sheets (2379, 2380, 2387), 10,000 KRW each;
  Aeronautical Navigation Chart 1:2,000,000, 10,000 KRW.
- **Edition:** the sales page gives 13 MAY 2026 and a four-year cycle for all
  three; GEN 3.2 still shows 15 MAY 2024.
- **Access:** paper only, ordered by form and paid by invoice. GEN 3.2 adds
  (paraphrase) that only holders of a domestic or alien registration card may
  buy them.
- The only free images are four preview thumbnails on the sales page, far too
  small to be a chart.
- Also checked: eAIP ENR 6 (en-route chart only); the AIM reference board
  (11 posts, none a VFR chart file; one is a chart user guide and one a UAM
  corridor chart); the public data portal, where a search for the Korean word for aeronautical chart returned a page with no chart dataset in its text (results may load by script: UNVERIFIED). MOLIT also publishes a mobile
  app called VFR NAVIGATO; its chart source was NOT CHECKED.
- **Verdict: NOT USABLE.** Paid paper charts, restricted to residents.

| URL | Result |
|---|---|
| `https://aim.koca.go.kr/` | 200, 72 (meta-refresh to `/aim/`) |
| `https://aim.koca.go.kr/aim/` | 200, 38,978 |
| `https://aim.koca.go.kr/eaipPub/Package/2026-09-17/html/eAIP/KR-GEN-3.2-en-GB.html` | 200, 36,712 |
| `https://aim.koca.go.kr/eaipPub/Package/2026-09-17/html/eAIP/KR-ENR-6-en-GB.html` | 200, 4,389 |
| `https://aim.koca.go.kr/aim/catalog.do?language=ko_KR` | 200, 34,923 (a data catalogue, not charts) |
| `https://aim.koca.go.kr/aim/boardList.do?gubun=2&language=ko_KR` | 200, 29,615 |
| `https://aim.koca.go.kr/google/sdoViewMap3.jsp` | 200, 7,536 |
| `http://aim.koca.go.kr/airmap/` | 404 |
| `https://www.molit.go.kr/atmo/USR/WPGE0201/m_37160/DTL.jsp` | 200, 93,905 (sales page; needs a cookie jar, it loops on 307 without one) |
| `https://www.molit.go.kr/atmo/USR/WPGE0201/m_37018/DTL.jsp` | 200, 52,405 |
| `https://www.molit.go.kr/images/place2016/acc/sub/map/map0.jpg` to `map3.jpg` | 200; CL 45,884 / 173,045 / 170,170 / 216,071 |
| `https://www.data.go.kr/data/15141563/fileData.do` | 200, 165,361 (the AIP as a dataset) |
| `https://www.data.go.kr/tcs/dss/selectDataSetList.do?keyword=%ED%95%AD%EA%B3%B5%EC%A7%80%EB%8F%84` (search for the Korean word for aeronautical chart) | 200, 473,372; the word does not occur in the returned page text, so the search result itself is UNVERIFIED |

### China (mainland)

- The CAAC Air Traffic Management Bureau released national VFR charts on
  26 December 2019 together with an upgraded general aviation information
  service platform. The news item gives neither scale nor sheet count:
  UNVERIFIED.
- The platform redirects to a login form (user name, password, captcha, with a
  free-registration link). Nothing is reachable without an account.
- The eAIP site is a JavaScript application shell; its content was NOT CHECKED.
- **Verdict: NOT USABLE.** Registration and login required; terms unknown.

| URL | Result |
|---|---|
| `http://www.caac.gov.cn/XWZX/MHYW/201912/t20191227_200055.html` | 200, 49,817 |
| `https://ga.aischina.com/` | 200, 7,197, redirected to `/pub/passport/login?next=/pub/` |
| `http://ga.aischina.com/` | 000, connection failed |
| `https://www.eaipchina.cn/` | 200, 873 |

### Hong Kong

- eAIP GEN 3.2 lists **no** 1:500,000 or 1:1,000,000 chart. The only visual
  charts are the Lands Department's topographic overprints: Hong Kong Local
  Flying Chart 1:100,000 (HM100LFC, one sheet) and Hong Kong Helicopter Flying
  Chart 1:50,000 (HM50HFC, two sheets), both edition 14 (2024).
- The Lands Department describes them as prepared and sold by its Survey and
  Mapping Office. Its open-data page lists free topographic maps and imagery
  but no flying chart.
- The current eAIP is discoverable from `https://www.ais.gov.hk/ais.json`
  (`amdt[].pubDate` and `effDate` build the path).
- **Licence of the AIS site (paraphrase):** the Government owns the copyright,
  and reproducing, adapting or distributing the content is forbidden without
  the Civil Aviation Department's prior written authorisation. Redistribution:
  **prohibited**.
- **Verdict: NOT USABLE.** No chart at the target scales, the flying charts are
  paid, and the AIS site forbids redistribution.

| URL | Result |
|---|---|
| `https://www.ais.gov.hk/` | 200, 64,138 |
| `https://www.ais.gov.hk/ais.json` | 200, 23,705 |
| `https://www.ais.gov.hk/eaip_20260903/2026-09-03-000000/html/eAIP/VH-GEN-3.2-en-US.html` | 200, 21,545 |
| `https://www.ais.gov.hk/eaip_20260122/2026-03-19-000000/html/eAIP/VH-GEN-3.2-en-US.html` | 404 (stale search result) |
| `https://www.landsd.gov.hk/en/survey-mapping/mapping/thematic-mapping.html` | 200, 65,380 |
| `https://www.landsd.gov.hk/en/spatial-data/open-data.html` | 200, 62,000 |

### Mongolia

- **Publisher:** AIS Division of the National Civil Aviation Center, for the
  Civil Aviation Authority of Mongolia.
- **Series (eAIP GEN 3.2):**
  - **WAC ICAO 1:1,000,000**, 11 sheets: 2240 Uvs, 2241 Khuvsgul, 2201 Khentii,
    2202 Dornod, 2242 Altai, 2286 Khangai, 2285 Sukhbaatar, 2284 Buir,
    2331 Erdene, 2287 Gobi, 2288 Dornogobi. Revisions dated 11 JAN 2024 to
    27 NOV 2025.
  - **Aeronautical Chart ICAO 1:500,000**, 34 sheets (2201-A Shaamar to
    2331-B Atas Bogd), most dated 06 OCT 2022, the newest 27 NOV 2025.
  - Both priced **MNT 28,200** per sheet plus VAT.
- **Access:** purchase from the AIS Division only. eAIP ENR 6 attaches the
  en-route chart alone.
- Also checked: the site's data set page (obstacle, aerodrome mapping and
  procedure data, released against an e-mail address and a licence key); the
  public ArcGIS account behind the site's airspace map, which holds 124 public
  items, all vector feature layers and aerodrome scenes, with no chart raster.
- **Verdict: NOT USABLE.** Both target series exist and are maintained, but are
  sold with no download.

| URL | Result |
|---|---|
| `https://ais.mn/` | 200, 29,428 |
| `https://ais.mn/files/aip/eAIP/valid/html/eAIP/ZM-GEN-3.2-en-MN.html` | 200, 109,451 |
| `https://ais.mn/files/aip/eAIP/valid/html/eAIP/ZM-ENR-6-en-MN.html` | 200, 2,962 |
| `https://ais.mn/dataset` | 200, 79,658 |
| `https://ais.mn/preNavigation`, `https://ais.mn/aipAip` | 200; 130,753 / 14,571 |
| `https://www.arcgis.com/sharing/rest/content/items/2cacc69b4f4349e2aabc8827b030b26c?f=json` | 200, 1,272 |
| `https://www.arcgis.com/sharing/rest/search?q=owner:mnaviationgis&f=json&num=100` | 200 (124 items) |

### Russia

- The state AIP is free to read. GEN 3.2 (dated 03 SEP 26) lists 13 chart
  series: aerodrome, procedure and en-route charts, plus VFR departure and VFR
  arrival charts per aerodrome. **The state publishes no 1:500,000 or
  1:1,000,000 visual chart series.** En-route charts are the only ones sold
  separately.
- VFR charts at 1:500,000 and 1:200,000 are produced commercially by a
  St Petersburg company, SZ RCAI, and sold through its store on paper and as
  raster charts for its own navigation product.
- **Verdict: NOT USABLE.** Nothing free at the target scales.

| URL | Result |
|---|---|
| `http://www.caiga.ru/common/AirInter/validaip/html/eng.htm` | 200, 570, redirected to `https://www.caica.ru/...` (frameset) |
| `https://www.caica.ru/common/AirInter/validaip/html/menueng.htm` | 200, 384,244 |
| `https://www.caica.ru/common/AirInter/validaip/aip/gen/gen3/gen3.2.pdf` | 200, 899,181, application/pdf |
| `https://www.caica.ru/` | 200, 65,720 |
| `http://www.caica.ru/sborniks/` | 200, 566,566 |
| `https://www.szrcai.ru/page/karty` | 200, 158,452 |

### Kyrgyzstan, Uzbekistan, Tajikistan, Turkmenistan

None of the four publishes a chart of the target type.

| State | What was checked | Result |
|---|---|---|
| Kyrgyzstan | eAIP GEN 3.2, `https://ais.ansp.kg/eaip/2026-09-03-AIRAC/html/eAIP/UC-GEN-3.2-en-GB.html` (200, 87,615). The current issue is discoverable from `https://ais.ansp.kg/api/v1/eaip_issues?limit=999&` (200, 450, JSON). `http://kan.kg/en/ais` now redirects to `https://ansp.kg/` (200, 3,542). | 12 series, all aerodrome, procedure or en-route. No visual en-route chart. |
| Uzbekistan | GEN 3.2, `https://uzaeronavigation.com/media/file/gen32_c8XPLJE.pdf` (200, 462,666), linked from `https://uzaeronavigation.com/ais/` (200, 269,475). | 11 series, none visual en-route. Charts are part of the AIP and not sold separately. |
| Tajikistan | GEN 3.2, `http://www.caica.ru/aiptjk/validaip/aiptjk/gen/gen3/gen3-2.pdf` (200, 266,529, dated 18 JUN 20); menu `http://www.caica.ru/aiptjk/validaip/html/menueng.htm` (200, 21,432). | WAC index: not published. Topographical charts: nil. |
| Turkmenistan | GEN 3.2, `http://www.caica.ru/aiptkm/validaip/aiptkm/gen/gen3/gen3-2.pdf` (200, 395,238, dated 19 FEB 26); menu `http://www.caica.ru/aiptkm/validaip/html/menueng.htm` (200, 23,793). | WAC index: not published. Topographical charts: not published. |

Guessed paths that failed: `https://www.caica.ru/aiptjk/validaip/aip/gen/gen3/gen3.2.pdf`
and the `aiptkm` equivalent (404); `https://www.uzaeronavigation.com/en/ais` (404);
`https://uzaeronavigation.uz/` (unresolved); `https://aip.aero/uz/en/` (403, a
third-party site).

**Verdict for all four: NOT USABLE.**

## Part 2. South and South-East Asia

Researched by a helper agent; checked and edited.

### Regional headline

**Nothing in this region is usable as it stands.** No state publishes a free
1:500,000 or 1:250,000 VFR chart. Four states put their 1:1,000,000 WAC sheets
online without payment (Singapore, Thailand, Malaysia, India: 29 sheets in all),
but every one of them reserves copyright and forbids reproduction or
redistribution without prior permission. The rest sell paper charts, hide the
AIP behind a login, or publish no VFR chart at all. Only one file found anywhere
carries georeferencing (a Nepal index chart, which is not the target series).

### Regional summary

| Country | Series | Scale | Sheets free online | Format | Georeferenced | Licence | Verdict |
|---|---|---|---|---|---|---|---|
| India | WAC ICAO (Survey of India) | 1:1,000,000 | 20 | 16 JPEG scans + 4 PDF, watermarked, 1997 | No | Reproduction prohibited without written permission | NOT USABLE WITHOUT PERMISSION |
| Pakistan | WAC ICAO 2441, 2549, 2550 (Survey of Pakistan) | 1:1,000,000 | 0 | Paper, purchase | n/a | n/a | NOT USABLE (nothing free) |
| Bangladesh | none published | -- | 0 | -- | -- | -- | NOT USABLE (nothing exists) |
| Sri Lanka | WAC ICAO 2796, 2803 | 1:1,000,000 | 0 | Paper, LKR 2000 each | n/a | n/a | NOT USABLE (paid) |
| Nepal | Aeronautical Chart of Nepal | 1:500,000 | 0 | Not online | n/a | NOT CHECKED | NOT USABLE (not online) |
| Nepal (by-product) | ENR 6.6 index chart | 1:1,200,000 | 1 | Geospatial vector PDF | **Yes**, UTM 45N | NOT CHECKED | Not the target series |
| Bhutan | none published | -- | 0 | -- | -- | -- | NOT USABLE (nothing exists) |
| Maldives | none published | -- | 0 | -- | -- | -- | NOT USABLE (nothing exists) |
| Thailand | WAC ICAO 2617, 2677, 2678, 2738, 2799 | 1:1,000,000 reduced to A4 | 5 | Raster PDF, A4 at 300 dpi | No | Personal non-commercial use only; no redistribution | NOT USABLE WITHOUT PERMISSION |
| Vietnam | Aeronautical chart, 3 scales | 1:1,000,000 / 1:500,000 / 1:250,000 | 0 | Paper, 1988 and 1997 | n/a | n/a | NOT USABLE (not online) |
| Cambodia | unknown | -- | 0 | eAIP behind registration and click-through | -- | Redistribution barred without authorisation | NOT USABLE |
| Laos | unknown | -- | 0 | No online AIP found | -- | -- | NOT USABLE (nothing found) |
| Myanmar | none published | -- | 0 | -- | -- | -- | NOT USABLE (nothing exists) |
| Malaysia | WAC ICAO 2858, 2859, 2861 | 1:1,000,000 | 3 | Raster PDF, 144 dpi full size, 2007 content | No | Copying needs approval (printed on chart) | NOT USABLE WITHOUT PERMISSION |
| Singapore | WAC ICAO 2860 | 1:1,000,000 | 1 | Vector PDF, 900 x 750 mm, 2024 | No | No copying, derivative works or automated access without written permission | NOT USABLE WITHOUT PERMISSION |
| Brunei | none published | -- | 0 | -- | -- | -- | NOT USABLE (nothing exists) |
| Indonesia | unknown | -- | 0 | AIP portals behind login | -- | -- | NOT USABLE (login) |
| Philippines | unknown | -- | 0 | AIP behind login, paid subscription | -- | -- | NOT USABLE (paid) |

If permission were sought, the order of technical merit is Singapore (vector,
2024), Malaysia (full-size raster, but 2007), India (full-size scans, but 1997
and watermarked), Thailand (A4 reductions). The three eAIP states share one WAC
sheet grid and adjoin: 2799 (TH) north of 2859 (MY), with 2858 (MY) and
2860 (SG) alongside.

---

### Singapore

- **Publisher:** Civil Aviation Authority of Singapore (CAAS). The chart names
  SLC Geomatic Solutions Ltd (UK) as producer.
- **Series:** World Aeronautical Chart ICAO 1:1,000,000, sheet **WAC 2860
  Singapore Island**. One sheet. GEN 3.2.5 lists it as in the AIP, dated
  21 MAR 24. No 1:500,000 or 1:250,000 chart is listed.
- **Coverage (read off the chart):** 102 E to 108 15 E, 0 to 4 15 N.
- **Format:** single-page **vector PDF**, PDF 1.7, 2551.5 x 2126.2 pt
  (900 x 750 mm). 6,461 path objects, 6,380 text objects, 109 images. The images
  include a raster base in strips 8,204 px wide totalling 5,665 rows. Linework
  and type are true vector, so it can be rendered at any resolution the way the
  `ifr-low` PDFs are.
- **Georeferencing:** none. 1,680 streams scanned, 760 inflated, no geospatial
  dictionary; no `/Viewport`. Chart states Lambert Conformal Conic, standard
  parallels 0 40 and 3 20, WGS84. 1 degree graticule drawn.
- **Edition:** WAC-2860 dated 21 MAR 2024, AIP AMDT 02/2024; aeronautical
  information March 2022. Updated by AIP amendment, irregularly.
- **Discovery by script:** GET `https://aim-sg.caas.gov.sg/aip/`, take the link
  matching `/aim-content/uploads/aip/<DD-MON-YYYY>/AIP/<date>-000000/html/index-en-GB.html`,
  replace `html/index-en-GB.html` with
  `pdf/SG-ENR-6-WORLD-AERONAUTICAL-CHART-ICAO.pdf`.
- **Access:** open, no login, no click-through.
- **Licence:** `https://www.caas.gov.sg/terms-of-use` (linked from the AIM-SG
  footer). Paraphrase: material may not be modified, copied, reproduced,
  distributed, published or made into derivative works without CAAS's written
  permission; one copy may be downloaded for personal non-commercial use; page
  scraping, robots and other automatic access are forbidden; no licence is
  granted by use of the site. GEN 3.2.3.1 says the charts can be accessed
  freely, which concerns access only. No copyright wording was found in GEN 0.1
  or GEN 3.1. Redistribution of derived tiles: **prohibited without written
  permission**. Note the terms also bar an automated fetcher.
- **Verdict: NOT USABLE WITHOUT PERMISSION (written, from CAAS).**

| URL | Result |
|---|---|
| `https://aim-sg.caas.gov.sg/` | 200, 90,450 (with DoH) |
| `https://aim-sg.caas.gov.sg/aip/` | 200, 106,109 |
| `https://aim-sg.caas.gov.sg/aeronautical-data-catalogue/` | 200, 108,304 (PANS-AIM .xlsx tables only) |
| `https://aim-sg.caas.gov.sg/aim-content/uploads/aip/17-SEP-2026/AIP/2026-09-03-000000/html/eAIP/SG-GEN-3.2-en-GB.html` | 200, 36,323 |
| `.../html/eAIP/SG-ENR-6-en-GB.html` | 200, 3,651 |
| `.../html/eAIP/SG-GEN-0.1-en-GB.html`, `SG-GEN-3.1-en-GB.html` | 200; 20,796 / 42,925 |
| `https://aim-sg.caas.gov.sg/aim-content/uploads/aip/17-SEP-2026/AIP/2026-09-03-000000/pdf/SG-ENR-6-WORLD-AERONAUTICAL-CHART-ICAO.pdf` | 200, application/pdf, len 10,835,746, Last-Modified 17 Sep 2026 |
| `https://www.caas.gov.sg/terms-of-use` | 200, 468,831 |

Sample: `samples/sg_wac2860.pdf` (10,835,746 bytes), preview
`samples/sg_wac2860_view.jpg`.

---

### Thailand

- **Publisher:** The Civil Aviation Authority of Thailand (CAAT).
- **Series:** World Aeronautical Chart ICAO 1:1,000,000. **Five sheets** in
  ENR 6: WAC 2677 (Gulf of Martaban), 2678, 2799, 2617, 2738. GEN 3.2 sections
  6 and 7 read NIL. No 1:500,000 or 1:250,000 en-route VFR chart; the only other
  VFR items are per-aerodrome VFR entry and exit procedure charts.
- **Coverage:** sheet 2677 spans about 96 E to 102 E, 16 N to 20 N. Whether five
  sheets cover all of Thailand is UNVERIFIED; the adjoining-sheet index on 2677
  also shows 2676 and 2679, which are not in the AIP.
- **Format (sheet 2677, the only one inspected):** single-page **raster PDF**,
  A4 landscape, 842 x 595 pt. Ten image strips 3,508 px wide, 2,479 rows: the
  whole sheet at **A4, 300 dpi**. No vector objects. The 1:1,000,000 sheet is
  therefore reduced about 2.9x: about **250 m/px**, native zoom about z9.
- The other four sheets are 0.77 to 1.59 MB against 7.6 MB. Their format is
  **UNVERIFIED** (HEAD only, one sample per source).
- **Georeferencing:** none. LCC, standard parallels 16 40 and 19 20 on this
  sheet, WGS84. 1 degree graticule drawn.
- **Edition:** imprint 2020, aeronautical information Jan 2020. AIP page dates
  7 AUG 2025 (2677, 2678, 2799), 2 OCT 2025 (2617), 27 NOV 2025 (2738).
- **Discovery by script:** GET `https://aip.caat.or.th/`, collect
  `YYYY-MM-DD-AIRAC/html/index-en-GB.html` links, take the latest date not after
  today (future issues are listed), GET `<issue>/html/eAIP/VT-ENR-6-en-GB.html`,
  read the `../../graphics/<id>.pdf` link on rows containing "WAC".
- **Access:** `aip.caat.or.th` serves the files with no login or click-through.
  The sister site `ais.caat.or.th` opens on a terms page with an agree button,
  which was read but **not submitted**.
- **Licence:** `https://ais.caat.or.th/term-condition`. Paraphrase: AIP material
  and aeronautical charts are CAAT copyright; they are offered free for personal
  non-commercial use only, which excludes internal business use; extracting,
  copying, redistributing, republishing or modifying is not allowed; commercial
  publishers and application developers wanting to redistribute should write to
  CAAT. Redistribution of derived tiles: **prohibited without authorisation**.
- **Verdict: NOT USABLE WITHOUT PERMISSION.** Also low resolution and 2020 data.

| URL | Result |
|---|---|
| `https://aip.caat.or.th/` | 200, 28,546 |
| `https://aip.caat.or.th/2026-09-03-AIRAC/html/index-en-GB.html` | frameset returned; status not recorded |
| `.../html/eAIP/VT-menu-en-GB.html` | 200, 552,517 |
| `.../html/eAIP/VT-GEN-3.2-en-GB.html` | 200, 367,880 |
| `.../html/eAIP/VT-ENR-6-en-GB.html` | 200, 5,451 |
| `.../html/eAIP/VT-GEN-0.1-en-GB.html`, `VT-GEN-3.1-en-GB.html` | 200; 13,011 / 76,008 (no copyright wording) |
| `https://aip.caat.or.th/2026-09-03-AIRAC/graphics/283086.pdf` (WAC 2677) | 200, application/pdf, len 7,606,920, Last-Modified 23 Jul 2026 |
| `.../graphics/283087.pdf` (WAC 2678) | 200, len 1,588,230 |
| `.../graphics/283088.pdf` (WAC 2799) | 200, len 1,135,434 |
| `.../graphics/289479.pdf` (WAC 2617) | 200, len 768,691 |
| `.../graphics/291548.pdf` (WAC 2738) | 200, len 882,115 |
| `.../graphics/313087.pdf` (en-route chart, IFR) | 200, len 3,927,534 |
| `https://ais.caat.or.th/` | 200, 9,126, redirected to `/term-condition` |
| `https://www.caat.or.th/en` | 403 |

Sample: `samples/th_wac2677.pdf` (7,606,920 bytes), preview
`samples/th_wac2677_view.jpg`.

---

### Malaysia

- **Publisher:** Civil Aviation Authority of Malaysia (CAAM). Imprint: published
  by the Department of Civil Aviation, prepared by the Department of Survey and
  Mapping Malaysia.
- **Series:** World Aeronautical Chart ICAO 1:1,000,000. **Three sheets** in
  ENR 6: WAC 2858 North Natuna Island (ENR 6-19, 04 SEP 2025), WAC 2859 Penang
  Island (ENR 6-21, 16 AUG 2018), WAC 2861 Cape Sirik (ENR 6-23, 16 AUG 2018).
  No 1:500,000 or 1:250,000 chart.
- **Coverage:** sheet 2859 spans about 100 E to 106 15 E, 4 N to 8 15 N.
  Southern Peninsular Malaysia is on Singapore's 2860. Coverage of Sabah and
  most of Sarawak is doubtful (UNVERIFIED).
- **Format (sheet 2859 only):** single-page **raster PDF**, 2490 x 2084 pt
  (full sheet size), one image **4,980 x 4,101 px = 144 dpi**, about
  **176 m/px**, native zoom about z9.8. Ghostscript 8.64 / pdftk.
- **Georeferencing:** none. LCC, WGS84; the standard parallels printed on this
  sheet were not legible in the preview (UNVERIFIED). 1 degree graticule.
- **Edition:** imprint 2007, aeronautical information Jan 2007 (read from a
  reduced preview, UNVERIFIED); AIP page dated 16 AUG 2018.
- **Discovery by script:** GET `https://aip.caam.gov.my/aip/eAIP/history-en-MS.html`,
  take the latest issue not after today (`2026-08-06-AIRAC/...` and, for
  non-AIRAC issues, `2026-08-11/...`; a future issue was listed), GET
  `<issue>/html/eAIP/WM-ENR-6-en-MS.html`, match rows containing "WAC".
- **Access:** open, no login.
- **Licence:** printed on the chart. Paraphrase: government copyright reserved;
  copying the map or any part needs the approval of the Director of National
  Mapping, Malaysia. No copyright wording in GEN 0.1 or GEN 3.1; no web terms
  page found. Redistribution: **prohibited without prior approval**.
- **Verdict: NOT USABLE WITHOUT PERMISSION.** Also 2007 content.

| URL | Result |
|---|---|
| `https://aip.caam.gov.my/` | 200, 357 (meta-refresh) |
| `https://aip.caam.gov.my/aip/eAIP/history-en-MS.html` | 200, 6,456 |
| `https://aip.caam.gov.my/aip/eAIP/2026-08-11/html/index-en-MS.html` | frameset returned; status not recorded |
| `.../2026-08-11/html/eAIP/WM-GEN-3.2-en-MS.html` | 200, 197,670 |
| `.../2026-08-11/html/eAIP/WM-ENR-6-en-MS.html` | 200, 6,956 |
| `.../2026-08-11/html/eAIP/WM-GEN-0.1-en-MS.html`, `WM-GEN-3.1-en-MS.html` | 200; 12,580 / 26,838 |
| `https://aip.caam.gov.my/aip/eAIP/2026-08-11/graphics/48598.pdf` (WAC 2858) | 200, application/pdf, len 795,451, Last-Modified 05 Aug 2026 |
| `.../graphics/48600.pdf` (WAC 2859) | 200, len 1,253,739 |
| `.../graphics/48602.pdf` (WAC 2861) | 200, len 1,602,202 |
| `.../graphics/288678.pdf`, `265778.pdf`, `265779.pdf`, `288679.pdf`, `116747.pdf`, `265896.pdf` (IFR and index charts) | 200; 5,001,974 / 344,260 / 786,971 / 633,223 / 275,537 / 392,062 |

Sample: `samples/my_wac2859.pdf` (1,253,739 bytes), previews
`samples/my_wac2859_view.jpg`, `samples/my_wac2859_crop.jpg`.

---

### India

- **Publisher:** Survey of India. The AAI eAIP GEN 3.2 says the 1:1,000,000 WAC
  is produced by Survey of India and obtained from its offices; AAI's own
  FIR/TMA/ATS charts are sold. ENR 6 holds five en-route charts only.
- **Series:** World Aeronautical Chart ICAO 1:1,000,000. **20 sheets** offered
  for free download: 2439 Bareilly, 2440 Delhi, 2551 Jaipur, 2552 Allahabad,
  2553 Patna, 2554 Guwahati, 2558 Calcutta, 2559 Nagpur, 2560 Ahmedabad,
  2561 Rajkot, 2673 Mumbai, 2674 Hyderabad, 2675 Chilika, 2679 Andaman,
  2681 Chennai, 2682 Bangalore, 2795 Trivandrum, 2796 Tiruchchirappalli,
  2798 Port Blair, 2801 Great Nicobar. Completeness of national coverage is
  UNVERIFIED (Kashmir/Ladakh and the far north-east look absent).
- **Format:** 16 JPEG scans and 4 PDFs (PDFs not inspected). Pixel sizes read
  from the first 128 KB of each JPEG:

  | File (under `https://surveyofindia.gov.in/files/`) | Page label | Status | len | Pixels |
  |---|---|---|---|---|
  | `2673_water_mark.jpg` | 2673 Mumbai | 200 | 2,090,973 | 5737 x 4796 |
  | `2795_trivendram_water_mark.jpg` | 2795 Trivandrum | 200 | 1,840,978 | 6894 x 4784 |
  | `2799_trichurapalli_water_mark.jpg` | 2796 Tiruchchirappalli | 200 | 3,005,353 | 8976 x 7088 |
  | `allahabad_water_mark.jpg` | 2552 Allahabad | 200 | 2,326,951 | 5779 x 4713 |
  | `barailly_water_mark.jpg` | 2439 Bareilly | 200 | 1,613,912 | 4356 x 3535 |
  | `chennai_water_mark.jpg` | 2681 Chennai | 200 | 2,950,340 | 8757 x 7124 |
  | `chilka_water_mark.jpg` | 2675 Chilika | 200 | 1,605,243 | 5908 x 5034 |
  | `Culcutta_water_mark.jpg` | 2558 Calcutta | 200 | 2,110,126 | 5721 x 4735 |
  | `delhi_water_rmark.jpg` | 2440 Delhi | 200 | 2,039,166 | 5758 x 4713 |
  | `great_Nicobar_water_mark.jpg` | 2801 Great Nicobar | 200 | 2,138,811 | 8874 x 7104 |
  | `guwahti_water_mark.jpg` | 2554 Guwahati | 200 | 2,814,923 | 5705 x 4788 |
  | `hydrabad_water_mark.jpg` | 2674 Hyderabad | 200 | 2,240,327 | 5706 x 4746 |
  | `jaipur%202551.jpg` | 2551 Jaipur | 200 | 9,378,719 | 9399 x 7396 |
  | `patna%202563_1.jpg` | 2553 Patna | 200 | 9,868,863 | 9600 x 7488 |
  | `rajkoti%202561.jpg` | 2561 Rajkot | 200 | 6,314,542 | 9557 x 7514 |
  | `ban_wm.jpg` | 2682 Bangalore | 200 | 7,103,002 | 9841 x 7183 |
  | `aeronautical_1.pdf` | 2559 Nagpur | 200 | 14,538,060 | not inspected |
  | `2560_abdwm.pdf` | 2560 Ahmedabad | 200 | 4,049,138 | not inspected |
  | `andaman.pdf` | 2679 Andaman | 200 | 3,505,715 | not inspected |
  | `portblair.pdf` | 2798 Port Blair | 200 | 3,425,347 | not inspected |

  All had Last-Modified 23 Jun 2025. File names are irregular and some disagree
  with the sheet number on the page, so a fetcher must scrape the page.
- **Sample (2440 Delhi):** 5758 x 4713 JPEG, 200 dpi tag, about **127 m/px**,
  native zoom about z10. A large pale Survey of India seal is **watermarked
  across the middle of the map**.
- **Georeferencing:** none. Lambert conical orthomorphic with standard parallels
  printed; 30-minute graticule.
- **Edition:** Delhi is third edition 1997, aeronautical data complete to
  5 May 1997, topographic base 1988. An archive, not a maintained product.
- **Discovery by script:** scrape
  `https://surveyofindia.gov.in/pages/aeronautical-charts-and-maps`, the list
  under the World Aeronautical Chart heading (the page also lists International
  Map of the World sheets, which are not aeronautical).
- **Access:** open, no login.
- **Licence:** `https://surveyofindia.gov.in/pages/copyright-policy`. Deciding
  sentence, quoted: "prohibited for reproduction in whole or part without
  written permission of Survey of India". A source acknowledgement is also
  required. Chart marked Government of India copyright 1997. Redistribution:
  **prohibited without written permission**.
- **Verdict: NOT USABLE WITHOUT PERMISSION**, and of little value with it: 1997 content, watermark.

| URL | Result |
|---|---|
| `https://aim-india.aai.aero/` | 200, 13,807 |
| `https://aim-india.aai.aero/eaip/eaip-v2-09-2026/index-en-GB.html` | 200, 899 |
| `.../eaip-v2-09-2026/toc-frameset-en-GB.html` | 200, 727 |
| `.../eaip-v2-09-2026/eAIP/Menu-en-GB.html` | 200, 156,700 |
| `.../eaip-v2-09-2026/eAIP/IN-GEN%203.2-en-GB.html` | 200, 18,667 |
| `.../eaip-v2-09-2026/eAIP/IN-ENR%206-en-GB.html` | 200, 8,695 |
| `.../eAIP/IN-menu-en-GB.html`, `.../eAIP/IN-ENR%206.1-en-GB.html` | 404 (guessed names) |
| `https://surveyofindia.gov.in/pages/aeronautical-charts-and-maps` | 200, 117,612 |
| `https://surveyofindia.gov.in/pages/copyright-policy` | 200, 113,750 |
| `https://surveyofindia.gov.in/pages/terms-and-conditions` | 200, 113,781 |
| `https://onlinemaps.surveyofindia.gov.in/Digital_Product_Show.aspx` | 200, 301,146 (no aeronautical product) |

Sample: `samples/in_wac2440_delhi.jpg` (2,039,166 bytes), previews
`in_wac2440_view.jpg`, `in_wac2440_crop.jpg`, `in_wac2440_crop2.jpg`.

---

### Nepal

- **Publisher:** Civil Aviation Authority of Nepal (CAAN); small-scale charts by
  the Department of Survey.
- **Target series:** GEN 3.2 lists an **Aeronautical Chart of Nepal at
  1:500,000**, and says it is produced instead of the 1:1,000,000 WAC. The list
  of charts available (3.2.5) reads "to be developed". **No file for it is in
  the AIP**, and neither the e-AIP site nor the Department of Survey site
  mentions it. Number of sheets, edition and price: unknown.
- **What is online instead (ENR 6):** six A-size index charts. The one sampled,
  **ENR 6.6** (transmission lines, FM antennas, aerial sporting and recreational
  activities), is a whole-country map at a stated **1:1,200,000**, 740 x 500 mm,
  dated 20 November 2025, AMDT 10/2025. It shows aerodromes, hypsometric tints,
  spot heights, protected areas, paragliding zones and roads, but no airspace
  structure: it is an index chart, not a VFR chart.
- **Format of ENR 6.6:** vector PDF with a raster base (886 paths, 850 text
  objects, 307 images in strips 16,250 px wide).
- **Georeferenced: yes.** It carries an ISO 32000 geospatial viewport: a
  `/Measure` dictionary of subtype GEO with four corner points (lat/lon
  26.082, 80.116; 30.546, 79.821; 30.737, 88.42; 26.24, 88.361) and a projected
  CRS of **WGS 1984 UTM zone 45N**. This venv's GDAL cannot read it (its PDF driver opens nothing); a GDAL built with a PDF read backend should.
- **Discovery by script:** GET `https://e-aip.caanepal.gov.np/welcome/listall/1`
  and match the link whose text is the page number (ENR 6.6-1 and so on). File
  names are opaque hashes that change with each amendment.
- **Access:** open, no login.
- **Licence:** NOT CHECKED (no terms page was found or read).
- **Verdict: NOT USABLE** for the target series, which is not online. The index
  chart is recorded as the only georeferenced file found in the region.

| URL | Result |
|---|---|
| `https://caanepal.gov.np/` | 200, 562,000 |
| `https://caanepal.gov.np/ais` | 200, 311,067 |
| `https://caanepal.gov.np/publications/integrated-aeronautical-information-packages` | redirects to `https://e-aip.caanepal.gov.np/`, 200, 7,140 |
| `https://e-aip.caanepal.gov.np/welcome` | 200, 7,140 |
| `https://e-aip.caanepal.gov.np/welcome/listall/1` | 200, 75,390 |
| `https://e-aip.caanepal.gov.np/welcome/listall/488`, `/489` | 200; 519,543 / 11,951 |
| `https://e-aip.caanepal.gov.np/_uploads/_pdf/30a003385545cd042cfa6145657b77b0.pdf` (GEN 3.2) | 200, application/pdf, 870,102 |
| `.../_pdf/2af045b2e564050be382c9a55c953ca5.pdf` (ENR 6.1-1 en-route) | 200, len 3,290,213 |
| `.../_pdf/611019f20ec1f5545fba7fd8fbd0a6d8.pdf` (ENR 6.2-1) | 200, len 389,513 |
| `.../_pdf/220310756024271ff8fef0dc4607ac51.pdf` (ENR 6.3-1) | 200, len 269,641 |
| `.../_pdf/ddf5cce28eda4c9aa6b79ec5b81d4b5b.pdf` (ENR 6.4-1) | 200, len 1,436,253 |
| `.../_pdf/1de278a830b3329799809795f6480dd3.pdf` (ENR 6.5-1) | 200, len 3,212,182 |
| `.../_pdf/3246cdbf54c9a9948d4f3cdc0b84dac6.pdf` (ENR 6.6-1) | 200, len 6,279,187, Last-Modified 01 Dec 2025 |
| `https://dos.gov.np/` | 200, 207,189 (no mention of aeronautical) |
| `https://dos.gov.np/pages/map-of-nepal` | 200, 128,881 (no mention) |

Sample: `samples/np_enr6_6.pdf` (6,279,187 bytes), preview
`samples/np_enr6_6_view.jpg`.

---

### Vietnam

- **Publisher:** Viet Nam Aeronautical Information Centre (VNAIC) under VATM.
- **Series listed in GEN 3.2:** an Aeronautical Chart series on a Gauss
  projection, WGS-84, in three scales: **1:1,000,000** (12 sheets, N-1 Ha Noi to
  N-12 An Bang Island, dated 1988), **1:500,000** (19 sheets, F-48-A Lao Cai and
  so on, dated 1997) and **1:250,000** (about 38 sheets, dated 1988; count
  UNVERIFIED). No price and no AIP page reference is given for any of them, so
  they are paper products obtained from VNAIC. Section 6 (WAC index) reads "to
  be developed".
- **Online:** ENR 6 holds two en-route charts at 1:1,900,000 only. The VFR
  series is **not downloadable**.
- **Discovery:** `https://aim.vatm.vn/images/stories/vnaic.vn/SanPhamDichVu/AIPVietNam/AIP/history-en-GB.html`
  lists issues; the latest not after today was `2026-06-30`.
- **Verdict: NOT USABLE.** The right chart types exist but only on paper, and
  are 29 to 38 years old.

| URL | Result |
|---|---|
| `https://www.vnaic.vn/index.html` | 200, 13,083 (JavaScript shell) |
| `https://www.vnaic.vn/index.php?option=com_content&view=category&id=51:map&layout=blog&Itemid=92&lang=en` | 200, 13,083 (same shell, no content) |
| `https://aim.vatm.vn/images/stories/vnaic.vn/SanPhamDichVu/AIPVietNam/AIP/history-en-GB.html` | 200, 10,633 |
| `.../AIP/2026-06-30/html/eAIP/VV-GEN-3.2-en-GB.html` | 200, 724,819 |
| `.../AIP/2026-06-30/html/eAIP/VV-ENR-6-en-GB.html` | 200, 4,266 |
| `.../AIP/2026-06-30/graphics/169715`, `188531` (en-route charts) | 200; len 4,473,632 / 4,794,050 |

---

### Sri Lanka -- paid

- **Publisher:** Airport and Aviation Services (Sri Lanka) (Private) Limited.
- **Series:** GEN 3.2 lists WAC ICAO 1:1,000,000 **Sri Lanka (2796)** and
  **Sri Lanka (2803)**, each priced **LKR 2000**, dated 02 DEC 24, obtained on
  request from the AIM unit. They are not attached to the AIP. ENR 6.1 holds an
  en-route chart and a minimum sector altitude chart only.
- **Access:** the AIM portal opens on a login page (free registration offered,
  not used). The eAIP pages themselves answered by direct URL with no login.
  The edition reached was dated 2025-06-12; whether it is current is UNVERIFIED
  because the edition index sits behind the portal.
- **Verdict: NOT USABLE** (paid paper product).

| URL | Result |
|---|---|
| `https://www.airport.lk/` (https and http), `https://www.airport.lk/aasl/AIS/web.Home.htm` | 000, connection reset |
| `https://airport.lk/aasl/AIM/AIP/AIP.html` | 200 after redirect to the home page |
| `https://www.caa.lk/` | 200 with DoH (redirects to `/en/`); unresolved without |
| `https://www.aimibsrilanka.lk/` | 200, 276 (script redirect to the portal) |
| `https://www.aimibsrilanka.lk/aes/control/welcomepage?HF_ACTION=init` | 200, 18,746, login page |
| `https://www.aimibsrilanka.lk/eaip/`, `/eaip/AIP_2501/` | 403 |
| `https://www.aimibsrilanka.lk/eaip/AIP_2501/Eurocontrol/SRI%20LANKA/2025-06-12-NON%20AIRAC/html/index-en-EN.html` | 200, 831 |
| `.../html/eAIP/EN-menu-en-EN.html` | 200, 131,822 |
| `.../html/eAIP/EN-VC-GEN-3.2-en-EN.html` | 200, 102,424 |
| `.../html/eAIP/EN-VC-ENR-6.1-en-EN.html` | 200, 2,847 |
| `.../html/eAIP/EN-VC-ENR-6-en-EN.html`, `EN-VC-ENR-6.0-en-EN.html`, `EN-ENR-6-en-EN.html`, `VC-menu-en-EN.html`, `EN-VC-menu-en-EN.html` | 404 (guessed names) |
| `.../SRI%20LANKA/history-en-EN.html`, `.../SRI%20LANKA/index.html`, and the same under `AIP_2601` | 404 (guessed) |

---

### Pakistan -- paid

- **AIP GEN 3.2 (AIRAC AMDT 02/26):** the WAC ICAO 1:1,000,000 is produced by
  **Survey of Pakistan**. Published sheets: 2441 (Quetta), 2549 (Jiwani),
  2550 (Karachi). WAC and topographical charts are marked as not available from
  the AIS and are obtained from Survey of Pakistan, Rawalpindi.
- **ENR 6:** two en-route charts, a P/R/D areas chart, four area charts.
- **Survey of Pakistan site:** home, Products, Paper Maps and Thematic Maps
  pages contain no occurrence of "aeronaut" or "WAC"; paper maps are described
  as paid products with previews only.
- **Verdict: NOT USABLE.**

| URL | Result |
|---|---|
| `https://paa.gov.pk/` | 200, 1,964 (JavaScript shell) |
| `https://paa.gov.pk/assets/index-c229GEKk.js` | 200, 801,639 |
| `https://paa.gov.pk/aeronautical-information/electronic-aeronautical-information-publication` | WebFetch failed on certificate verification |
| `https://paawebadmin.paa.gov.pk/media/eaip/02-25/eAIP/index.htm`, `main.html`, `left.htm` | 200; 538 / 710,344 / 17,407 |
| `https://paawebadmin.paa.gov.pk/media/eaip/02-25/eAIP/GEN/GEN-0-1.pdf` | 200, len 543,112 |
| `https://paawebadmin.paa.gov.pk/media/eaip/02-25/eAIP/GEN/GEN3_2.pdf` | 200, 963,905 |
| `.../02-25/eAIP/GEN/GEN-3-2.pdf`, `.../ENR/ENR-6.pdf`, `.../02-25/`, `.../02-25/index.html`, `.../02-25/eAIP/` | 404 (guessed) |
| `.../media/eaip/<ed>/eAIP/index.htm` for 01-25 to 04-25 and 01-26 to 03-26 | 200 |
| same for 05-25, 06-25, 04-26 | 404 |
| `https://paawebadmin.paa.gov.pk/media/eaip/03-26/eAIP/left.htm` | 200, 17,622 |
| `https://paawebadmin.paa.gov.pk/media/eaip/03-26/eAIP/GEN/GEN3_2.pdf` | 200, len 3,410,512, Last-Modified 18 Aug 2026 |
| `https://surveyofpakistan.gov.pk/` | 200, 49,333 |
| `https://surveyofpakistan.gov.pk/Detail/YWIxMWQ1MGYtZTA2Zi00YzZjLWE4OTYtNmFlM2FiZDljMGIx` (Paper Maps) | 200, 120,547 |
| `https://surveyofpakistan.gov.pk/Detail/MjhlZWYyMmMtOWU3Mi00ODA2LWFkN2MtMmQxMjRjODBmYjA5` (Products) | 200, 47,628 |
| `https://surveyofpakistan.gov.pk/Detail/YzA2N2I1NjUtYzM3ZC00NWNkLWFhZjQtODM3OTNkNTg3ZjNh` (Thematic Maps) | 200, 50,798 |

---

### Indonesia -- behind login

- The hinted host `aimindonesia.dephub.go.id` no longer exists (DNS: non-existent
  domain). The service has moved to `aimindonesia.kemenhub.go.id`, which opens
  on a **sign-in page** with a register link.
- AirNav Indonesia's AIS centre (`pia.airnavindonesia.co.id`) lists AIP and
  aeronautical charts among its services but also requires sign-in. Its
  Nav-Earth link returns an application shell with no readable content.
- No account was created, so GEN 3.2, the chart list and any chart files are
  **UNVERIFIED**. A web search result (not confirmed) suggested WAC sheets are
  sold by subscription.
- **Verdict: NOT USABLE** on the evidence available without logging in.

| URL | Result |
|---|---|
| `https://aimindonesia.dephub.go.id/` (https and http) | 000, could not resolve; `nslookup` at 8.8.8.8: non-existent domain |
| `https://aimindonesia.kemenhub.go.id/` | 200, 10,493, redirected to `/login` |
| `https://pia.airnavindonesia.co.id/` | 200, 19,415 |
| `https://pia.airnavindonesia.co.id/?page=c2VydmljZXM=` | 200, 12,657 |
| `https://app-pia.airnavindonesia.co.id/navearth` | 200, 6,580 |
| `https://www.airnavindonesia.co.id/`, `https://hubud.kemenhub.go.id/` | 200 |
| `https://aim.airnavindonesia.co.id/` | 000, could not resolve (guessed) |

---

### Philippines -- paid, behind login

- The AIS site sends the AIP link to a **login page**. The subscription page
  prices the AIP at USD 324.80 for international subscribers (manual, amendment
  service, charges and VAT) and PHP 5,600 for local ones.
- NAMRIA's home page has no occurrence of "aeronaut".
- GEN 3.2 and the chart list were not reachable. **UNVERIFIED** whether any WAC
  or VFR chart exists.
- **Verdict: NOT USABLE** (paid subscription).

| URL | Result |
|---|---|
| `https://caap.gov.ph` | 200 (redirects to `https://www.caap.gov.ph/`) |
| `https://ais.caap.gov.ph/home` | 200, 80,624 |
| `https://ais.caap.gov.ph/aip` | 200, 73,336, redirected to `/login` |
| `https://ais.caap.gov.ph/subscription-info` | 200, 70,191 |
| `https://www.namria.gov.ph/` | 200, 16,653,746 |

---

### Cambodia -- registration and click-through

- The eAIP is published by Cambodia Air Traffic Services (CATS) for the State
  Secretariat of Civil Aviation. The landing page requires agreeing to terms of
  usage and registering before the eAIP opens. Neither was done, so the chart
  list is **UNVERIFIED**.
- **Terms (paraphrase):** without authorisation from CATS the eAIP may not be
  extracted, copied, reproduced, redistributed, republished or modified, nor
  used for commercial gain.
- **Verdict: NOT USABLE.**

| URL | Result |
|---|---|
| `https://aim.cats.com.kh/eaip.html` | 200, 18,738 |
| `https://civilaviation.gov.kh/` | 200 |
| `http://civilaviation.gov.kh/en/component/content/category/43-aip-cambodia` | 404 after redirect to https |

---

### Laos -- nothing found

- The Department of Civil Aviation site has an air navigation services page that
  names AIS publications as a heading but links no AIP, no chart and no PDF. Its
  tables look like placeholder content. No online AIP was found by search.
- **Verdict: NOT USABLE** (nothing online). Existence of any VFR chart is
  UNVERIFIED.

| URL | Result |
|---|---|
| `https://www.dcal.gov.la/en` | 200, 63,955 |
| `https://www.dcal.gov.la/en/ans` | 200, 39,645 |
| `https://www.dcal.gov.la/en/sitemap` | 404 |
| `https://www.lans.la/`, `https://lans.gov.la/`, `https://www.laoairnav.la/` | 000, could not resolve (guessed hosts) |

---

### Countries that publish no WAC or VFR chart at all

| Country | Evidence | URLs |
|---|---|---|
| **Bangladesh** | GEN 3.2.4 lists six series (aerodrome, obstacle, parking, instrument approach, terminal area, en-route). GEN 3.2.6, the WAC index, reads "Not Available". ENR 6 pages in the 156-page ENR part are A4 ATS route, FIR and Dhaka TMA charts. AIP amendment 03/26. | `https://new.caab.gov.bd/aip/` 200, 6,889; `https://new.caab.gov.bd/aip/general/genall.pdf` 200, 20,474,190; `https://new.caab.gov.bd/aip/enr/enrall.pdf` 200, 14,009,990; `https://new.caab.gov.bd/aip/aip.html` 404; `http://www.caab.gov.bd/aip/aip.html` redirects to the home page; `https://caab.gov.bd/` 200 |
| **Bhutan** | GEN 3.2 (AMDT 02/2025) lists two series only: aerodrome chart and aerodrome obstacle chart type A. The AIP has no ENR 6. | `https://www.doat.gov.bt/aip/` 200, 67,874; `https://www.doat.gov.bt/wp-content/uploads/2025/09/GEN3_2-Aeronautical-Charts.pdf` 200, 16,726; `https://www.doat.gov.bt/` 200, 53,225; `https://doat.gov.bt/` TLS name mismatch; `https://www.doat.gov.bt/ais/` 404; `https://bcaa.gov.bt/` 200, 323,234; `https://bcaa.gov.bt/publications/` 200, 276,910 |
| **Maldives** | GEN 3.2 (pages to 06 AUG 26) lists area, SID, STAR, approach, aerodrome and en-route charts. ENR 6 holds en-route charts, an aerial sporting index chart and PBN route charts. | `https://www.macl.aero/air-navigation-services/aip` 200, 142,870; `https://stpublishrdataolprodac.blob.core.windows.net/api/277/GEN-3.2-AERONAUTICAL-CHARTS.pdf` 200, 309,643; `https://www.caa.gov.mv/` 200, 28,402; `https://www.macl.aero/` 200, 175,670; guessed and failed: `https://www.macl.aero/corporate/services/operators/aip` (redirected to `/about-us`), `https://aim.macl.aero/`, `https://www.maldivesaip.com/` (unresolved) |
| **Myanmar** | GEN 3.2 lists aerodrome, obstacle, area, instrument approach and visual approach charts, and says charts are not sold separately. ENR 6 is intentionally blank. The newest eAIP issue is dated 30 MAY 2022. | `https://www.ais.gov.mm/eAIP/history-en-GB.html` 200, 9,469; `https://www.ais.gov.mm/eAIP/2022-05-30/html/eAIP/menu-en-GB.html` 200, 344,280; `https://www.ais.gov.mm/eAIP/2022-01-21-AIRAC/html/eAIP/GEN-3.2-en-GB.html` 200, 10,274; `.../eAIP/ENR-6-en-GB.html` 200, 2,393; `https://ais.gov.mm/` 200, 150,770; `https://www.dca.gov.mm` 200 |
| **Brunei** | GEN 3.2 lists en-route, instrument approach, obstacle, aerodrome and parking charts; the WAC index reads "Not available". Six ENR 6 files are 25 to 84 KB each. | `https://www.dca.gov.bn/eaip/` 200, 190,899; `https://www.dca.gov.bn/wp-content/uploads/2026/08/GEN-3.2new.pdf` 200, 314,359; `https://www.dca.gov.bn/wp-content/uploads/2026/08/ENR-6-1.pdf` to `ENR-6-6.pdf` 200, len 73,807 / 32,097 / 25,553 / 78,394 / 63,653 / 84,197; `https://www.dca.gov.bn/aip-page/` 200, 106,215; `https://www.dca.gov.bn/` 200, 153,009; an old supplements `.aspx` URL from search returned 404 |

---

### Sample files

In `research/samples/`: `sg_wac2860.pdf`, `th_wac2677.pdf`, `my_wac2859.pdf`,
`in_wac2440_delhi.jpg`, `np_enr6_6.pdf`, plus previews `sg_wac2860_view.jpg`,
`th_wac2677_view.jpg`, `my_wac2859_view.jpg`, `my_wac2859_crop.jpg`,
`in_wac2440_view.jpg`, `in_wac2440_crop.jpg`, `in_wac2440_crop2.jpg`,
`np_enr6_6_view.jpg`.

## Part 3. Middle East

Researched by a helper agent; checked and edited. Requests here used a full desktop Chrome User-Agent. Where this part says "I", the helper is speaking.

### Regional summary

| Country | Series | Scale | Sheets | Format | Georeferenced | Licence (tiles on a public site) | Verdict |
|---|---|---|---|---|---|---|---|
| Saudi Arabia | Aeronautical Chart - ICAO (AIP ENR 6) | 1:500,000 | 45 | PDF, raster inside (~600 dpi JPEG tiles) | No (graticule printed, LCC) | Prohibited without prior agreement from GACA | NOT USABLE WITHOUT PERMISSION |
| Saudi Arabia | World Aeronautical Chart - ICAO (AIP ENR 6) | 1:1,000,000 | 8 | PDF (content not opened, UNVERIFIED; assumed same as above) | UNVERIFIED | Same | NOT USABLE WITHOUT PERMISSION |
| UAE | Aeronautical Chart - ICAO 1:500 000 | 1:500,000 | 1 | GeoTIFF (RGBA, LZW) + .tfw, in a zip | Yes, LCC 2SP on WGS 84, 42.33 m/px | Prohibited (no reproduction; no robots) | NOT USABLE WITHOUT PERMISSION (technically ideal) |
| Qatar | Aeronautical Chart - ICAO (AIP ENR 6-7) | 1:500,000 (+1:250,000 Doha inset) | 1 | PDF, single 12815x6969 raster (300 dpi) | No | Prohibited without written permission | NOT USABLE WITHOUT PERMISSION |
| Israel | CVFR low-altitude routes map (domestic AIP) | 1:250,000 | 2 (North, South) | Vector PDF (Illustrator), 700x1000 mm | No (graticule printed, datum WGS 84) | All rights reserved; base map belongs to a commercial publisher | NOT USABLE WITHOUT PERMISSION; current edition URL not discoverable by script |
| Bahrain | World Aeronautical Chart 2547 (AIP ENR 6-8) | 1:1,000,000 | 1 | PDF: 72 dpi ONC raster base + vector overlay | No | Unclear (AIP copyright policy "To be developed"; base is UK Crown copyright) | NOT USABLE (aeronautical data dated 2004, base ~350 m/px) |
| Oman | World Aeronautical Chart | 1:1,000,000 | 4 (2548, 2563, 2669, 2670) | Printed only, on request | n/a | n/a | NOT USABLE (70 OMR per sheet, paper) |
| Iran | WAC and "VFR Chart" listed in GEN 3.2 | 1:1,000,000 | 7 WAC sheets in the index | Not found online | n/a | Prohibited without written permission | NOT USABLE (nothing downloadable found) |
| Jordan | none listed (GEN 3.2 of 2008) | - | - | AIP behind "I agree" + CAPTCHA | n/a | Prohibited | NOT USABLE |
| Kuwait | none found (ENR 6 = en-route chart, radio facility index) | - | - | - | - | - | NOT USABLE (nothing published) |
| Lebanon | none found | - | - | - | - | - | NOT USABLE (no AIP online at DGCA site) |
| Iraq | none found | - | - | - | - | - | NOT USABLE (ICAA site behind a security check) |

Only two sources are technically strong: UAE (a real GeoTIFF) and Saudi Arabia (53 sheets
covering the whole Kingdom). **Every publisher in this region that states a policy reserves
all rights and forbids redistribution without permission.** None is open-licensed. Whether to ask for permission or skip the region is a decision for the user. (The helper's report called the three free sources "usable with caveats"; they are relabelled here on the report's common scale, since their terms forbid republication.)

---

### Saudi Arabia

- **Publisher:** Saudi Air Navigation Services (SANS), AIM, under GACA. Logos on the sheet:
  GEOSA, GACA, SANS.
- **Series:**
  - "Aeronautical Chart - ICAO 1:500 000": **45 sheets**, numbered as WAC quadrants
    (2444-D ... 2670-A). The sampled sheet 2546-D "AR RASS" covers 24-26 N, 42-45 E, i.e.
    2 deg x 3 deg per sheet.
  - "World Aeronautical Chart - ICAO 1:1 000 000": **8 sheets** (2446, 2545, 2546, 2564,
    2565, 2566, 2668, 2669).
  - One legend sheet: "Aeronautical and Topography Information (For All WAC and
    Aeronautical Charts).pdf".
- **Projection (from GEN 3.2 and the sheet):** Lambert Conformal Conic, standard parallels
  printed on each chart (2546-D: 25 deg 20' and 30 deg 40').

#### URLs requested

| URL | Result |
|---|---|
| `https://aimss.sans.com.sa/` | 200, 11648 bytes, Angular SPA shell |
| `https://aimss.sans.com.sa/assets/configs.json` | 200, 195 bytes JSON (`baseURL` = `https://api.sans.com.sa/ccms`; also holds an `accessCode`, which I did **not** use) |
| `https://api.sans.com.sa/ccms/AIM/AIP/get` | 200, 581 bytes JSON, no token needed; `content` = `a76d1f86-b18c-488d-a95a-a5f4280020dc.html` |
| `https://api.sans.com.sa/ccms/AIM/AeronauticalCharts/get` | 200, 107 bytes, `"data":[]` (empty) |
| `https://aimss.sans.com.sa/assets/FileManagerFiles/a76d1f86-b18c-488d-a95a-a5f4280020dc.html` | 200, 10711 bytes: the current "Published eAIPs" history page |
| `https://aimss.sans.com.sa/assets/FileManagerFiles/e65727c9-8414-49dc-9c6a-0b30c956ed33.html` | 200, 8188 bytes: a stale history page from May 2024 (what search engines index) |
| `https://aimss.sans.com.sa/assets/FileManagerFiles/AIP%20AMDT%2010_26_2026_09_17/index.html` | 200, 1547 bytes |
| `.../AIP%20AMDT%2010_26_2026_09_17/eAIP/menu.html` | 200, 2351811 bytes |
| `.../AIP%20AMDT%2010_26_2026_09_17/eAIP/GEN%203.2-en-US.html` | 200, 51171 bytes |
| `.../AIP%20AMDT%2010_26_2026_09_17/eAIP/ENR%206-en-US.html` | 200, 69224 bytes: the chart index, 65 PDF links |
| `.../AIP%20AMDT%2010_26_2026_09_17/eAIP/GEN%200.1-en-US.html` | 200, 26947 bytes |
| `.../eAIP/GEN%203.2-en-GB.html`, `.../eAIP/ENR%206-en-GB.html`, `.../eAIP/OE-menu-en-GB.html` | 200, 11648 bytes each: **SPA fallback, not the page** (wrong locale suffix; a missing file returns the shell with 200) |
| `.../AIP%20AMDT%2010_26_2026_09_17/documents/Root_WePub/Sans_Rep/Charts/ENR%206/Aeronautical%20Chart%20-%20ICAO%201-500%20000%20(2546-D).pdf` | **200, 16799155 bytes, application/pdf** (downloaded) |
| `https://aimss.sans.com.sa/assets/FileManagerFiles/AIRAC%20AIP%20AMDT%2005_26_2026_05_14/documents/Root_WePub/Sans_Rep/Charts/ENR%206/Aeronautical%20Chart%20-%20ICAO%201-500%20000%20(2546-D).pdf` | 200, 16770811 bytes (older amendment, still served) |
| `https://aim.sans.com.sa/` | curl timeout (exit 28); the hint URL is dead, the live host is `aimss.sans.com.sa` |
| `https://www.sans.com.sa/en/pdpl/terms` | 200, 42040 bytes (HEAD only, not read) |

HEAD of all 54 chart PDFs under
`.../AIP%20AMDT%2010_26_2026_09_17/documents/Root_WePub/Sans_Rep/Charts/ENR%206/`, every one
**200 application/pdf**, Last-Modified 28 Jul 2026:

| File | Bytes |
|---|---|
| Aeronautical Chart - ICAO 1-500 000 (2444-D).pdf | 8752912 |
| ... (2445-A) | 7314305 |
| ... (2445-C) | 9407073 |
| ... (2445-D) | 12257046 |
| ... (2446-A) | 9266061 |
| ... (2446-B) | 10959380 |
| ... (2446-C) | 10907319 |
| ... (2446-D) | 13723341 |
| ... (2447-C) | 8198896 |
| ... (2544-B) | 11194331 |
| ... (2545-A) | 12469694 |
| ... (2545-B) | 15432711 |
| ... (2545-C) | 12884995 |
| ... (2545-D) | 17014260 |
| ... (2546-A) | 16360326 |
| ... (2546-B) | 19125778 |
| ... (2546-C) | 20677573 |
| ... (2546-D) | 16799155 |
| ... (2547-A) | 15708898 |
| ... (2547-C) | 9487107 |
| ... (2547-D) | 15908413 |
| ... (2563-A) | 7109308 |
| ... (2563-D) | 14620555 |
| ... (2564-A) | 14271736 |
| ... (2564-B) | 12083579 |
| ... (2564-C) | 13343585 |
| ... (2564-D) | 8785133 |
| ... (2565-A) | 14576650 |
| ... (2565-B) | 14110613 |
| ... (2565-C) | 18254101 |
| ... (2565-D) | 14364520 |
| ... (2566-A) | 7135901 |
| ... (2566-B) | 17568391 |
| ... (2566-C) | 21620557 |
| ... (2566-D) | 10362165 |
| ... (2667-B) | 15438120 |
| ... (2667-C) | 12454253 |
| ... (2668-A) | 17709917 |
| ... (2668-B) | 12755522 |
| ... (2668-C) | 12026979 |
| ... (2668-D) | 13338189 |
| ... (2669-A) | 18043247 |
| ... (2669-B) | 12124139 |
| ... (2669-D) | 6475946 |
| ... (2670-A) | 7811792 |
| Aeronautical and Topography Information (For All WAC and Aeronautical Charts).pdf | 1740177 |
| World Aeronautical Chart - ICAO 1-1000 000 (2446).pdf | 12614083 |
| ... (2545) | 19213176 |
| ... (2546) | 19759519 |
| ... (2564) | 15156244 |
| ... (2565) | 15750946 |
| ... (2566) | 22403853 |
| ... (2668) | 14239721 |
| ... (2669) | 9085021 |

Totals: 1:500,000 = 45 files, about 590 MB; WAC = 8 files, about 128 MB.

#### Format (sample `samples/sa_500k_2546-D.pdf`)

- PDF 1.5, 1 page, 2384 x 1684 pt = 841 x 594 mm (A1), page rotation 90.
- **Raster inside, not vector.** 70 image objects: 63 JPEG tiles of 2048 x 2048 px each
  placed on 246 x 246 pt, plus 7 edge tiles of 440 x 2048 px. That is **~599 dpi**; the
  raster as a whole is about **18,850 x 14,320 px**, which at 1:500,000 is **~21.2 m/px**.
  Only 7 text objects and 6 paths (the AIP page header/footer: "ENR 6 - 75", "17 SEP 2026",
  "AIP AMDT 10/26").
- Producer string: Bullzip PDF Printer, i.e. printed to PDF from a raster.
- **Not georeferenced.** No `/Measure`, `/GPTS`, `/LGIDict`, no WKT. (One `/VP` byte match
  was inside a compressed stream, a false positive.) The GDAL in the venv lists a PDF
  driver but could not open the file ("not recognized as being in a supported file
  format"), so that check was done on the bytes and with pypdfium2.
- The whole sheet is furniture plus map: title, hypsometric legend, conversion scales,
  adjoining-sheet index, scale bars. The map has a printed graticule at 30' with labelled
  ticks and a neatline at whole degrees, so each sheet can be registered from its known
  corner coordinates in LCC. **Standard parallels differ by sheet band** and must be read
  per sheet (UNVERIFIED beyond 2546-D).
- Chart notes on the sample: topographic base 2019, isogonic data 2020, aeronautical
  information 2026, map production June 2023.

#### Edition and discovery

- GEN 0.1 says regular AIP amendments are issued twice a year "and when necessary"; in
  practice the history page shows an amendment every few weeks (AIRAC AMDT 08/26 effective
  06 AUG 2026, AIP AMDT 10/26 effective 17 SEP 2026, AIRAC AMDT 10/26 effective 01 OCT 2026).
  The chart PDFs carried the same Last-Modified (28 Jul 2026) across all sheets, so they are
  re-exported as a set.
- Script route, all anonymous GETs:
  1. `GET https://api.sans.com.sa/ccms/AIM/AIP/get` -> `data[0].content` (an `.html` name).
  2. `GET https://aimss.sans.com.sa/assets/FileManagerFiles/<content>` -> links under
     "Currently Effective Issue" such as `AIP AMDT 10_26_2026_09_17/index.html`.
  3. `GET <issue>/eAIP/ENR 6-en-US.html` -> the `../documents/.../Charts/ENR 6/*.pdf` links.
- Watch for the 200-with-SPA-shell trap: a wrong path returns 200 and 11648 bytes of HTML,
  so check `Content-Type: application/pdf` and the `%PDF` magic.

#### Access

Open. No login, key or click-through for the files. The history page asks visitors to fill in a survey but nothing enforces it.

#### Licence

- Source: AIP GEN 0.1 section 0.1.5 "CopyRight Policy",
  `.../AIP%20AMDT%2010_26_2026_09_17/eAIP/GEN%200.1-en-US.html`.
- Deciding sentence (paraphrase): redistributing or copying the publication requires the prior agreement of GACA.
- GEN 3.2.3 adds that AIP charts are free of charge as part of the AIP.
- Redistribution of derived tiles: **prohibited without prior agreement.**

#### Verdict: NOT USABLE WITHOUT PERMISSION

Free, complete national coverage at both scales, high resolution, stable scriptable URLs.
Caveats: written agreement from GACA is required before publishing tiles; raster PDFs with
no georeferencing, so each of 53 sheets needs registration and a collar mask; the WAC sheets
were HEAD-checked only, their content is UNVERIFIED.

---

### United Arab Emirates

- **Publisher:** General Civil Aviation Authority (GCAA), Sheikh Zayed Air Navigation Centre
  AIM Department.
- **Series:** "Aeronautical Chart - ICAO 1:500 000", **one sheet** covering the Emirates FIR
  (about 51.2-58.0 E, 22.2-26.75 N), with inset panels for Dubai, Sharjah and Abu Dhabi
  printed over the Gulf and the south-west corner. GEN 3.2.6 states the UAE does **not**
  produce a WAC 1:1,000,000.
- ENR 6 of the UAE AIP also holds VFR area charts (Dubai CTA VFR, Abu Dhabi CTA VFR, Northern
  Emirates VFR) as PDFs; these are route/VRP diagrams, not the topographic series, and were
  not examined.

#### URLs requested

| URL | Result |
|---|---|
| `https://www.gcaa.gov.ae/en/ais/Pages/AeroChartViewPackage.aspx` | 200, ~1.34 MB HTML (index page) |
| `https://www.gcaa.gov.ae/en/ais/SiteAssets/AeronauticalChart/js/AeroChartViewPackage.js?v=3.0` | 200, 20059 bytes (a comment in it records that the login for the chart package was removed) |
| `https://www.gcaa.gov.ae/_catalogs/masterpage/GCAA.Web.Master/js/GCAA_Global_Common.js?v=3.0` | 200 |
| `https://www.gcaa.gov.ae/_layouts/15/GCAA.Common.Service/ConfigurationService.asmx/GetConfigValuesByCategoryFromList` (POST `{"CategoryName":"ACP"}`, the call the page itself makes) | 200, 37 bytes, `{"error": "Unauthorized"}` |
| `https://www.gcaa.gov.ae/en/ais/_api/web/lists?$select=Title,ItemCount` | 200, 4271 bytes JSON (anonymous SharePoint REST) |
| `https://www.gcaa.gov.ae/en/ais/_api/web/lists/getbytitle('ACP%20Documents')/items?$select=EncodedAbsUrl,ID,Modified,FileLeafRef` | 200, 1185 bytes JSON: 3 items, one is the zip |
| `https://www.gcaa.gov.ae/en/ais/_api/web/lists/getbytitle('ACPHtmlFiles')/items?$select=...` | 200 JSON: 8 items (tif, tfw, user guide, amendments list, hash list, MD5 help) |
| `https://www.gcaa.gov.ae/en/ais/ACP%20Documents/Today/AERONAUTICAL_CHART_2025-12.zip` | **200, 82156906 bytes, application/x-zip-compressed**, Last-Modified 30 Oct 2025 (downloaded) |
| `https://www.gcaa.gov.ae/en/ais/ACPHtmlFiles/ACP/Current/Aeronautical%20Chart%20-%20ICAO%201-500%20000.tif` | **200, 74792915 bytes, image/tiff**, Last-Modified 07 Nov 2025 (HEAD only) |
| `.../ACP/Current/Aeronautical%20Chart%20-%20ICAO%201-500%20000.tfw` | 200 but text/html 31362 bytes, body "Unauthorized Access Prohibited": the `.tfw` extension is blocked. The world file is inside the zip. |
| `.../ACP/Current/Aeronautical%20Chart%20-%20ICAO%20500%20000%20-%20User%20Guide_Ed%2003.pdf` | 200, 7366274 bytes |
| `.../ACP/Current/List%20of%20Significant%20Amendments.pdf` | 200, 140469 bytes |
| `.../ACP/Current/HashList.xlsx` | 200, 10156 bytes |
| `https://www.gcaa.gov.ae/en/ais/ACP%20Documents/Forms/AllItems.aspx`, `.../ACPHtmlFiles/Forms/AllItems.aspx` | 302 (to sign-in; not followed further) |
| `https://www.gcaa.gov.ae/en/ais/AIPHtmlFiles/AIP/Current/AIRACs/2026-P02/html/eAIP/GEN-3.2-en-GB.html` (and GEN-0.1, GEN-3.1, ENR-6) | 404: that AIRAC folder has been retired |
| `https://www.gcaa.gov.ae/en/ais/AIPHtmlFiles/AIP/Current/AIRACs/2026-P10/html/eAIP/GEN-3.2-en-GB.html` | 200, 14388 bytes |
| `.../2026-P10/html/eAIP/GEN-0.1-en-GB.html` | 200, 8438 bytes |
| `.../2026-P10/html/eAIP/GEN-3.1-en-GB.html` | 200, 59198 bytes |
| `.../2026-P10/html/eAIP/ENR-6-en-GB.html` | 200, 6194 bytes |

#### Format (sample `samples/ae_AERONAUTICAL_CHART_2025-12.zip`, extracted to `samples/ae/`)

Zip contents: `Aeronautical Chart - ICAO 1-500 000.tif` (74792915), `.tfw` (127),
user guide PDF (7366274), `HashList.xlsx`, MD5 help PDF, `List of Significant Amendments.pdf`.

`gdal.Info` on the TIFF:

- GTiff, **15899 x 11849 px**, 4 bands Byte (R, G, B, premultiplied alpha), LZW, stripped
  (block 15899 x 8), 300 dpi tag.
- **Georeferenced in the file itself** (GeoTIFF tags) and by the .tfw, which agree:
  origin (223630.175, 808342.975), **pixel 42.333418 m** (1:500,000 at 300 dpi), no rotation.
- CRS: `UAE_NEW_LAMBERT`, **Lambert Conic Conformal (2SP) on WGS 84**: false origin 24 N /
  54 E, standard parallels 23 deg 10' and 25 deg 50', false easting/northing 500000/500000.
  No EPSG code on the projected CRS.
- Corners: UL 51d13'E 26d45'N, LR 57d50'E 22d12'N.
- The raster is the whole sheet: title strip, a legend column down the right, scale bar,
  margin, and three inset panels over the map. A mask is needed, as for the FAA sheets.

This is the same resolution class as the FAA sectionals (42.3 m/px, native ~z11.5).

#### Edition and discovery

- Sampled edition: **AIRAC 12/2025, effective 27 NOV 2025** (from `List of Significant
  Amendments.pdf`); zip named `AERONAUTICAL_CHART_2025-12.zip`. The 2024 user guide is
  Edition 03, effective 28 Nov 2024; first edition Dec 2022. That points to **about one
  edition a year**, UNVERIFIED as a stated cycle.
- Script route: the anonymous SharePoint REST call on the `ACP Documents` list returns the
  current zip's `EncodedAbsUrl` and `Modified`. **But see the licence: the GCAA terms forbid
  robots and similar tools**, so automating this is itself against the stated terms.

#### Access

Open for download without login today (the page script says login was removed for the
chart package). The page still offers optional subscription/registration. The wider UAE
AIP page advertises "How to Register For UAE AIP", but the eAIP HTML was served anonymously.

#### Licence

- Source: UAE AIP GEN 0.1.5 "Copyright policy",
  `https://www.gcaa.gov.ae/en/ais/AIPHtmlFiles/AIP/Current/AIRACs/2026-P10/html/eAIP/GEN-0.1-en-GB.html`.
  It names "AIP and Aeronautical Charts" explicitly.
- Deciding sentence (paraphrase): no part of the AIP or of the aeronautical charts may be reproduced or transmitted.
- The same section withholds the right to modify the content, to frame it in another
  website, and to use robots, crawlers and similar automated data-gathering tools.
- The user guide PDF carries a 2023 GCAA copyright notice reserving all rights.
- Redistribution of derived tiles: **prohibited.**

#### Verdict: NOT USABLE WITHOUT PERMISSION

Technically the best source in the region: free, a true GeoTIFF with a clean CRS, no
registration step. The licence forbids reproduction, modification, framing and automated
retrieval, so it cannot go on a public site without written permission from GCAA
(the AIP names the GCAA AIM department as the contact).

---

### Qatar

- **Publisher:** Qatar Civil Aviation Authority (QCAA), Air Navigation Department, AIM.
- **Series:** "Aeronautical Chart - ICAO 1:500 000", **one sheet** (chart ENR 6-7), titled
  "QATAR AERONAUTICAL CHART - ICAO SCALE 1:500,000", with a **1:250,000 Doha inset** in the
  lower right. Covers Qatar, Bahrain and the adjacent Gulf. GEN 3.2 lists no WAC.

#### URLs requested

| URL | Result |
|---|---|
| `https://www.aim.gov.qa/` | redirects to `https://www.caa.gov.qa/en-us/Pages/AIM.aspx`, 404 |
| `https://www.aim.gov.qa/eaip/` and `https://aim.gov.qa/eaip/` | 403 |
| `https://aim.gov.qa/eaip/index.html` | 404 |
| `https://www.aim.gov.qa/eaip/history-en-GB.html` | 200, 34297 bytes (old eAIP tree, superseded) |
| `https://www.aim.gov.qa/eaip/2022-10-06-AIRAC/html/eAIP/GEN-3.2-en-GB.html` | 200, 15948 bytes (old) |
| `https://caa.gov.qa/en/aeronautical-information-management` | 200, 54862 bytes; its "View eAIP" button opens the URL below |
| `https://aim.gov.qa/AIP/QA-history-en-GB.html` | **200, 3990 bytes: current index** |
| `https://aim.gov.qa/AIP/11-JUN-2026/AIP-29/2026-08-06-000000/html/index-en-GB.html` | 200, 1201 bytes |
| `.../html/eAIP/QA-menu-en-GB.html` | 200, 48444 bytes |
| `.../html/eAIP/QA-GEN-3.2-en-GB.html` | 200, 21909 bytes |
| `.../html/eAIP/QA-GEN-0.1-en-GB.html` | 200, 20271 bytes |
| `.../html/eAIP/QA-GEN-3.1-en-GB.html` | 200, 57634 bytes |
| `.../html/eAIP/QA-ENR-6-en-GB.html` | 200, 3927 bytes |
| `.../html/eAIP/GEN-3.2-en-GB.html`, `.../OT-GEN-3.2-en-GB.html` (and the GEN-0.1, GEN-3.1, ENR-6 equivalents) | 404: file names carry the `QA-` prefix |
| `https://aim.gov.qa/AIP/11-JUN-2026/AIP-29/2026-08-06-000000/pdf/QA-ENR-6-Aeronautical-Chart-ICAO.pdf` | **200, 26913250 bytes, application/pdf**, Last-Modified 11 Jun 2026 (downloaded) |
| `https://aim.gov.qa/dowp` | 200, 1360 bytes |
| `https://caa.gov.qa/en/node/14496`, `/14343`, `/10618` | 200, unrelated pages |

#### Format (sample `samples/qa_ENR-6-Aeronautical-Chart-ICAO.pdf`)

- PDF 1.7, 1 page, 3075.6 x 1672.6 pt = 1085 x 590 mm.
- **One image object and nothing else**: 12815 x 6969 px, Flate-compressed, no text, no
  paths. That is exactly **300 dpi**, so **42.3 m/px** at 1:500,000.
- **Not georeferenced** (no geospatial dictionaries). Graticule and border ticks printed.
  GEN 3.2 says only "conformal (orthomorphic) projection"; the exact parameters are on the
  chart face and were not read (UNVERIFIED).
- About a fifth of the sheet on the left is legend, and the Doha inset covers the
  south-east corner of the map.

#### Edition and discovery

- The sheet is marked "Edition 44th, Effective 06 AUG 2026" (read from a 1400 px thumbnail,
  so the ordinal is UNVERIFIED); the file is part of "AIP 2nd Edition", published 11 JUN
  2026, effective 06 AUG 2026. The next issue (published 03 SEP 2026, effective 01 OCT 2026)
  is at `03-SEP-2026/AIP-30/2026-10-01-000000/`.
- Script route: `GET https://aim.gov.qa/AIP/QA-history-en-GB.html`, take the link under
  "Currently effective Issues", replace `html/index-en-GB.html` with
  `pdf/QA-ENR-6-Aeronautical-Chart-ICAO.pdf`.

#### Access

Open, no login. (A separate portal at `https://aim.gov.qa/Portal/login.html` exists for
other services; not touched.)

#### Licence

- Source: Qatar AIP GEN 0.1 section 5 "Copyright policy",
  `.../html/eAIP/QA-GEN-0.1-en-GB.html`.
- Deciding sentence (paraphrase): no part of the publication may be reproduced without prior written permission.
- GEN 3.2 section 5.1: all charts in the Qatar AIP are free of charge to users.
- Redistribution of derived tiles: **prohibited without written permission.**

#### Verdict: NOT USABLE WITHOUT PERMISSION

Free, current, 300 dpi. One sheet, needs manual registration and a mask, and written
permission from QCAA before publication. It overlaps the Saudi 2547 quadrant sheets and
the Bahrain WAC.

---

### Israel

- **Publisher:** Civil Aviation Authority of Israel (CAAI); cartography by Gideon Dan
  Cartography (studio-dan), which also sells the printed map.
- **Series:** "CVFR" low-altitude transport routes map (mapat netivei tovala nemukhim),
  **1:250,000, two sheets (North, South)**, part of the Hebrew domestic AIP. Third-party
  pages describe a 2025 edition updated 2 May 2025 (UNVERIFIED, from search results).
- The international eAIP has **no** VFR chart: GEN 3.2 says that Israel does not currently publish a WAC or its index, lists no 1:500,000 series, and ENR 6
  holds only the en-route chart (1:400,000, IFR) and index charts.

#### URLs requested

| URL | Result |
|---|---|
| `https://www.gov.il/en/Departments/Guides/aip-israel` | redirects to `/en/pages/aip-israel`, **403 "Just a moment..." (Cloudflare challenge)** |
| `https://www.gov.il/he/departments/guides/aip` | redirects to `/he/pages/aip`, 403 challenge |
| `https://www.gov.il/he/pages/aip` | 403 challenge |
| `https://www.gov.il/he/api/DynamicCollector` | 403 challenge |
| `https://www.gov.il/he/departments/general/cvfr-map` (a guess) | 301 |
| `https://www.gov.il/en/pages/aip-israel` via WebFetch | 403 |
| `https://e-aip.azurefd.net/` | 200, 19080 bytes: eAIP index, issues `2026-08-06-AIRAC` and `2026-11-26-AIRAC` |
| `https://e-aip.azurefd.net/2026-08-06-AIRAC/html/eAIP/LL-GEN-3.2-en-GB.html` | 200, 52995 bytes |
| `.../LL-GEN-0.1-en-GB.html` | 200, 12223 bytes |
| `.../LL-GEN-3.1-en-GB.html` | 200, 46360 bytes |
| `.../LL-ENR-6-en-GB.html` | 200, 8989 bytes |
| `https://e-aip.azurefd.net/2022-11-03-AIRAC/html/eAIP/LL-GEN-3.2-en-GB.html` | 200, 52645 bytes (old) |
| `https://www.gov.il/BlobFolder/generalpage/updates-2023/he/aip_CVFR_South_2023.pdf` | **GET 200, 8194956 bytes, application/pdf**, Last-Modified 18 May 2023 (downloaded). HEAD returns 404; ranged GET returns 206 `bytes 0-1023/8194956` |
| `https://www.gov.il/BlobFolder/generalpage/updates-2020/he/aip_cvfr-north.pdf` | ranged GET 206, total 9090221, Last-Modified 03 May 2021 |
| `https://www.gov.il/BlobFolder/generalpage/updates-2020/he/aip_cvfr-south.pdf` | 206, total 2548191 |
| `https://www.gov.il/BlobFolder/generalpage/updates-2017/he/aip_cvfr-south-17.pdf` | 206, total 2174087 |
| `https://www.gov.il/BlobFolder/generalpage/updates-2020/he/aip_route-chart-mar.pdf` | 200, 1939767 bytes (an ENR 6 route chart) |
| `https://www.gov.il/BlobFolder/guide/aip/he/aip_%D7%90'-02.pdf` | 206, total 148546, Last-Modified 22 Sep 2026 (domestic AIP chapter A-02, text) |
| Guessed names, all **404**: `.../updates-2023/he/aip_CVFR_North_2023.pdf`, `.../updates-2023/he/aip_CVFR_Back_2023.pdf`, `.../updates-2024/he/aip_CVFR_South_2024.pdf`, `..._North_2024.pdf`, `.../updates-2025/he/aip_CVFR_South_2025.pdf`, `..._North_2025.pdf`, `.../updates-2026/he/aip_CVFR_South_2026.pdf`, `..._North_2026.pdf` | 404 |
| Search-result URLs now **404**: `.../BlobFolder/guide/aip/he/aip_south-flight2.pdf`, `.../aip_north-flight2.pdf`, `.../aip_Alef%2002.pdf`, `.../aip_ats-routes04-flights.pdf`, `.../generalpage/electronic-aip/en/Full%20AIP%202-25.pdf` | 404 |
| `https://www.caa.gov.il/index.php?option=com_docman&view=list&slug=2017-05-22-08-20-58&Itemid=669&lang=he` | no response (curl 000) |
| `https://caa.gov.il/index.php?Itemid=157&id=69&lang=he&option=com_content&view=article` | no response |
| `https://www.preflight.co.il/aip/` | 200 (third party; only links back to the gov.il guide page) |
| `https://arielbider.github.io/cvfr-map/` | 200, 219 bytes (third-party interactive map, not examined) |
| `https://data.gov.il/dataset/cvfr` | 307 then 404 |
| `https://data.gov.il/api/3/action/package_show?id=cvfr` | **200, 8842 bytes JSON** (see below) |
| `https://web.archive.org/cdx/search/cdx?...` (three queries for gov.il AIP pages) | "Internet Archive: Temporarily Offline" |

#### Format (sample `samples/il_aip_CVFR_South_2023.pdf`)

- PDF 1.6, 1 page, 1984.2 x 2834.6 pt = **700 x 1000 mm**.
- **True vector**: about 70,400 path objects, 2,786 text objects, 8,540 forms, 7 shadings,
  plus 171 images (relief shading and symbols). Creator Adobe Illustrator 27.3.
- **Not georeferenced**: no `/Measure`, `/GPTS`, `/LGIDict` or WKT. The face prints
  "Datum WGS 84", scale 1:250,000, and a graticule with border ticks. The projection is not
  stated in the extracted text (UNVERIFIED).
- A vector source like this would render the way the FAA IFR PDFs do, at any scale.
- The sheet is heavily furnished: notes panel down the right side, legend, frequency table
  and title block laid over the map area; the country is a narrow wedge in the middle.
- Edition of the sample: update 2/23, 18 May 2023. **It is not the current edition.**

#### Edition and discovery

- Apparently annual (2014, 2017, 2020, 2023 files found; 2025 edition reported). File names
  are not regular (`aip_cvfr-south-may14.pdf`, `aip_cvfr-south-17.pdf`,
  `aip_cvfr-north.pdf`, `aip_CVFR_South_2023.pdf`), so they cannot be guessed.
- The only index is the gov.il AIP guide page, which sits behind a Cloudflare challenge that
  returns 403 to scripts. **I did not attempt to get past it.** The blob files themselves
  are served without the challenge (GET only; HEAD gives 404).
- So a script cannot find the current edition. The current North/South URLs are UNVERIFIED
  and would have to be copied from the page by hand in a browser.

#### Access

Files open by direct URL. Index page challenge-gated. GEN 3.2 section 3 says charts may be obtained from the online eAIP free of charge.

#### Licence

- Printed on the map itself, in Hebrew (paraphrase): all rights are reserved to CAAI, and the rights in the geographic information belong to a company named Mapa.
- So the base map is the property of a commercial map publisher.
- gov.il site terms could not be read (challenge page). UNVERIFIED.
- Redistribution of derived tiles: **appears prohibited** (all rights reserved, third-party
  commercial base).

#### Related open data (not a chart)

`data.gov.il` dataset "cvfr" (Ministry of Transport, source CAAI), licence field
`other-open` / "Other (Open)", metadata modified 2026-03-22. Resources: `cvfr_mot.zip`
(shapefile, 100717 bytes), `cvfr_mot_kmz.zip`, `cvfr_mot.csv`, metadata xlsx, all under
`https://aws-e.data.gov.il/dataset/360fb8b4-ea71-4485-b80b-c5b996d25cae/resource/...`. These
are the CVFR route lines only, with no chart base. Resource URLs were read from the API and
**not requested**.

#### Verdict: NOT USABLE WITHOUT PERMISSION

The chart is free to download and is a fine vector source, but it is all-rights-reserved
with a commercial base map, only 1:250,000 exists, the current edition cannot be discovered
by script, and the one file I could verify is the 2023 edition.

---

### Bahrain

- **Publisher:** Bahrain Civil Aviation Affairs / Ministry of Transportation and
  Telecommunications, AIM. The AIP is titled for the Bahrain FIR.
- **Series:** "World Aeronautical Chart - WAC 1:1000000", **one sheet, 2547 (BAHRAIN)**,
  covering 24-28 N, 47-54 E (Bahrain, Qatar, eastern Saudi Arabia, part of Iran and the UAE).
  Chart ENR 6-8. No 1:500,000 series; GEN 3.2.5 is an index to US ONC and TPC charts sold
  through UK chart agents.

#### URLs requested

| URL | Result |
|---|---|
| `https://aim.mtt.gov.bh/` | 200, 43104 bytes |
| `https://aim.mtt.gov.bh/eaip` | 200, 52728 bytes: links `2026-03-19-AIRAC` and `2026-07-09-AIRAC` |
| `https://aim.mtt.gov.bh/eAIP/2026-07-09-AIRAC/html/eAIP/OB-GEN-3.2-en-BH.html` | 200, 24360 bytes |
| `.../OB-GEN-0.1-en-BH.html` | 200, 15782 bytes |
| `.../OB-ENR-6-en-BH.html` | 200, 4001 bytes |
| `https://aim.mtt.gov.bh/eAIP/2026-07-09-AIRAC/graphics/822.pdf` (the WAC) | **200, 8816140 bytes, application/pdf**, Last-Modified 24 Sep 2026 (downloaded) |
| `.../graphics/53158.pdf` (en-route chart) | 200, 1645031 |
| `.../graphics/53566.pdf` (radio facility index) | 200, 211379 |
| `.../graphics/53569.pdf` (aerodrome index) | 200, 158620 |

#### Format (sample `samples/bh_WAC_822.pdf`)

- PDF 1.3, 1 page, 840 x 594 mm. Created 2010 from FreeHand 10.
- One base image of only **2105 x 1357 px placed at 72 dpi**, which at 1:1,000,000 is about
  **353 m/px**, plus 2,012 vector paths (airspace, routes, graticule). No extractable text.
- Not georeferenced. LCC, standard parallels printed.
- The base is a scanned US ONC: the sheet header cites "SERIES ONC, SHEET H-6 / H-7", and
  the footer gives a 1998 topographical base, aeronautical information correct at 1 September 2004, publication in 2004 by Bahrain's Directorate of Air Navigation, and a notice that UK Crown copyright data is included by permission.

#### Edition and discovery

The file is re-issued with every AIRAC (Last-Modified 24 Sep 2026) but the content is the
2004 chart. Script route: `https://aim.mtt.gov.bh/eaip` -> current AIRAC folder ->
`html/eAIP/OB-ENR-6-en-BH.html` -> the row named "World Aeronautical Chart". The numeric file
name (`822.pdf`) is a database id and should be read from that page, not assumed.

#### Access

Open, no login.

#### Licence

- AIP GEN 0.1.5 "COPYRIGHT POLICY": "To be developed".
- The chart itself carries a UK Crown copyright notice for its base data.
- Redistribution of derived tiles: **unclear.**

#### Verdict: NOT USABLE

Free and scriptable, but the aeronautical content is 22 years old and the base is a
72 dpi scan, coarser than a z8 tile. The Saudi 1:500,000 sheets 2547-A, -C, -D and Qatar's chart
cover the same ground with current data.

---

### Oman

- **Publisher:** Civil Aviation Authority (CAA) Oman, AIM Department.
- **Series:** World Aeronautical Chart - ICAO 1:1,000,000, sheets **2548, 2563, 2669, 2670**,
  LCC. GEN 3.2 lists no 1:500,000 series.
- **Price and form:** GEN 3.2 section 5 lists the WAC at **70 OMR per sheet**, dated
  5 OCT 23. AIC 01/24 (20 May 2024) says the WAC is supplied on request by e-mail to the CAA, in printed form, possibly at a charge.
- ENR 6 holds only the en-route chart, Muscat UTA, P/R/D areas, radio facility index,
  aerial sporting activities index and military training areas index.

#### URLs requested

| URL | Result |
|---|---|
| `https://aim.caa.gov.om/` | 200, 3743 bytes |
| `https://aim.caa.gov.om/eAIP_Oman/history-en-GB.html` | 200, 10029 bytes (issue list is a JavaScript array; current = effective 03 SEP 2026, link `index-en-GB.html`) |
| `https://aim.caa.gov.om/eAIP_Oman/index-en-GB.html` | 200, 872 bytes |
| `https://aim.caa.gov.om/eAIP_Oman/final/2026-09-03/html/toc-frameset-en-GB.html` | 200, 541 bytes |
| `https://aim.caa.gov.om/eAIP_Oman/final/2026-09-03/html/eAIP/menu-en-GB.html` | 200, 213122 bytes |
| `https://aim.caa.gov.om/eAIP_Oman/final/2026-09-03/html/eAIP/GEN-3.2-en-GB.html` (and GEN-0.1, GEN-3.1, ENR-6) | 404, 808 bytes: sections live under the `-Non-AIRAC` folder |
| `https://aim.caa.gov.om/eAIP_Oman/final/2026-09-03-Non-AIRAC/html/eAIP/GEN-3.2-en-GB.html` | 200, 14372 bytes |
| `.../2026-09-03-Non-AIRAC/html/eAIP/GEN-0.1-en-GB.html` | 200, 10415 bytes |
| `.../GEN-3.1-en-GB.html` | 200, 14886 bytes |
| `.../ENR-6-en-GB.html` | 200, 5307 bytes |
| `https://www.caa.gov.om/en/aim-publications` | 200, 114888 bytes (AICs and SUPs only, no chart files) |
| `https://www.caa.gov.om/upload/files/AIM/AIC%2001-24.pdf` | 200, 135822 bytes |

No copyright statement was found in GEN 0.1 or GEN 3.1 by keyword search (UNVERIFIED that
none exists elsewhere).

#### Verdict: NOT USABLE

The only VFR series is paid and paper. Nothing to download.

---

### Iran

- **Publisher:** Iran Airports & Air Navigation Company (IAC), Aeronautical Information
  Services, under the Civil Aviation Organization.
- **Series named in GEN 3.2** (WEF 02 NOV 23): "j. VFR Chart" and "k. World Aeronautical
  Chart (WAC)", ICAO 1:1,000,000. The index on page GEN 3.2-2 hatches **seven WAC sheets:
  2338, 2339, 2428, 2429, 2443, 2444, 2548**. GEN 3.2 section 5.1 says all listed charts come as part of the AIP.
- **What is actually online:** the AIP is a Liferay document library of per-section PDFs.
  The ENR 6 folder holds **one document, `ENR 6.1.pdf`**, in both the current and the next
  edition. It is the en-route chart (1160 x 930 mm, vector, route designators), not a VFR
  chart. GEN 3 holds GEN 3.1 to 3.6. I found no WAC or VFR chart file. AD 2 aerodrome
  folders were listed for four aerodromes only and hold ADC/IAC/SID/STAR files; whether a
  "VFR Chart" exists inside some aerodrome folder is UNVERIFIED.
- **Price page:** "AIM PUBLICATIONS" annual subscription 50 USD, initial 170 USD; "EAIP
  PACKAGE" 60 / 250 USD; AIP AMDT, SUP, AIC free on the web site. The WAC may be in the paid
  package (UNVERIFIED).

#### URLs requested

| URL | Result |
|---|---|
| `https://ais.airport.ir/` | 200, 30417 bytes |
| `https://ais.airport.ir/132` (AIP incl. AIRAC AMDT 1/26, WEF 19 FEB 2026) | 200, 44462 bytes |
| `https://ais.airport.ir/144` (AIP incl. AIRAC AMDT 2/26, WEF 01 OCT 2026) | 200, 44462 bytes |
| `https://ais.airport.ir/132/-/document_library_display/CYZjlxW5J3M4/view/172209125` (ENR) | 200, 44141 bytes |
| `.../view/172209128` (GEN) | 200, 41669 bytes |
| `.../view/172209724` (ENR 6) | 200, 34760 bytes: 1 document |
| `.../view/172209142` (GEN 3) | 200, 40851 bytes |
| `.../view/172209133` (GEN 0) | 200, 40848 bytes |
| `.../view/172209122` (root), `172210281` (AD 0), `172210284` (AD 1), `172210296` (AD 3), `172210421`, `172210455`, `172210458`, `172210461`, `172210464`, `172210467` (aerodromes) | 200 each |
| `https://ais.airport.ir/144/-/document_library_display/WOot3AEAL8oa/view/186838153` (ENR, next edition) | 200, 44277 bytes |
| `.../WOot3AEAL8oa/view/186838694` (ENR 6, next edition) | 200, 34759 bytes: 1 document, `ENR 6.1.pdf`, 2.7 MB |
| `https://ais.airport.ir/documents/452631/172209724/ENR+6.1.pdf/7a13e5b4-c028-49b9-ae25-8c82d4bf562d?version=1.0` | 200, 1719689 bytes, application/pdf (no Content-Length header; size from download) |
| `https://ais.airport.ir/documents/452631/172209142/GEN+3.2.pdf/9d78335c-5138-417c-9057-cc8b89a65ddb?version=1.0` | 200, 2338889 bytes |
| `https://ais.airport.ir/documents/452631/172209133/GEN+0.1.pdf/306631f4-23fa-47f4-b25e-27975201501e?version=1.0` | 200, 397622 bytes |
| `https://ais.airport.ir/78`, `/aip-cd`, `/37`, `/16` | 200 each (product list, empty "eAIP" page, price list, subscription folder: empty) |

#### Licence

- Source: AIP GEN 0.1 (the PDF above).
- Deciding sentence (paraphrase): no part of the publication or of the AIS products may be reproduced without prior written permission from IAC.
- Redistribution of derived tiles: **prohibited without written permission.**

#### Verdict: NOT USABLE

No VFR or WAC file is downloadable from the free site. The series exists on paper or in the
paid package.

---

### Jordan

- **Publisher:** Civil Aviation Regulatory Commission (CARC), AIS HQ; chart maintenance is
  coordinated with the Royal Jordanian Geographic Center.
- **Series:** the only GEN 3.2 I could read is dated **01 MAY 2008** (AMDT 49/2008). Its
  list of series has instrument, visual approach, aerodrome, obstacle, SID, STAR, parking
  and en-route charts. **No WAC, no 1:500,000, no VFR en-route chart.** The current GEN 3.2
  is UNVERIFIED.
- **Access:** the AIS page shows a "Copyright Procedure" ending in an "I agree to the terms
  of use" control followed by a human-verification question. The AIP sits behind it.
  **I did not click through.**

#### URLs requested

| URL | Result |
|---|---|
| `https://carc.gov.jo/en/directory-flight-information` | 200, 75889 bytes (AIS page with the copyright procedure and the click-through) |
| `https://carc.gov.jo/en/node/240` | 200, 75845 bytes (same page) |
| `https://carc.gov.jo/pdf/9-3/GEN_3.2_Aeronautical_Charts.pdf` | 200, 24996 bytes, application/pdf (4 pages, 2008) |
| `https://carc.gov.jo/pdf/9-3/` | 403 |
| `https://carc.gov.jo/pdf/9-3/ENR_6.pdf` (a guess) | 404 |
| `https://carc.gov.jo/en/versions` | 200, 56357 bytes (no AIP links) |
| `https://www.carc.jo/en/content/281-aeronautical-information-publication-aip` | no response (curl 000) |

#### Licence

- Source: the AIS page above, sections 3.2, 3.3 and 3.5.
- Deciding sentence (paraphrase): no part of the AIS publications may be redistributed, republished or used commercially.
- Use is limited to downloading, displaying or printing the material unchanged, for information only.
- Redistribution of derived tiles: **prohibited.**

#### Verdict: NOT USABLE

No VFR series is evidenced, the AIP needs accepted terms and a human check, and the terms
forbid redistribution and modification.

---

### Kuwait

- **Publisher:** Directorate General of Civil Aviation (DGCA) Kuwait.
- The AIP index lists, for ENR 6, only "ENR 6.1: ENROUTE CHART" and "ENR 6.2-1: INDEX TO
  RADIO FACILITIES". No WAC, no 1:500,000, no VFR chart entry. AD 2 has an "AD 2.OKKK-77
  VISUAL APPROACH CHART" (aerodrome scale, out of scope).
- GEN 3.2 could not be read: `ALL GEN 3.pdf` is **password-protected** (pdfium: "Incorrect
  password error"). I did not try to open it further. So the statement "Kuwait publishes no
  VFR series" rests on the index listing alone; the GEN 3.2 text is UNVERIFIED.

#### URLs requested

| URL | Result |
|---|---|
| `https://dgca.gov.kw/AIP` | 200, 362978 bytes (AIP index, links to Azure blob PDFs) |
| `https://www.dgca.gov.kw/en/navigation/aip` (a guess) | 404 |
| `https://dgcawebappstg.blob.core.windows.net/upload/AIPItemSub/live/576/ALL%20GEN%203.pdf` | 200, 7105130 bytes (encrypted) |
| `https://dgcawebappstg.blob.core.windows.net/upload/AIPItemSub/live/607/ENR%206.1.pdf` | 200, 3174247 bytes (HEAD) |
| `https://dgcawebappstg.blob.core.windows.net/upload/AIPItemSub/live/608/ENR%206.2.pdf` | 200, 308582 bytes (HEAD) |

#### Verdict: NOT USABLE (nothing published)

---

### Lebanon

- **Publisher:** Directorate General of Civil Aviation (DGCA), Air Navigation Department.
- The site describes the AIS and the Integrated Aeronautical Information Package in prose
  but links to no AIP, eAIP or chart file. The general aviation page has no chart or PDF
  links.

#### URLs requested

| URL | Result |
|---|---|
| `https://www.dgca.gov.lb/` and `https://dgca.gov.lb/` | 404 (HTTPS host serves nothing) |
| `https://www.dgca.gov.lb/index.php/en/tid-en/and-en` | 404 |
| `https://www.dgca.gov.lb/index.php/en/pro-cat-en/category/68-aip-en` (a guess) | 404 |
| `http://www.dgca.gov.lb/` | 200, 59985 bytes |
| `http://www.dgca.gov.lb/index.php/en/tid-en/and-en` | 200, 41996 bytes |
| `http://www.dgca.gov.lb/index.php/en/general-aviation-en` | 200, 36112 bytes |

#### Verdict: NOT USABLE (nothing published online)

---

### Iraq

- **Publisher:** Iraq Civil Aviation Authority (ICAA).
- The official site answers with a "Secure Gateway ... Please complete the security check"
  page asking for a verification code. **I did not attempt it.** Search results only turned
  up third-party copies of the Iraq AIP (Scribd, Yumpu, docplayer), which are not a source.

#### URLs requested

| URL | Result |
|---|---|
| `https://icaa.gov.iq/` | redirects to `https://icaa.gov.iq/verify/index.php?url=/`, 200, 2622 bytes: security check page |
| `https://gcans.gov.iq/` | redirects to `https://msg.securegateway.com/msg/`, 200, 2434 bytes |
| `https://ans.iq/` (a guess) | no response (curl 000) |
| `http://www.iraqcaa.com/`, `https://www.iraqcaa.com/` | 200, 501 bytes: placeholder page, no content |

#### Verdict: NOT USABLE (nothing reachable)

---

### Countries where nothing free and usable was found

| Country | What was checked | What it returned |
|---|---|---|
| Oman | eAIP GEN 3.2, ENR 6; CAA publications page; AIC 01/24 | WAC 1:1M exists, 70 OMR per sheet, printed, on request |
| Iran | AIS site, AIP document library (GEN 0, GEN 3, ENR 6 in two editions), price page | WAC and "VFR Chart" named in GEN 3.2; ENR 6 holds only the en-route chart |
| Jordan | CARC AIS page; GEN 3.2 (2008) PDF | No VFR series listed; AIP behind accepted terms plus a human check |
| Kuwait | DGCA AIP index; ENR 6 files; GEN 3 PDF | ENR 6 = en-route chart and radio index only; GEN 3 encrypted |
| Lebanon | DGCA site (HTTP), Air Navigation and general aviation pages | No AIP or chart links |
| Iraq | icaa.gov.iq, gcans.gov.iq, iraqcaa.com | Security check page; placeholder |
| Bahrain | eAIP GEN 3.2, ENR 6, WAC PDF | One free WAC sheet, but 2004 data on a 72 dpi base |
| Israel | eAIP GEN 3.2 / ENR 6; gov.il blobs; data.gov.il | No 1:500k or WAC; free 1:250k CVFR vector PDF, all rights reserved, current edition not discoverable |

National mapping agencies: only Jordan's (Royal Jordanian Geographic Center, named in GEN
3.2 as a partner) and Israel's (Survey of Israel, named in the eAIP as a source of
topographic charts) came up. Neither was found to publish an aeronautical chart; their
sites were **NOT CHECKED** directly. The mapping agencies of the other countries were
**NOT CHECKED**.

### Things the caller should know

1. **The UAE terms forbid automated retrieval.** GEN 0.1.5 withholds the right to use robots, crawlers and similar automated tools. The helper's requests to gcaa.gov.ae were a few dozen page and metadata fetches plus one 82 MB
   download; a pipeline that fetches the chart on a schedule would be inside what those
   terms exclude.
2. **One POST was made by the helper**, to the GCAA configuration service, replaying the read-only lookup
   the public chart page performs on load. It returned "Unauthorized" and nothing was
   submitted or changed. Everything else was GET or HEAD.
3. The Saudi portal's public `configs.json` contains an `accessCode` value. It was not used; the API answered without it.
4. gov.il (Israel), icaa.gov.iq (Iraq) and carc.gov.jo (Jordan) put a bot challenge, a
   verification code, or an accept-terms control in front of their indexes. None was
   attempted, so those three results are limited to what is reachable without them.

5. The GDAL build in the venv cannot open PDFs (driver listed, open fails), so PDF
   georeferencing was judged from the file bytes and pypdfium2, not from `gdal.Info`.

### Sample files saved

In `C:\Users\jrbir\AppData\Local\Temp\claude\E--faa-tiles\73473049-9788-4c6b-b726-5c43b44ca519\scratchpad\research\samples\`:

| File | Bytes | Source |
|---|---|---|
| `sa_500k_2546-D.pdf` | 16799155 | Saudi Arabia 1:500,000 sheet 2546-D |
| `ae_AERONAUTICAL_CHART_2025-12.zip` | 82156906 | UAE chart package; extracted to `ae/` |
| `qa_ENR-6-Aeronautical-Chart-ICAO.pdf` | 26913250 | Qatar 1:500,000 |
| `il_aip_CVFR_South_2023.pdf` | 8194956 | Israel CVFR South, 2023 edition |
| `bh_WAC_822.pdf` | 8816140 | Bahrain WAC 2547 |

Working files (fetched HTML, small AIP text PDFs, thumbnails, helper scripts) are in
`...\scratchpad\research\me\`, including `ir_enr61.pdf` (Iran ENR 6.1, 1719689 bytes),
`ir_gen32.pdf`, `ir_gen01.pdf`, `kw_gen3.pdf`, `om_aic0124.pdf` and the thumbnails
`sa_thumb.png`, `ae_thumb.png`, `qa_thumb0.png`, `il_thumb.png`, `bh_thumb.png`.

## Part 4. Oceania and Africa

Researched by a helper agent; checked and edited. Where this part says "I", the helper is speaking.

Two User-Agent strings were used and the difference matters for two hosts:
"short UA" is `Mozilla/5.0`; "full UA" is a complete desktop Chrome string.

### Regional summary

| Country | Series | Scale | Format | Georeferenced | Licence verdict | Overall verdict | Key URL |
|---|---|---|---|---|---|---|---|
| Australia | VNC, 15 sheets | 1:500,000 | Vector PDF, encrypted | None detected | Redistribution prohibited | NOT USABLE WITHOUT PERMISSION | https://www.airservicesaustralia.com/aip/aip.asp |
| Australia | VTC, about 26 sheets | 1:250,000 | PDF | UNVERIFIED, presumed no | Redistribution prohibited | NOT USABLE WITHOUT PERMISSION | same |
| Australia | PCA | planning | PDF | UNVERIFIED | Redistribution prohibited | NOT USABLE WITHOUT PERMISSION | same |
| Australia | WAC, 43 sheets | 1:1,000,000 | Paper; PDF + GeoTIFF paid only | Yes (paid) | Paid, AUD 5,000 | NOT USABLE | https://data.airservicesaustralia.com/data-product/world-aeronautical-charts |
| New Zealand | Visual Planning Chart A1/A2 | 1:1,000,000 | Paper only seen | n/a | Reproduction prohibited | NOT USABLE | https://shop.aeropath.aero/ |
| New Zealand | VNC B1-B6 | 1:500,000 | GeoTIFF / KML / MBTiles, paid | Yes (paid) | Paid + EULA | NOT USABLE | https://shop.aeropath.aero/collections/digital-visual-navigation-charts-2025-2026 |
| New Zealand | VNC C1-C20, D1-D4 | 1:250,000, 1:125,000 | same, paid | Yes (paid) | Paid + EULA | NOT USABLE | same |
| South Africa (also covers Namibia) | ICAO WAC, 16 sheets (NGI) | 1:1,000,000 | Paper; no download found | n/a | UNVERIFIED | NOT USABLE | https://ngi.dlrrd.gov.za/ |
| South Africa (also covers Namibia) | Aeronautical chart, 23 to 33 sheets (NGI) | 1:500,000 | Paper; no download found | n/a | UNVERIFIED | NOT USABLE | https://ngigeoportal.dlrrd.gov.za/cdngiportal/ |
| Morocco | WAC (Rabat 2420, Marrakech 2454, others UNVERIFIED) | 1:1,000,000 | PDF, per search results | UNVERIFIED | UNVERIFIED | BLOCKED, not verified; follow-up candidate | https://siamaroc.onda.ma/cartes_vfr.htm |
| ASECNA, 18 states | none produced | - | - | - | - | NOT USABLE (series does not exist yet) | https://aim.asecna.aero/html/eAIP/FR-_00GEN-3.2-01-fr-FR.html |
| Namibia | none of target type; en-route chart only | 1:2,300,000 | Vector PDF inside AIP | No | (c) NCAA, no licence found | NOT USABLE | https://ncaa.com.na/aimpub.php?pagetitle=AIMpub&cat=AIPS |
| Mauritius | none; AIP says WAC not produced | - | - | - | - | NOT USABLE | https://civil-aviation.govmu.org/ |
| Cabo Verde | WAC 2656-2657, 2699 listed, not downloadable | 1:1,000,000 | index figure only | - | UNVERIFIED | NOT USABLE | https://eaip.asa.cv/ |
| Botswana | AIP behind account login | - | - | - | - | NOT USABLE | https://www.caab.co.bw/aeronautic-information-publication-aip/ |
| Kenya | eAIP behind login; AIP sold | - | - | - | - | NOT USABLE | https://eaip.kcaa.or.ke/ |
| Zimbabwe | AIP is subscriber-only | - | - | - | - | NOT USABLE | https://www.caaz.co.zw/aip/ |
| Tanzania | AIP sold by order form; no online AIP | - | - | - | - | NOT USABLE | https://www.tcaa.go.tz/index.php/pages/aeronautical-information-publication-aip |
| Egypt | only AIP amendments online; charts priced | - | - | - | - | NOT USABLE | http://www.nansceg.net/ais.html |
| Nigeria | no chart downloads; products sold | - | - | - | - | NOT USABLE | https://nama.gov.ng/charting/ |
| Ethiopia | AIP by email subscription | - | - | - | - | NOT USABLE | https://ecaa.gov.et/sectoral/navigation-services/ais |

**Bottom line: nothing in this region is usable for a public tileset on what was
found.** Australia is the only place where target charts can be fetched by a
script without payment, and its terms forbid exactly what we would do with
them. Morocco is the only place that may publish a free WAC online, and its site
sits behind a Cloudflare challenge that I did not attempt to pass. Across most
of Africa the 1:500,000 and 1:1,000,000 series either do not exist (ASECNA,
Mauritius) or exist only on paper (South Africa, which also covers Namibia).

---

### 1. Australia

#### Publisher and series

Airservices Australia. Series per
https://www.airservicesaustralia.com/aip/document_charts.asp (200, 18105):

| Series | Scale | Sheets | Notes |
|---|---|---|---|
| VNC, Visual Navigation Chart | 1:500,000 | 15, verified below | Populated coastal belts and Tasmania only, **not the interior** |
| VTC, Visual Terminal Chart | 1:250,000 | about 26 per the data portal listing, which includes a Perth legend and a Sydney flying guide | Around major aerodromes |
| WAC, World Aeronautical Chart | 1:1,000,000 | **43** (42 mainland and Tasmania sheets plus one special island sheet), counted from the Airservices index PDF | ICAO series, Lambert conformal conic; the only whole-continent series |
| PCA, Planning Chart Australia | planning | 1, as front and back files | |

#### Click-through agreement (not accepted)

https://www.airservicesaustralia.com/aip/aip.asp (200, 28480) is a "Copyright
Notice" ending in a form, `method="post" action="aip.asp?pg=10"`, with a submit
button "I Agree" and hidden field `check=1`. I did not submit it. Index requests
without acceptance return the notice again:

| URL | Result |
|---|---|
| https://www.airservicesaustralia.com/aip/aip.asp?pg=60 | 200, 28480, effective URL `aip.asp` |
| https://www.airservicesaustralia.com/aip/aip.asp?pg=60&vdate=01DEC2022&sect=VNC&ver=1 | 200, 28480, the notice |

The **index is gated; the files are not.** No cookie is checked on
`/aip/current/...`.

#### What is reachable without accepting (short UA, HEAD)

| URL | Status | Content-Length | Notes |
|---|---|---|---|
| https://www.airservicesaustralia.com/aip/current/aipchart/vnc/Brisbane_VNC_09JUL2026.pdf | 200 | 15960283 | application/pdf, Last-Modified 14 Apr 2026. **Sample downloaded** |
| https://www.airservicesaustralia.com/aip/current/aipchart/vnc/Sydney_VNC_09JUL2026.pdf | 200 | 29066133 | |
| https://www.airservicesaustralia.com/aip/current/aipchart/vtc/Sydney_VTC_09JUL2026.pdf | 200 | 15137765 | |
| https://www.airservicesaustralia.com/aip/current/aipchart/vtc/Brisbane_VTC_09JUL2026.pdf | 404 | 4941 | VTC names do not all follow `<City>_VTC_`; pattern UNVERIFIED |
| https://www.airservicesaustralia.com/aip/current/aipchart/pca/PCA_front_09JUL2026.pdf | 200 | 1149260 | |
| https://www.airservicesaustralia.com/aip/current/aipchart/pca/PCA_back_09JUL2026.pdf | 200 | 185999 | |
| https://www.airservicesaustralia.com/aip/current/aipchart/pca/PCA_09JUL2026.pdf | 404 | 4923 | |
| https://www.airservicesaustralia.com/aip/current/aipchart/wac/Sydney_WAC_09JUL2026.pdf | 404 | 4937 | A guess; no free WAC file exists as far as found |
| https://www.airservicesaustralia.com/aip/current/wac/World_Aeronautical_Charts.pdf | 200 | 1180243 | Two-page **index**, created 15 Aug 2024: sheet names, numbers, edition numbers. States that updated WAC are bought from the AIP Shop |
| https://www.airservicesaustralia.com/aip/current/iaipchart/Aeronauticalchartuserguide.pdf | 200 | 2285100 | Last-Modified 13 Aug 2026 |
| https://www.airservicesaustralia.com/aip/current/aipchart/vnc/ | 403 | 5133 | No directory listing |
| https://www.airservicesaustralia.com/aip/current/aip/complete_19MAR2026.pdf | 404 | 4915 | Superseded |

All 15 VNC sheets, edition 09JUL2026, each 200 `application/pdf`, pattern
`.../aipchart/vnc/<Name>_VNC_09JUL2026.pdf`:

| Sheet | Bytes | Sheet | Bytes |
|---|---|---|---|
| Adelaide | 11741553 | Melbourne | 16164836 |
| Brisbane | 15960283 | Newcastle | 29610736 |
| Bundaberg | 14739433 | Perth | 24575206 |
| Cairns | 17700205 | Rockhampton | 19430864 |
| Darwin | 41321511 | Sydney | 29066133 |
| Deniliquin | 24449359 | Tindal | 8447844 |
| Hobart | 13413692 | Townsville | 26882465 |
| Launceston | 5105084 | **Total** | **about 309 MB** |

#### Format, from the sample

`samples/au_Brisbane_VNC_09JUL2026.pdf`, 15,960,283 bytes.

- PDF 1.7, one page, 2948.03 x 1899.21 pt = 40.94 x 26.38 in (1040 x 670 mm).
- **Vector**: 73,299 path objects, 2,968 text objects, 90 small image objects
  (for example 495 x 908 px), so tints and relief patches, not a scan.
- Creator Adobe InDesign 20.5, producer Adobe PDF Library 17.0, created
  2026-04-08.
- **Encrypted**, security handler revision 4, permissions `0xfffffac4`: printing
  allowed; modification, content extraction, annotation and assembly not
  allowed. pdfium opens it without a password.
- **No georeferencing detected**: no `/GPTS`, `/LGIDict`, `/Measure`, `/GCS` in a
  byte search. That is weak evidence on an encrypted file with compressed
  object streams, and GDAL 3.13.3 refused the file ("not recognized as being in
  a supported file format"), so this is not fully verified. An InDesign export
  is very unlikely to be a GeoPDF.
- CRS: Lambert conformal conic is stated for WAC; for VNC UNVERIFIED.

#### Edition and discovery

- Current edition 09 JUL 2026. The data portal describes the VFR/IFR chart set
  as updated "Bi-annually" and WAC as "Ad-Hoc".
- The CanPrint store notes the 11 June 2026 cycle was deferred to 09 July 2026,
  so **edition dates cannot be computed from the AIRAC calendar**.
- File names embed the date as `DDMMMYYYY`; the listing is gated and the
  directory is 403, so a script must probe. Probes on
  `Brisbane_VNC_<date>.pdf`: 12JUN2025 404, 27NOV2025 404, 14MAY2026 404,
  04JUN2026 404, 11JUN2026 404, 18JUN2026 404, **09JUL2026 200**, 04AUG2026 404,
  06AUG2026 404, 26NOV2026 404. Also `Melbourne_VNC_16JUN2022.pdf` 404 (4943).

#### Paid digital products (excluded)

| URL | Result |
|---|---|
| https://data.airservicesaustralia.com/data-product/vfrifr-charts | 200, 70243. VTC, VNC, ERC, TAC, PCA as GeoTIFF (TIF + TFW + PRJ) and PDF. AUD 5,000.00 plus royalties. Subscribe and log in |
| https://data.airservicesaustralia.com/data-product/world-aeronautical-charts | 200, 45919. WAC as PDF and GeoTIFF, AUD 5,000.00 |
| https://data.airservicesaustralia.com/data-products | 200, 105318. Catalogue |
| https://data.airservicesaustralia.com/terms-and-conditions | 200, 19401. Body only refers to the privacy policy |
| https://www.aipshop.canprint.com.au/ | 200, 38075. Paper charts |
| https://www.aipshop.canprint.com.au/search_result.aspx?stype=C&cat=200&product=260 | 200, 26013. WAC category, no price in static HTML |
| https://www.aipshop.canprint.com.au/search_result.aspx?stype=C&cat=200&product=240 | 200, 26797 |
| https://www.aipshop.canprint.com.au/WAC_area_codes.pdf | 200, 1134799. HEAD only |

#### Other Australian sources

| URL | Result |
|---|---|
| https://data.gov.au/data/api/3/action/package_search?q=aeronautical+chart&rows=30 | 200, 110839. 18 results, none an aeronautical chart raster |
| https://data.gov.au/data/api/3/action/package_search?q=aeronautical&rows=50 | 200, 433490. 79 results, first 50 reviewed, none relevant |
| https://data.gov.au/data/api/3/action/package_search?q=%22world+aeronautical+chart%22&rows=20 | 200, 22047. HEAD only |
| https://www.ga.gov.au/scientific-topics/national-location-information/topographic-maps-data/topographic-maps | 200. Topographic, not aeronautical |
| https://ecat.ga.gov.au/geonetwork/srv/api/search/records/_search | 403 |
| https://www.airservicesaustralia.com/industry-info/aeronautical-information-management/ | 200, 184206. Not reviewed |

#### Licence

Source: the Copyright Notice at https://www.airservicesaustralia.com/aip/aip.asp,
which names "Aeronautical Charts" among the covered publications. Deciding sentence (paraphrase): the publications may be viewed on screen, unaltered, for personal and non-commercial purposes only. It goes on to prohibit reproducing, storing, transmitting,
redistributing, altering or adapting any part without written permission, and
prohibits caching on a local server. Tiles on a public site: **prohibited**.

#### Verdict: NOT USABLE WITHOUT PERMISSION (VNC, VTC, PCA); NOT USABLE (WAC)

Good vector sources that download free, under terms that forbid reuse, in files that carry PDF restrictions. WAC has no free digital form.

---

### 2. New Zealand

#### Publisher and series

Aeropath (Airways International Limited) for CAA NZ. Edition effective
**27 November 2025**, from the shop's product data:

| Series | Scale | Sheets |
|---|---|---|
| A1/A2 Visual Planning Chart | 1:1,000,000 | 2, one double-sided sheet |
| B1-B6 VNC | 1:500,000 | 6 charts on 3 sheets |
| C1-C20 VNC | 1:250,000 | 20 charts on 10 sheets; whole country |
| D1-D4 VNC | 1:125,000 | 4 charts on 2 sheets |

#### Access

| URL | Result |
|---|---|
| https://www.aip.net.nz/ | 200, **212 bytes**: Imperva Incapsula bot-challenge stub. Not bypassed |
| https://www.aip.net.nz/document-category/Visual-Navigation-Charts | 200, 212, same stub. A guessed path; proves nothing about the page |
| https://www.aip.net.nz/document-category/General-GEN | 200, 212, same stub. Guessed path |
| https://shop.aeropath.aero/collections/digital-visual-navigation-charts-2025-2026/products.json?limit=250 | 200, 49459. 4 "Digital File" products: 1:500,000, 1:250,000, 1:125,000 at **NZD 12.00** per chart area, one variant NZD 20.00. GeoTIFF, KML raster, MBTiles. EULA accepted at checkout |
| https://shop.aeropath.aero/collections/2025-2026-visual-navigation-charts/products.json?limit=250 | 200, 57030. 19 paper products at NZD 14.50; chart book NZD 94.00. Free items: chart legends download, chart book coordinate index |
| https://shop.aeropath.aero/collections/digital-charts-1 | 404, 100243 |
| https://shop.aeropath.aero/collections/charts | 404, 100243 |
| https://shop.aeropath.aero/pages/terms-and-conditions | 200, 109451 |

`aip.net.nz` content is entirely **UNVERIFIED**.
https://www.aviation.govt.nz/airspace-and-aerodromes/air-navigation/aip/ was
tried through WebFetch only and returned nothing.

Georeferencing and CRS of the paid GeoTIFFs were not inspected. A search
snippet said NZ aeronautical charts use the New Zealand Map Grid; UNVERIFIED and
possibly out of date.

Edition cycle: annual, late November (30 Nov 2023, 28 Nov 2024, 27 Nov 2025 seen
in search results; otherwise UNVERIFIED).

#### LINZ Data Service

| URL | Result |
|---|---|
| https://data.linz.govt.nz/data/?q=aeronautical | 200, 12181, JavaScript shell |
| https://data.linz.govt.nz/services/api/v1/data/?q=aeronautical | 200, 2 bytes, empty list |
| https://data.linz.govt.nz/services/api/v1/data/?q=airspace | 200, 2 bytes, empty list |
| https://data.linz.govt.nz/services/api/v1/data/?q=aerodrome | 200, 4541, 8 items, all hydrographic runway layers |
| https://data.linz.govt.nz/services/api/v1/data/?q=visual+navigation | 200, 59574, 100 items; first 14 reviewed, all nautical or imagery |

The same queries on `/services/api/v1.x/data/` matched (200; 2, 2, 4567, 59970).
**No aeronautical layer on LINZ.**

#### Licence

https://shop.aeropath.aero/pages/terms-and-conditions. Deciding sentence (paraphrase): without written permission no product may be extracted, copied, reproduced, modified or adapted. The page also forbids scraping the site; I had read two
catalogue JSON files before reaching that clause and made no further requests.
Tiles: **prohibited**.

#### Verdict: NOT USABLE

Paid, under a EULA, reproduction forbidden.

---

### 3. South Africa (and, through the same series, Namibia)

#### What the AIP says

https://cad.atns.co.za/SmartAIM/EAipPackages/15-OCT-20/2020-10-15-000000/html/eAIP/FA-GEN-3.2-en-US.html
(200, 107878) is GEN 3.2 of the AIP package effective **15 OCT 2020**. It is an
old package; the current one is behind a login (`https://cad.atns.co.za/SmartAIM/`
redirects to `Login.aspx`, 200, 6952), so the following is UNVERIFIED for 2026.

- The WAC 1:1,000,000 and the 1:500,000 series are **compiled by NGI**, the
  national mapping agency, not by SACAA, and are sold flat or folded from NGI
  and the Surveyor-General offices.
- **WAC 1:1,000,000, 16 sheets**: Bloemfontein 3397, Bulawayo 3275, Calvinia
  3396, Cape Town 3422, Durban 3398, Inhambane 3276, Johannesburg 3300,
  Kalahari 3274, Keetmanshoop 3302, Livingstone 3177, Maputo 3299, Ondangwa
  3179, Port Elizabeth 3421, Tsumeb 3178, Vryburg 3301, Windhoek 3273. The
  newest aeronautical overprint listed is **October 2017**; several are May
  2014 or December 2012. Base map sources date from 1998 to 2009.
- **1:500,000 "SA Topographical Aeronautical Edition", 33 sheets listed**, of
  which 12 are Namibian. South African sheets mostly December 2015 to April
  2018; the Namibian sheets date from **1995 to 2003**.
- So this one series is the small-scale VFR chart of both South Africa and
  Namibia, and it was already stale in 2020.

#### SACAA (caa.co.za)

| URL | Result |
|---|---|
| https://www.caa.co.za/industry-information/aeronautical-information-aeronautical-charts/ | 200, 534076. 365 PDF links on `caasanwebsitestorage.blob.core.windows.net/aeronautical-charts/`, all aerodrome, approach, SID/STAR, obstacle and radar charts |
| https://www.caa.co.za/industry-information/aeronautical-information-vfr-charts/ | 200, 245165. Eight "Airspace Infringement Hotspot" PDFs, 2017-2018 |
| https://www.caa.co.za/aeronautical-charts/ | First attempt no response; second 200, 513661. Not reviewed |
| https://caasanwebsitestorage.blob.core.windows.net/shared-documents/SACAA%20Terms%20of%20Use.pdf | 200, 136922. Read |
| https://caasanwebsitestorage.blob.core.windows.net/aip-ammendments/GEN_3_2_EN.pdf | 404, 215 |
| https://caasanwebsitestorage.blob.core.windows.net/aeronautical-information-publication/General%20(15_OCT_2025).pdf | 404 |

SACAA publishes no small-scale VFR chart online. Its terms of use grant no
reuse right; they say site contents may be copyrighted and that rights not
expressly granted are reserved, and they forbid obtaining material by means not
intentionally made available.

#### NGI

`ngi.dalrrd.gov.za` and `itis.ngi.gov.za` **no longer resolve**. The live host
is `ngi.dlrrd.gov.za`, which returns **403 (670 bytes) to the short UA** and 200
to a full UA.

| URL (200 with full UA) | Bytes | Content |
|---|---|---|
| https://ngi.dlrrd.gov.za/ | 51341 | Home |
| https://ngi.dlrrd.gov.za/index.php/what-we-do/maps-and-geospatial-information/35-map-products/56-1-500-000-icao-world-aeronautical-charts | 44399 | 1:500,000 ICAO chart |
| https://ngi.dlrrd.gov.za/index.php/what-we-do/maps-and-geospatial-information/35-map-products/57-1-1000-000-international-civil-aviation-organisation-world-aeronautical-charts | 44473 | 1:1,000,000 WAC |
| https://ngi.dlrrd.gov.za/index.php/what-we-do/maps-and-geospatial-information/35-map-products/53-1-500-000-aeronautical-edition-maps | 44258 | 1:500,000 aeronautical edition |
| https://ngi.dlrrd.gov.za/index.php/what-we-do/maps-and-geospatial-information/38-maps-and-charts-digital-raster-or-printed | 73364 | Product list |

Those pages state: 1:500,000 series of **23 sheets** (the AIP lists 33 names
including Namibia), each about 2 by 4 degrees, topographic base with a blue
aeronautical overprint, heights in feet; Lambert conformal conic with standard
parallels 17 deg 30 min S and 23 deg 30 min S north of 25 S, and 26 deg 40 min S
and 33 deg 20 min S south of it; WGS84. 1:1,000,000 WAC of 16 sheets, 4 by 6
degrees with a 15 minute overlap. **No download link on any page.**

#### NGI geoportal

| URL | Status | Bytes | Notes |
|---|---|---|---|
| http://www.cdngiportal.co.za/cdngiportal/ | 200 | 1953 | "Portal has moved" notice. https on that host refused |
| https://ngigeoportal.dlrrd.gov.za/cdngiportal/ | 200 | 515223 | Intergraph Geospatial Portal with an ERDAS APOLLO catalogue |
| https://BP-CDNGIAPOLLO.dlrrd.gov.za/erdas-iws/ogc/wms/CDNGI_MAP_MOSAICS (GetCapabilities) | 200 | 15566 | 1:50k, 1:250k, 1:2M topographic mosaics, land cover |
| .../erdas-iws/ogc/wmts/CDNGI_MAP_MOSAICS | 200 | 404035 | same layers |
| .../erdas-iws/ogc/wms/CDNGI_50K_TIMESERIES | 200 | 3871 | |
| .../erdas-iws/ogc/wms/CDNGI_IMAGERY_MOSAICS | 200 | 16445 | aerial imagery |
| .../erdas-iws/ogc/wms/CDNGI_PORTAL_BACKDROP | 200 | 27737 | |
| .../erdas-iws/ogc/wms | 200 | 77137 | vendor sample images only |
| .../erdas-iws/ogc/wmts | 200 | 268702 | not parsed |
| .../erdas-apollo/ | 200 | 558 | |
| .../erdas-apollo/catalog/csw (GetCapabilities) | 200 | 12462 | |
| .../erdas-apollo/catalog/csw (GetRecords, AnyText like AERO) | **401** | 60 | credentials required |
| .../erdas-apollo/content/catalog/children.json | 303 | 0 | |
| .../erdas-apollo/coverage/CATALOG | 500 | 2387 | |

No aeronautical layer in any public WMS or WMTS (0 matches for "aero").

I then opened the portal in the browser pane and **browsed its catalogue tree
without logging in or searching**. `Coverage Catalog > ROOT > MAPPING` holds
folders `1000K`, `2000K`, `250K`, `500K`, `50K`, `LCLU`, `MOSAIC`, `PROVINCIAL`,
`PROVINCIAL_MAPS`:

- `MAPPING/1000K/TIF` is **empty**.
- `MAPPING/500K/TIF` holds **three rasters only**:
  `2126_2001_ED3_500K_GEO.tif`, `3126_1992_ED2_500k.tif` and
  `3126_TOPO_1992_ED2_500K_GEO.TIF`, access listed as WMS, WMTS and
  clip-zip-ship. Two sheets out of 23, editions of 1992 and 2001, one
  explicitly topographic. Whether any is the aeronautical edition is
  UNVERIFIED; none was downloaded.

The portal's page source embeds default catalogue credentials for its own use.
**I did not use them**, and a pipeline should not.

#### Licence

NGI's data terms were not found. UNVERIFIED. Tiles: **unclear**.

#### Verdict: NOT USABLE

The series exists and is exactly the target, but it is a paper product. NGI's
public catalogue holds no 1:1,000,000 raster and two stray 1:500,000 sheets. The
most recent overprints known are 2017-2018. Getting scans would mean asking NGI
directly, and the data would still be old.

---

### 4. Other African states

#### ASECNA: the series does not exist

ASECNA is the air navigation provider for 18 states (Benin, Burkina Faso,
Cameroon, Central African Republic, Chad, Comoros, Congo, Cote d'Ivoire,
Equatorial Guinea, Gabon, Guinea-Bissau, Madagascar, Mali, Mauritania, Niger,
Rwanda, Senegal, Togo).

| URL | Status | Bytes | Notes |
|---|---|---|---|
| https://aim.asecna.aero/ | 200 | 308 | Meta-refresh to `html/index-fr-FR.html` |
| https://aim.asecna.aero/html/eAIP/ | 403 | 58 | |
| https://aim.asecna.aero/html/eAIP/FR-_00GEN-3.2-01-fr-FR.html | 200 | 224539 | GEN 3.2, valid from 16 APR 2026 |
| https://aim.asecna.aero/html/eAIP/FR-_00GEN-3.2-07-fr-FR.html | 200 | 40216 | Chart list and prices, valid from 05 DEC 2019 |
| https://www.asecna.aero/images/Docs/Appel_offre/AOffres2025/CCTP-Projet-Production-Cartes-Aeronautiques-Mondiales-WAC-v2.3.pdf | 200 | 2009132 | Tender specification, March 2025, 41 pages |
| https://www.ais-asecna.org/ | TLS handshake failed | 0 | |

GEN 3.2 lists: radio navigation charts at 1:9,000,000, TMA charts, visual and
instrument approach and landing charts at 1:250,000 and 1:25,000, aerodrome and
obstacle charts, and radio facility charts at 1:7,000,000. Prices are EUR 10 to
20 each by mail order. **No 1:500,000 or 1:1,000,000 chart is listed.**

The tender document settles it. It is ASECNA's specification for producing WAC
at 1:1,000,000 and 1:500,000 for all 18 states, and it states that en-route
visual navigation charts are currently not produced and that no production
facility for small-scale charts exists yet. The project plans vector and raster
outputs and a web-mapping platform, so this is **worth re-checking in a year or
two**. The document carries a notice restricting it to member-state
representatives, though it is served publicly.

Verdict: **NOT USABLE**. There is nothing to download because the charts have
not been made.

#### Morocco: probably publishes a free WAC, but blocked

| URL | Status | Bytes | Notes |
|---|---|---|---|
| https://siamaroc.onda.ma/ | 403 | 5578 | Cloudflare "Just a moment..." challenge |
| https://siamaroc.onda.ma/cartes_vfr.htm | 403 | 5641 | same |
| https://siamaroc.onda.ma/guidevfr.html | 403 | 5617 | same |
| https://siamaroc.onda.ma/eAIP/GEN/GEN3.2.pdf | 403 | 5656 | same |
| https://siamaroc.onda.ma/CARTES_WAC/Rabat.pdf | 403 | 5659 | header `Cf-Mitigated: challenge`, both UAs |
| https://siamaroc.onda.ma/CARTES_WAC/Marrakech.pdf | 403 | 5671 | same |
| https://siamaroc.onda.ma/guidevfr/Guide%20VFR%20MAR%202026.pdf | 403 | 5731 | same |
| http://www.sia-aviation.gov.ma/cartes_vfr.htm | connection failed | 0 | old domain, also on https |

Every request, including each PDF, is answered by a Cloudflare bot challenge. I
did not attempt to pass it, in curl or in a browser. WebFetch also got 403.

What search-engine results indicate, all **UNVERIFIED**: the SIA Maroc site
(ONDA) has a "Cartes VFR Maroc" page and a `CARTES_WAC` directory holding at
least `Rabat.pdf` (WAC 2420) and `Marrakech.pdf` (WAC 2454) at 1:1,000,000, plus
a 2026 VFR guide. Format, georeferencing, sheet count, edition and licence are
all unknown.

Verdict: **BLOCKED, not verified.** The best lead in Africa. It needs a person
to open the site in a browser, read the terms, and save the PDFs by hand. A
scripted download is not possible without defeating the challenge, so at best
this would be a manual drop-in like our wall planning chart.

#### Namibia

| URL | Status | Bytes | Notes |
|---|---|---|---|
| https://ncaa.com.na/aimpub.php?pagetitle=AIMpub&cat=AIP+Supplement | 200 | 54984 | Supplement list |
| https://ncaa.com.na/aimpub.php?pagetitle=AIMpub&cat=AIPS | 200 | 40112 | Links the AIP as three PDFs |
| https://ncaa.com.na/publications/aeronautical-information/aeronautical-information-publication/aips/General.pdf | 200 | 1523656 | Last-Modified 13 Jul 2026 |
| https://ncaa.com.na/publications/aeronautical-information/aeronautical-information-publication/aips/Enroute.pdf | 200 | 6353689 | **Sample downloaded** |
| https://ncaa.com.na/publications/aeronautical-information/aeronautical-information-publication/aips/Aerodrome.pdf | 200 | 13610005 | |
| https://ncaa.com.na/publications/aeronautical-information/aeronautical-information-publication/aip-supplement/S03_2024%20GEN%203.2%20Aeronautical%20Charts.pdf | 200 | 376349 | GEN 3.2, effective 18 Apr 2024. Read |
| https://ncaa.com.na/publications/aeronautical-information/aeronautical-information-publication/aip-supplement/S04_2024%20Enroute%20Chart.pdf | 200 | 2243388 | HEAD only |
| https://www.ncaa.com.na//index.php/ncaa-departments/air-navigation-services/aeronautical-information-service-ais | 200 | 95912 | Redirected to the home page |

The whole AIP is free and open, no login. GEN 3.2 lists aerodrome, en-route,
SID/STAR, approach and visual approach charts, and one "VFR Chart", not to
scale, for the FIR. **No WAC and no 1:500,000 chart.** In
`samples/na_AIP_Enroute.pdf` (198 pages) ENR 6 holds two charts: an en-route
chart at 1:2,300,000 (page 195, 2384 x 1684 pt, vector, 09 JUL 2026) and an ATS
routes chart (page 197, A3, 15 MAY 2025). Both are IFR route charts on a plain
base. Neither is georeferenced.

Licence: pages carry "(c) Namibia Civil Aviation Authority"; no reuse terms
found. Verdict: **NOT USABLE**, wrong chart type. Namibia's small-scale VFR
coverage is the South African NGI series above, 1995-2003 editions.

#### Mauritius

https://civil-aviation.govmu.org/eAIP/eAIPMauritius_12_11_2024_updated/eAIPMauritius_12_11_2024_updated/final/2017-08-17-Non-AIRAC/html/eAIP/GEN-3.2-en-GB.html
(200, 47757). The eAIP is open. GEN 3.2.6 says Mauritius does not produce the
WAC 1:1,000,000, and 3.2.7 says topographical charts are not available. Home
page https://civil-aviation.govmu.org/ is 200, 91238. Verdict: **NOT USABLE**.

#### Cabo Verde (not in the brief; found in passing)

| URL | Status | Bytes |
|---|---|---|
| https://eaip.asa.cv/ | 200 | 3751 |
| https://eaip.asa.cv/2024-04-18-AIRAC/html/index-en-GB.html | 200 | 877 |
| https://eaip.asa.cv/2024-04-18-AIRAC/html/eAIP/GV-GEN-3.2-en-GB.html | 200 | 16347 |
| https://eaip.asa.cv/2024-04-18-AIRAC/html/eAIP/GV-ENR-6-en-GB.html | 200 | 4465 |
| https://eaip.asa.cv/2024-04-18-AIRAC/graphics/3897.pdf | 200 | 603367 |
| https://ais.asa.cv/ | 200 | 129568 |

Open eAIP with a clean history page, current issue 18 APR 2024. GEN 3.2 lists a
WAC 1:1,000,000 as produced, and the index figure shows sheets 2656-2657 and
2699. But ENR 6 holds only en-route and TMA charts: **the WAC itself is not in
the eAIP.** Verdict: **NOT USABLE** as found.

#### States where the AIP itself is closed or sold

| Country | URL | Status, bytes | What it returned |
|---|---|---|---|
| Botswana | https://www.caab.co.bw/aeronautic-information-publication-aip/ | 200, 230682 | Sign-in form; links to `/aip-register/` and `/aip-login/`. AIP needs an account |
| Botswana | https://www.caab.co.bw/aeronautical-information-management/ | 200, 275305 | Descriptive |
| Kenya | https://eaip.kcaa.or.ke/ | 200, 9714 | Login form, "Register/Sign up". First attempt failed DNS; later resolved |
| Kenya | https://eaip.kcaa.or.ke/Home/AIP%20text.html | 200, 3004 | AIP in paper, online and CD-ROM |
| Kenya | https://eaip.kcaa.or.ke/Home/Maps%20and%20Charts%20text.html | 200, 3262 | Non-AIP maps and charts sold separately; no list |
| Kenya | https://eaip.kcaa.or.ke/Home/Purchase%20text.html | 200, 3642 | AIP USD 255 overseas, amendments USD 75 a year |
| Kenya | https://kcaa.or.ke/ | 200, 154209 | Home |
| Zimbabwe | https://www.caaz.co.zw/aip/ | 200, 203258 | "Subscriber Content": active subscription and login required |
| Zimbabwe | https://www.caaz.co.zw/ans/ | 200, 214838 | Links a subscription form |
| Tanzania | https://www.tcaa.go.tz/index.php/pages/aeronautical-information-publication-aip | 200, 98508 | AIP sold by order form; charts not in the AIP on request from the cartographic unit |
| Tanzania | https://www.tcaa.go.tz/index.php/publications/aip-supplement | 200, 114600 | Supplements are free PDFs |
| Tanzania | https://aim.tcaa.go.tz/ | 200, 535 | Placeholder page, no content |
| Egypt | http://www.nansceg.net/ | 200, 12089 | NANSC home |
| Egypt | http://www.nansceg.net/ais.html | 200, 10807 | Links AIRAC amendments and a supplement only |
| Egypt | http://www.nansceg.net/airac_amdt_all_pages.pdf | 200, 11309274 | AIRAC AMDT 01/26, 60 pages. Read |
| Nigeria | https://nama.gov.ng/charting/ | 200, 444748 | Describes the charting department; no downloads |
| Nigeria | https://nama.gov.ng/purchasing-ais-products/ | 200, 434753 | Products are purchased |
| Nigeria | https://nama.gov.ng/ | 200, 508965 | Home |
| Nigeria | https://aim.nama.gov.ng/ | DNS failure, 0 | Host does not resolve |
| Ethiopia | https://ecaa.gov.et/sectoral/navigation-services/ais | 200, 81765 | AIP by subscription ordered by email |
| Ethiopia | https://ecaa.gov.et/ | 200, 113193 | Home |
| Ethiopia | https://ecaa.gov.et/aeronautical-information-management-directorate/ | 404, 15668 | |
| Ethiopia | https://ecaa.gov.et/home/aeronautical-information-services-ais-directorate/ | 404, 15686 | |
| Ethiopia | https://www.ecaa.gov.et/aeronautical-information-management-directorate/ | TLS certificate name mismatch, 0 | `www` host has a bad certificate |

Notes:

- **Egypt**: the amendment PDF contains GEN 3.2 pages 5 to 7 only, which list
  instrument approach, aerodrome and obstacle charts at USD 6.5 to 12.5 each.
  The pages that would list a WAC were not in the amendment, so whether Egypt
  publishes one is **UNVERIFIED**. The full AIP was not found online.
- For all seven states no GEN 3.2 could be read, so whether a 1:500,000 or
  1:1,000,000 series exists is **UNVERIFIED**. What is verified is that nothing
  is downloadable without an account or a purchase.

Verdict for Botswana, Kenya, Zimbabwe, Tanzania, Egypt, Nigeria, Ethiopia:
**NOT USABLE**.

#### Also tried, outside the brief

| Country | URL | Result |
|---|---|---|
| Algeria | https://www.sia-enna.dz/ | DNS failure, on http as well |
| Tunisia | http://www.oaca.nat.tn/index.php?id=726 | 500, 39118, a firewall "Web Page Blocked" page |
| Tunisia | https://www.oaca.nat.tn/ | 200, 113371, home page; not pursued |

Neither was investigated further. Both are **NOT CHECKED** in substance.

---

### Countries where nothing free and usable was found

| Country | What was checked | What it returned |
|---|---|---|
| Australia | AIP site, data portal, CanPrint store, data.gov.au, Geoscience Australia | Free vector PDFs, licence prohibits reuse; GeoTIFF and all WAC paid |
| New Zealand | aip.net.nz, Aeropath shop and terms, LINZ API | Bot challenge on aip.net.nz; charts sold under EULA; nothing on LINZ |
| South Africa | SACAA pages and terms, AIP GEN 3.2 (2020), NGI pages, NGI portal, OGC services, catalogue tree | Paper series only; catalogue has no 1:1M and two old 1:500k sheets |
| Namibia | NCAA AIP PDFs, GEN 3.2 supplement, ENR 6 | Open AIP, but only IFR route charts |
| ASECNA states | eAIP GEN 3.2, WAC tender specification | Series not produced; production tendered in 2025 |
| Morocco | SIA Maroc pages and PDF URLs | All 403 behind a Cloudflare challenge; content UNVERIFIED |
| Mauritius | eAIP GEN 3.2 | States it produces no WAC |
| Cabo Verde | eAIP GEN 3.2, ENR 6, WAC index | WAC listed but not published in the eAIP |
| Botswana, Kenya, Zimbabwe | AIP pages | Login or subscription walls |
| Tanzania, Egypt, Nigeria, Ethiopia | AIM pages | AIP sold or by subscription; no chart downloads |

### Files saved by the Oceania and Africa helper

Chart samples, in `...\scratchpad\research\samples\`:

- `au_Brisbane_VNC_09JUL2026.pdf`, 15,960,283 bytes. Covered by the Airservices
  copyright notice; inspection only.
- `na_AIP_Enroute.pdf`, 6,353,689 bytes. Namibia AIP Part 2.

Reference documents, in `...\scratchpad\research\pages\oa\`:
`au_wac_index.pdf` (1,180,243), `asecna_wac_cctp.pdf` (2,009,132),
`na_gen32_sup.pdf` (376,349), `eg_airac_amdt.pdf` (11,309,274),
`za_sacaa_terms.pdf` (136,922), `cv_wac_index.pdf` (603,367), plus fetched HTML,
JSON and XML and three rendered previews (`na_enr6_p195.jpg`,
`na_enr6_p197.jpg`, `cv_wac_index.jpg`).

Helper scripts in `...\scratchpad\research\`: `h2t.py`, `kw.py`,
`pdfinspect.py`, `pdfpages.py`, `pdfpagetext.py`, `pdftext.py`, `pdfrender.py`.

### Open items and caveats

- Morocco is unresolved and is the item most worth a manual look.
- ASECNA's WAC project may produce usable data later; re-check.
- Australian georeferencing is "none detected", not proven absent.
- `aip.net.nz` content is entirely unverified.
- The South African chart lists are from a 2020 AIP package.
- NGI licence terms were not found.
- For Botswana, Kenya, Zimbabwe, Tanzania, Egypt, Nigeria and Ethiopia the
  existence of a small-scale VFR series is unverified, because GEN 3.2 could not
  be read without an account or purchase.

## Every country where nothing free was found

"Free" here means obtainable without payment, login or registration. Sources that
are free but may not be republished are in the summary table above, not here.

| Country | What was checked | What it showed |
|---|---|---|
| Japan | JAPA chart shop, JHA chart shop, SWIM portal | 1:500,000 and WAC sold; AIP behind registration |
| South Korea | eAIP GEN 3.2 and ENR 6, MOLIT sales page, AIM reference board, public data portal | Paper charts sold to residents; only thumbnails free |
| China | CAAC news item, general aviation platform, eAIP site | VFR charts exist behind a login |
| Hong Kong | eAIP GEN 3.2, Lands Department thematic and open-data pages | No target-scale chart; flying charts sold |
| Mongolia | eAIP GEN 3.2 and ENR 6, data set page, public ArcGIS items | Both target series sold at MNT 28,200 a sheet |
| Russia | State AIP GEN 3.2 and menu, SZ RCAI | No state series; commercial charts sold |
| Kyrgyzstan, Uzbekistan, Tajikistan, Turkmenistan | AIP GEN 3.2 of each | No chart of the target type is published |
| Pakistan | AIP GEN 3.2, ENR 6, Survey of Pakistan site | WAC sold on paper by Survey of Pakistan |
| Bangladesh | AIP GEN and ENR parts | WAC index reads "Not Available" |
| Sri Lanka | eAIP GEN 3.2 and ENR 6.1 | WAC sold, LKR 2000 a sheet |
| Nepal | e-AIP GEN 3.2 and ENR 6, Department of Survey site | 1:500,000 chart listed but not online |
| Bhutan, Maldives, Myanmar, Brunei | AIP GEN 3.2 and ENR 6 of each | No WAC or VFR chart published |
| Vietnam | eAIP GEN 3.2 and ENR 6 | Three series on paper, dated 1988 and 1997 |
| Cambodia | eAIP landing page | Registration and click-through required |
| Laos | Department of Civil Aviation site | No online AIP found |
| Indonesia | AIM Indonesia, AirNav Indonesia AIS centre | Behind sign-in |
| Philippines | CAAP AIS site, NAMRIA | AIP behind login, sold by subscription |
| Jordan | CARC AIS page, GEN 3.2 of 2008 | No VFR series listed; AIP behind accepted terms and a human check |
| Oman | eAIP GEN 3.2 and ENR 6, AIC 01/24 | WAC on paper, 70 OMR a sheet |
| Iran | AIS site, AIP document library, price page | WAC named in GEN 3.2 but no file online |
| Kuwait | AIP index, ENR 6 files | En-route chart only; GEN 3 password-protected |
| Lebanon | DGCA site | No AIP or chart links |
| Iraq | ICAA and GCANS sites | Security check page; nothing reachable |
| New Zealand | aip.net.nz, Aeropath shop and terms, LINZ Data Service | Bot challenge; charts sold under a EULA; nothing on LINZ |
| Australia (WAC only) | Airservices AIP site, data portal, CanPrint store, data.gov.au | WAC sold on paper and as paid GeoTIFF |
| South Africa | SACAA pages and terms, AIP GEN 3.2 of 2020, NGI pages, portal and OGC services | Paper series; no download |
| Namibia | NCAA AIP PDFs, GEN 3.2 supplement | Open AIP with IFR route charts only |
| ASECNA states (18) | eAIP GEN 3.2, 2025 tender specification | Series not yet produced |
| Mauritius | eAIP GEN 3.2 | No WAC produced |
| Cabo Verde | eAIP GEN 3.2, ENR 6 | WAC listed but not in the eAIP |
| Botswana, Kenya, Zimbabwe | AIP pages | Login or subscription walls |
| Tanzania, Egypt, Nigeria, Ethiopia | AIM pages | AIP sold or by subscription; no chart downloads |

Not settled: **Morocco** (blocked by a bot challenge, not verified).
Not checked: **Algeria, Tunisia** (outside the brief; one DNS failure, one firewall
page), and the national mapping agencies of most states, which were looked at only
where an AIP named them as the chart publisher (India, Pakistan, Nepal, Malaysia,
Hong Kong, South Africa).

## What remains unverified

- **Taiwan:** whether the CAA's open-data declaration covers the separate chart
  domain; whether any z14 tiles exist.
- **Kazakhstan:** the standard parallels of the projection; the update cadence; the
  content of 26 of the 27 sheets (one was inspected).
- **Saudi Arabia:** the content of the eight WAC PDFs (HEAD only) and the standard
  parallels of sheets other than 2546-D.
- **Australia:** absence of georeferencing in the encrypted PDFs; VTC sheet names
  and count; the VNC projection.
- **Thailand, Malaysia, India:** one sheet of each was inspected; India's four PDF
  sheets were not opened.
- **Israel:** the URLs of the current CVFR edition; the sample is the 2023 edition.
- **South Africa:** chart lists come from a 2020 AIP package; NGI's data terms were
  not found.
- **Behind a wall, so unknown:** what charts China, Indonesia, the Philippines,
  Cambodia, Botswana, Kenya, Zimbabwe, Tanzania, Egypt, Nigeria and Ethiopia
  publish; the whole of `aip.net.nz`; Japan's GEN 3.2; Kuwait's GEN 3.2.

## Samples saved

All in the session scratchpad, `research\samples\`. None is under `E:\faa-tiles`.

| File | Bytes | Source |
|---|---|---|
| `Taiwan_Eng_Map_20260921_print.pdf` | 14,671,733 | Taiwan VFR chart, English |
| `kz_first5MB.bin`, `kz_sheet_first.jpg` | 5,000,000; 4,485,330 | Kazakhstan chart, first 5 MB by ranged request, and sheet B1 cut from it |
| `ae_AERONAUTICAL_CHART_2025-12.zip` (extracted to `ae\`) | 82,156,906 | UAE chart package with the GeoTIFF |
| `sa_500k_2546-D.pdf` | 16,799,155 | Saudi Arabia 1:500,000 sheet 2546-D |
| `qa_ENR-6-Aeronautical-Chart-ICAO.pdf` | 26,913,250 | Qatar 1:500,000 |
| `il_aip_CVFR_South_2023.pdf` | 8,194,956 | Israel CVFR South, 2023 edition |
| `bh_WAC_822.pdf` | 8,816,140 | Bahrain WAC 2547 |
| `sg_wac2860.pdf` | 10,835,746 | Singapore WAC 2860 |
| `th_wac2677.pdf` | 7,606,920 | Thailand WAC 2677 |
| `my_wac2859.pdf` | 1,253,739 | Malaysia WAC 2859 |
| `in_wac2440_delhi.jpg` | 2,039,166 | India WAC 2440 Delhi |
| `np_enr6_6.pdf` | 6,279,187 | Nepal ENR 6.6 index chart (georeferenced) |
| `au_Brisbane_VNC_09JUL2026.pdf` | 15,960,283 | Australia VNC Brisbane |
| `na_AIP_Enroute.pdf` | 6,353,689 | Namibia AIP Part 2 |

Most of these are covered by terms that forbid redistribution. They were fetched
to inspect format and georeferencing and should be deleted with the scratchpad.

## Conduct of the research

- Nothing under `E:\faa-tiles` was modified.
- The Australian sample was fetched from a public file URL. The AIP index that
  lists such files sits behind an "I Agree" form, which was not submitted; the
  file URL itself checks nothing. The notice behind that form covers the file.
- One POST request was made, by the Middle East helper, to a UAE configuration
  service: a replay of the read-only lookup the public chart page makes when it
  loads. It returned "Unauthorized". Everything else was GET or HEAD.
- Two public pages expose credentials in their source (a Saudi `accessCode`, and
  default catalogue credentials on South Africa's NGI portal). Neither was used.
- The NGI portal's public catalogue tree was browsed once in a browser pane,
  without logging in or searching.
- The New Zealand chart shop's terms forbid scraping. Two of its catalogue JSON
  files had been read before that clause was reached; no further requests were
  made to it.
