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

    # Deactivate a trader
    python register_trader.py --deactivate random_baseline

    # List all traders
    python register_trader.py --list
"""

import argparse
import json

import db


def main():
    parser = argparse.ArgumentParser(description="Register a trader")
    parser.add_argument("--name", help="Unique trader name")
    parser.add_argument(
        "--type",
        choices=["XGBoost", "Random", "LLM"],
    )
    parser.add_argument("--deactivate", metavar="NAME", help="Deactivate a trader")
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all traders",
    )
    parser.add_argument("--model-path", default="", help="Path to model dir")
    parser.add_argument("--tp", type=float, default=0.04)
    parser.add_argument("--sl", type=float, default=-0.04)
    parser.add_argument("--max-hold", type=int, default=72)
    parser.add_argument("--min-confidence", type=float, default=0.80)
    parser.add_argument("--amount-usd", type=float, default=10)
    parser.add_argument("--buy-prob", type=float, default=0.05)
    args = parser.parse_args()

    db.init_db()

    # List mode
    if args.list:
        traders = db.get_active_traders()
        if not traders:
            print("No active traders")
        for t in traders:
            s = t["strategy"]
            print(
                f"  [{t['id']}] {t['name']} ({t['model_type']})"
                f" TP={s.get('tp', 0):+.0%}"
                f" SL={s.get('sl', 0):+.0%}"
                f" hold={s.get('max_hold', 72)}h"
            )
        return

    # Deactivate mode
    if args.deactivate:
        with db.get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE traders SET active = false WHERE name = %s",
                (args.deactivate,),
            )
            if cur.rowcount:
                print(f"Deactivated trader '{args.deactivate}'")
            else:
                print(f"Trader '{args.deactivate}' not found")
        return

    # Register mode — name and type required
    if not args.name or not args.type:
        parser.error("--name and --type are required to register")

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

    trader_id = db.register_trader(
        name=args.name,
        model_type=args.type,
        model_path=args.model_path,
        features=features,
        strategy=strategy,
    )
    print(f"Registered trader '{args.name}' (id={trader_id})")
    print(f"   Type: {args.type}")
    tp = args.tp
    sl = args.sl
    hold = args.max_hold
    print(f"   Strategy: TP={tp:+.0%}, SL={sl:+.0%}, hold={hold}h")
    if features:
        print(f"   Features: {len(features)}")


if __name__ == "__main__":
    main()
