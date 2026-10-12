# World-wide VFR charts: what is free, and what is built from it

Researched 2026-09-27 for `tileset-worldwide-vfr`. The rule was the user's: only
charts that can be had **without payment**. The regional reports this summarises
are in [worldwide-vfr-research/](worldwide-vfr-research/); they were written by
research agents, record every URL with the status it returned on the day, and
have not been reviewed line by line. Where this page and a report disagree, the
report is the record of what was seen.

Two things that are easy to confuse:

- **Free to download** is what the rule asks for, and what decides whether a
  source is in the pipeline.
- **Free to republish** is a different question, answered by each publisher's
  terms. It decides whether a layer may go on a public site. Each series records
  its answer as its `licence` in `scripts/chart_series.py`, and
  `--redistributable-only` builds a tileset of just the layers that may.

Unclear terms are not permission. A layer is marked redistributable only where
the terms were read and say so.

## In the pipeline

Bottom layer first, which is the order they are painted in.

| Layer | Publisher | Coverage | Scale | Source form | Republish? |
| --- | --- | --- | --- | --- | --- |
| `onc` | US Defense Mapping Agency, scans at the University of Texas | World, 270 sheets | 1:1,000,000 | JPEG scans, unregistered | Yes, as US government works |
| `tpc` | the same | Most land, 650 sheets | 1:500,000 | JPEG scans, unregistered | Yes, except about 98 Crown copyright sheets |
| `br-wac` | DECEA, Brazil | Brazil, 46 sheets | 1:1,000,000 | GeoTIFF | Unclear; not marked |
| `faa-caribbean` | FAA | Bahamas to the Virgin Islands | 1:1,000,000 | GeoTIFF | Yes |
| `ofm` | open flightmaps association | 18 European regions | 1:500,000 | Web Mercator tiles | Yes, with attribution |
| `es-vfr500` | ENAIRE | Spain, 8 sheets | 1:500,000 | GeoTIFF | No |
| `dk-icao` | Naviair | Denmark | 1:500,000 | GeoTIFF | No terms stated; not marked |
| `ch-icao` | swisstopo | Switzerland, Liechtenstein | 1:500,000 | GeoTIFF | Yes, with attribution |
| `dk-250` | Naviair | Copenhagen area, Faroe Islands | 1:250,000 | GeoTIFF | No terms stated; not marked |
| `sectionals` | FAA | United States | 1:500,000 | GeoTIFF | Yes |
| `tac` | FAA | 34 US terminal areas | 1:250,000 | GeoTIFF | Yes |

### The historical layers

`onc` and `tpc` are the US military's Operational Navigation Charts and Tactical
Pilotage Charts, compiled between 1961 and 2004 and mostly in the 1970s to
1990s. They are in the tileset because the user asked for a gap filler: most of
the planet has no current chart that is free, and these cover it. **They are
decades out of date and are never to be navigated by.** `metadata.json` marks
both layers `historical`.

Three things about them that cost time to find out:

- **They are scans, and the scans are not rigid.** See `scripts/graticule.py`.
- **The published sheet indexes cannot be relied on.** Memorial University's
  index gives TPC E-2A as beginning at 1° 52' W; the sheet begins at 1° W. New
  York University's gives ONC J-24 a southern limit of 15° 40' for a corner of
  the sheet that dips below its neatline at 16°. So each sheet's corner labels
  are read off the scan, and the reading is what `scripts/*_sheets.json`
  records.
- **Not all of them are US government works.** Some TPC sheets were produced by
  the UK's Military Survey or by Australia and carry Crown copyright notices.
  The University of Texas lists TPC E-2A as a US chart; the sheet itself says
  otherwise. The sheet index marks these `crown`.

## Free to download, not yet in the pipeline

These are real sources that the pipeline does not yet read. Most need one of two
things it cannot yet do: read the georeferencing embedded in a PDF, or register
a sheet that has none.

