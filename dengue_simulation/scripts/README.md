# Supporting coursework scripts

These are selected original files, copied without changing their algorithms:

| File | Purpose |
| --- | --- |
| `population_data.py` | Prepare the European city population subset. |
| `city_data.py` | Compute geographical distances for the largest 1,000 population rows. |
| `climate_data.py` | Obtain weather and generate seasonal fallback data. |
| `results.py` | Original combined-centrality before/after comparison. |
| `seir_model.py` | Earlier city SIR beta sweep (despite the filename). |
| `sir_model_assignment_2.py` | Additional SIR and threshold exploration. |
| `sir_model_assignment_3.py` | Additional SIR and eigenvalue exploration. |

The straightforward entry point is `python -m dengue_simulation.main` from the repository root. These older scripts are retained to show the coursework work behind it; they are not all independently verified.

Most older scripts expect to run from `dengue_simulation/`, using relative `data/` paths. Data preparation scripts can overwrite outputs. `population_data.py` expects `worldcities.csv`; `city_data.py` writes `city_distances.csv` to its working directory, which must be placed under `data/` for the simulations. `climate_data.py` makes upstream weather requests and requires the population CSV first.

Depending on the script, extra dependencies include Geopy, Meteostat, Seaborn, SciPy and Basemap. Those historical environments were not reconstructed. The root requirements cover only the runnable combined-centrality entry point. Earlier unrelated exercises and prototype frameworks are retained in the original local project, outside this compact report repository.
