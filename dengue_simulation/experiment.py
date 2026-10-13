"""Seeded orchestration of the original city SIR and combined removal routines.

This runner does not add probabilistic recovery, mosquito compartments or a
new transmission model. See methodology.md for the original semantics.
"""

import argparse
import hashlib
import json
import platform
import random
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from .model import SIR_simulation, combined_centrality_removal_strategy


DATA_DIR = Path(__file__).resolve().parent / "data"


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_network(data_dir, legacy_identifiers=False):
    """Match results.py preprocessing while reading the climate file in chunks.

    Intentionally use only the original `index` date column. Switching to the
    fallback `time` column would change the research experiment.
    """
    population_path = data_dir / "population/city_population_data.csv"
    distance_path = data_dir / "city_distances.csv"
    climate_path = data_dir / "climate/city_temperature_data.csv"
    for path in (population_path, distance_path, climate_path):
        if not path.is_file():
            raise ValueError(f"Missing input: {path}. See dengue_simulation/data/README.md.")
    cities = pd.read_csv(population_path)
    required = {"city", "country", "population", "lat", "lng"}
    if not required.issubset(cities.columns):
        raise ValueError(f"Population data requires columns {sorted(required)}")
    missing = int(cities.city.isna().sum())
    repeated = int(cities.city.duplicated().sum())
    if missing or repeated:
        message = (f"Population input has {missing} missing and {repeated} repeated city names. "
                   "The original graph uses city names as identifiers and collapses repeated names.")
        if not legacy_identifiers:
            raise ValueError(message + " Use --legacy-identifiers to retain this documented behaviour.")
        warnings.warn(message, stacklevel=2)

    sums, counts = {}, {}
    rows = valid_rows = 0
    for chunk in pd.read_csv(climate_path, usecols=["index", "city", "tavg"], chunksize=200000):
        rows += len(chunk)
        dates = pd.to_datetime(chunk["index"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        chunk = chunk.loc[dates.notna()]
        valid_rows += len(chunk)
        grouped = chunk.groupby("city")["tavg"].agg(["sum", "count"])
        for city, row in grouped.iterrows():
            sums[city] = sums.get(city, 0.0) + float(row["sum"])
            counts[city] = counts.get(city, 0) + int(row["count"])
    means = {city: sums[city] / count for city, count in counts.items() if count}
    if not means:
        raise ValueError("No usable temperature rows in the original index date column.")
    low, high = min(means.values()), max(means.values())
    if not np.isfinite([low, high]).all() or low == high:
        raise ValueError("Original temperature scaling requires a finite, nonzero temperature range.")

    graph = nx.Graph()
    for _, row in cities.iterrows():
        graph.add_node(row["city"], population=row["population"], country=row["country"],
                       lat=row["lat"], lng=row["lng"])
    distance_rows = 0
    for chunk in pd.read_csv(distance_path, chunksize=200000):
        if not {"city1", "city2", "distance"}.issubset(chunk.columns):
            raise ValueError("Distance data requires city1, city2 and distance columns.")
        distance_rows += len(chunk)
        for _, row in chunk.loc[chunk.distance <= 100].iterrows():
            graph.add_edge(row["city1"], row["city2"], weight=row["distance"])
    missing_temperatures = 0
    for city in graph:
        if city not in means:
            missing_temperatures += 1
        temperature = means.get(city, 0)
        graph.nodes[city]["lambda"] = 0.1 + (temperature - low) / (high - low) * 0.4
    info = {"population_rows": len(cities), "missing_city_names": missing,
            "repeated_city_names": repeated, "distance_rows": distance_rows,
            "climate_rows": rows, "climate_rows_with_valid_index_date": valid_rows,
            "nodes": len(graph), "edges": graph.number_of_edges(),
            "isolated_nodes": nx.number_of_isolates(graph),
            "nodes_without_temperature_mean": missing_temperatures,
            "mean_temperature_min": low, "mean_temperature_max": high}
    return graph, info, [population_path, distance_path, climate_path]


def run_experiment(graph, betas, repeats, initial_count, remove_count, seed, output_dir):
    """Use one initial infected sample and the original sequential RNG stream."""
    if not 1 <= initial_count <= len(graph):
        raise ValueError("Initial infected count must be between one and the number of nodes.")
    if not 0 <= remove_count < len(graph):
        raise ValueError("Removal count must be smaller than the number of nodes.")
    if repeats < 1 or any(not 0 <= beta <= 1 for beta in betas):
        raise ValueError("Use positive repeats and beta values in [0, 1].")
    for _, attrs in graph.nodes(data=True):
        for beta in betas:
            probability = beta * attrs["lambda"]
            if not np.isfinite(probability) or not 0 <= probability <= 1:
                raise ValueError("Input temperatures give an invalid transmission probability.")
    random.seed(seed)
    np.random.seed(seed)
    initial = random.sample(list(graph.nodes), initial_count)
    records = []
    trajectories = []

    def simulate(current_graph, infected, strategy):
        for beta in betas:
            for repeat in range(repeats):
                final_s, final_i, final_r, s_values, i_values, r_values = SIR_simulation(
                    current_graph, infected, beta, gamma=0.1)
                records.append({"strategy": strategy, "beta": beta, "repeat": repeat,
                                "nodes": len(current_graph), "initial_infected": len(infected),
                                "final_S": final_s, "final_I": final_i, "final_R": final_r})
                for time, (s, i, r) in enumerate(zip(s_values, i_values, r_values), start=1):
                    trajectories.append({"strategy": strategy, "beta": beta, "repeat": repeat,
                                         "step": time, "S": s, "I": i, "R": r})

    simulate(graph, initial, "before_control")
    controlled = graph.copy()
    removed = combined_centrality_removal_strategy(controlled, remove_count) if remove_count else []
    initial_after = [city for city in initial if city in controlled]
    simulate(controlled, initial_after, "combined_centrality")
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = pd.DataFrame(records)
    summary.to_csv(output_dir / "summary.csv", index=False)
    pd.DataFrame(trajectories).to_csv(output_dir / "trajectories.csv", index=False)
    pd.DataFrame({"city": removed}).to_csv(output_dir / "removed_cities.csv", index=False)
    fig, ax = plt.subplots(figsize=(8, 5))
    for strategy, group in summary.groupby("strategy", sort=False):
        means = group.groupby("beta")["final_R"].mean()
        ax.plot(means.index, means.values, marker="o", label=strategy.replace("_", " "))
    ax.set(xlabel="Transmission parameter beta", ylabel="Final recovered cities (cumulative affected)",
           title=f"New seeded run: seed={seed}, repetitions={repeats}")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "outbreak_size.png", dpi=150)
    plt.close(fig)
    return {"initial_infected_cities": [str(x) for x in initial],
            "initial_infected_cities_after_removal": [str(x) for x in initial_after],
            "removed_cities": [str(x) for x in removed]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DATA_DIR.parent / "results/seeded")
    parser.add_argument("--seed", type=int, default=2024)
    parser.add_argument("--betas", type=float, nargs="+", default=[0.2, 0.4, 0.6])
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--initial-infected", type=int, default=200)
    parser.add_argument("--remove", type=int, default=5)
    parser.add_argument("--legacy-identifiers", action="store_true")
    args = parser.parse_args(argv)
    if not 0 <= args.seed < 2**32:
        parser.error("Seed must be in [0, 2**32).")
    try:
        graph, info, inputs = load_network(args.data_dir, args.legacy_identifiers)
        selection = run_experiment(graph, args.betas, args.repeats, args.initial_infected,
                                   args.remove, args.seed, args.output_dir)
    except (ValueError, nx.PowerIterationFailedConvergence) as error:
        parser.exit(2, f"Experiment stopped: {error}\nSee methodology.md and dengue_simulation/data/README.md.\n")
    metadata = {"seed": args.seed, "betas": args.betas, "repeats": args.repeats,
                "initial_infected": args.initial_infected, "remove": args.remove,
                "legacy_identifiers": args.legacy_identifiers, "inputs": info,
                "input_sha256": {p.relative_to(args.data_dir).as_posix(): file_hash(p) for p in inputs},
                "model_sha256": file_hash(Path(__file__).with_name("model.py")),
                "runner_sha256": file_hash(Path(__file__)),
                "python": platform.python_version(),
                "versions": {m.__name__: m.__version__ for m in (np, pd, nx, matplotlib)},
                "notes": ["New validation experiment, not a reconstruction of the unseeded report run.",
                          "Gamma is unused; infection lasts one discrete step.",
                          "City names and original index-only climate preprocessing are preserved.",
                          "Centrality ignores geographic edge weights, matching results.py.",
                          "After-control runs may have fewer initial infections when seed cities are removed."],
                **selection}
    (args.output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n",
                                              encoding="utf-8")
    print(f"Wrote new seeded experiment to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