| Country | Chart | Form | What it needs | Republish? |
| --- | --- | --- | --- | --- |
| Latvia | VFR Aeronautical Chart ICAO 1:500,000 | Vector PDF, georeferenced | PDF georeferencing | Unclear |
| Estonia | Aeronautical Chart ICAO 1:500,000 | Vector PDF, georeferenced | PDF georeferencing | No |
| Romania | VFR Chart ICAO 1:500,000, 4 sheets | Vector PDF, georeferenced | PDF georeferencing | No |
| Taiwan | VFR Chart 1:500,000 | Vector PDF, georeferenced; also tiles | PDF georeferencing | Appears permitted |
| Slovakia | VFR Manual web chart | Public tile cache, z7 to z14 | A tile-cache fetcher | Overlay yes; base map unclear |
| Austria | Luftfahrtkarte ICAO 1:500,000 | Raster PDF | Registration | Non-commercial use only |
| Czech Republic | Aeronautical Chart ICAO 1:500,000 | Raster PDF | Registration | No |
| Netherlands | Aeronautical Chart ICAO 1:500,000 | Raster PDF | Registration | No |
| Slovenia | VFR chart 1:250,000 | PDF | Registration | No |
| Albania | Aeronautical Chart ICAO 1:500,000 | Raster PDF; embedded georeferencing is wrong | Registration | No |
| Bosnia and Herzegovina | VFR Chart 1:500,000 | Mostly vector PDF | Registration | No |
| Kazakhstan | Aeronautical Chart 1:500,000, 27 sheets | PDF of JPEG pages | Registration | None stated |
| Argentina | VFR below TMA Buenos Aires and Cordoba | Georeferenced PDF | PDF georeferencing | None stated |
| Brazil | CNAV 1:500,000, 91 sheets, patchy | Georeferenced vector PDF | PDF georeferencing | Unclear |
| Mexico | WAC 1:1,000,000, 2016 | JPEG, about 245 m a pixel | Registration | Not for profit |
| Singapore | WAC 1:1,000,000, one sheet | Vector PDF | Registration | No |

The Danish, Spanish and Brazilian charts that *are* in the pipeline are also
published as georeferenced vector PDFs. Rendering those, as the FAA's IFR charts
are rendered, would be sharper than upsampling their rasters.

**This project's GDAL cannot open a PDF.** Its PDF driver is built without a
reader. Every report that inspected one did so with `pypdfium2` and by reading
the geospatial dictionaries out of the file.

## Needs you

Sources that are free but that a script may not reach, because reaching them
means accepting terms, registering, or passing a bot challenge. The pipeline
does none of those.

| Country | Chart | What stands in the way |
| --- | --- | --- |
| Iceland | Aeronautical Chart ICAO 1:500,000, georeferenced PDF | A tick-box accepting a disclaimer |
| United Arab Emirates | Aeronautical Chart ICAO 1:500,000, GeoTIFF | Terms bar automated access |
| Bulgaria | Aeronautical chart, PDF and KMZ | Free registration |
| Lithuania | VFR chart, and an online chart that may serve tiles | Bot challenge on every host |
| Georgia | Aeronautical Chart ICAO, GeoTIFF and PDF per its AIP | Download page empty on the day |
| Hungary | ICAO chart 1:500,000 | Licence forbids publication; downloading is acceptance |

## Free to view or download, but republication is refused

Recorded so that they are not researched twice. A written permission from the
publisher would change the answer for any of them.

Norway (web map only), France (paid licence for any public digital use),
Germany, Australia, Saudi Arabia, Qatar, Israel, Malaysia, Thailand, India,
Colombia.

## Nothing free

Canada, United Kingdom, Ireland, Portugal, Italy, Belgium, Finland, Sweden,
Poland, Serbia and Montenegro, Croatia, Greece, Turkey, Ukraine, Belarus,
Armenia, Japan, South Korea, Mongolia, China, Russia, Pakistan, Chile, Ecuador,
Cuba, Costa Rica, Panama, New Zealand, South Africa, and every state that
publishes no VFR chart at all. For all of these the historical layers are the
only cover.

## Attribution

`metadata.json` carries the credit line for whatever layers a tileset was built
from, as `attribution`, and the detail per layer under `layers`. A site that
shows the tiles should show that line.
