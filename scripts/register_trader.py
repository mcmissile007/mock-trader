"""Register a new trader in the database.

Usage:
    # XGBoost trader from Velma
    python register_trader.py \\
        --name xgboost_v1 \\
        --type XGBoost \\
        --model-path /path/to/trained_model \\
        --tp 0.04 --sl -0.04 --max-hold 72 --min-confidence 0.80

    # Random baseline trader
    python register_trader.py \\
        --name random_baseline \\
        --type Random \\
        --buy-prob 0.05 \\
        --tp 0.04 --sl -0.04 --max-hold 72
"""

import argparse
import json

import db


def main():
    parser = argparse.ArgumentParser(description="Register a trader")
    parser.add_argument("--name", required=True, help="Unique trader name")
    parser.add_argument("--type", required=True, choices=["XGBoost", "Random", "LLM"])
    parser.add_argument("--model-path", default="", help="Path to model dir")
    parser.add_argument("--tp", type=float, default=0.04)
    parser.add_argument("--sl", type=float, default=-0.04)
    parser.add_argument("--max-hold", type=int, default=72)
    parser.add_argument("--min-confidence", type=float, default=0.80)
    parser.add_argument("--amount-usd", type=float, default=10)
    parser.add_argument("--buy-prob", type=float, default=0.05)
    args = parser.parse_args()

    strategy = {
        "tp": args.tp,
        "sl": args.sl,
        "max_hold": args.max_hold,
        "min_confidence": args.min_confidence,
        "amount_usd": args.amount_usd,
    }
    if args.type == "Random":
        strategy["buy_probability"] = args.buy_prob

    features = []
    if args.model_path and args.type == "XGBoost":
        from pathlib import Path

        meta_path = Path(args.model_path) / "metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
            features = meta.get("features", [])

    db.init_db()
    trader_id = db.register_trader(
        name=args.name,
        model_type=args.type,
        model_path=args.model_path,
        features=features,
        strategy=strategy,
    )
    print(f"Registered trader '{args.name}' (id={trader_id})")
    print(f"   Type: {args.type}")
    print(f"   Strategy: TP={args.tp:+.0%}, SL={args.sl:+.0%}, hold={args.max_hold}h")
    if features:
        print(f"   Features: {len(features)}")


if __name__ == "__main__":
    main()
