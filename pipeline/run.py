"""CLI for the offline pipeline: python -m pipeline.run [step ...|all]."""

import argparse
import importlib

STEPS = ["zone", "roads", "terrain", "population", "buildings", "sites", "rainfall", "river",
         "precompute", "snapshot"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("steps", nargs="+", choices=STEPS + ["all"])
    args = parser.parse_args()
    steps = STEPS if "all" in args.steps else args.steps
    for name in steps:
        module = importlib.import_module(f"pipeline.{name}")
        if not hasattr(module, "build"):
            print(f"[skip] pipeline.{name}.build() not implemented yet")
            continue
        print(f"[run] {name}")
        module.build()


if __name__ == "__main__":
    main()
