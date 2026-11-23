import argparse
import json
from pathlib import Path
from .core import Model


def main():
    parser = argparse.ArgumentParser(description="Audit-ready portfolio fragility analysis")
    parser.add_argument("portfolio", type=Path, help="JSON model input")
    parser.add_argument("--loss", type=float, default=1000000)
    parser.add_argument("--hedge", action="store_true")
    parser.add_argument("--radius", type=float, default=2.0)
    args = parser.parse_args()
    raw = json.loads(args.portfolio.read_text(encoding="utf-8"))
    model = Model.build(raw["factors"], raw["exposure"], raw["covariance"])
    report = {"reverse_stress": model.reverse_stress(args.loss)}
    if args.hedge:
        h = raw["hedges"]
        report["hedge"] = model.hedge(args.loss, h["factor_sensitivities"],
                                      h["cost_per_unit"], h["names"], args.radius)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
