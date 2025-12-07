from pathlib import Path


def process_fprints(target: Path, symbols: dict[str, bytes], paths_to_models):
    print("\n 👣 Footprints ...")

    target_models = target.with_suffix(".pretty")
    print(target_models)
    print(symbols.keys())