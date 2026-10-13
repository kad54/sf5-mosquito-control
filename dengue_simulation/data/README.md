# Input data

The geographical simulation needs these files relative to this directory:

| Path | Required columns |
| --- | --- |
| `population/city_population_data.csv` | `city,country,population,lat,lng` |
| `city_distances.csv` | `city1,city2,distance` (kilometres) |
| `climate/city_temperature_data.csv` | `index,city,tavg` (timestamp, city name, Celsius) |

The CSV snapshot used for the coursework is retained locally and is not included in this repository. Its redistribution terms have not been confirmed. City data was prepared from Simplemaps World Cities; weather was obtained through Meteostat with synthetic seasonal fallback. The exact city-data edition is unconfirmed.

The supporting scripts show the original preparation steps, but a new download can differ from the original inputs. Temperature dates accepted by the SIR code use `YYYY-MM-DD HH:MM:SS` in `index`; rows dated only in `time` are omitted. See [methodology](../../methodology.md).

`--data-dir` can point the runner at an existing data folder. For example, from this repository root on the original local machine:

```powershell
python -m dengue_simulation.main --data-dir ../../dengue_simulation/data --legacy-identifiers --seed 2024
```

That relative path applies when this copy is under `SF5/publication/sf5-coursework/`. For a different location, supply the path to your own input folder.
