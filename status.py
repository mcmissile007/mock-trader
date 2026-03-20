"""Show current status of all traders.

Usage:
    python status.py
"""
import db


def main():
    db.init_db()
    traders = db.get_active_traders()

    if not traders:
        print("No active traders")
        return

    print(f"\n{'='*80}")
    print("  MOCK TRADER STATUS")
    print(f"{'='*80}")

    for t in traders:
        summary = db.get_trades_summary(t["id"])
        open_pos = db.get_open_positions(t["id"])
        strategy = t["strategy"]

        total = int(summary.get("total", 0) or 0)
        wins = int(summary.get("wins", 0) or 0)
        wr = wins / total if total > 0 else 0
        pnl_usd = float(summary.get("total_pnl_usd", 0) or 0)
        avg_pnl = float(summary.get("avg_pnl", 0) or 0)

        print(f"\n  {'_'*50}")
        print(f"  {t['name']} ({t['model_type']})")
        print(f"  {'_'*50}")
        print(f"  Strategy: TP={strategy.get('tp', 0):+.0%} SL={strategy.get('sl', 0):+.0%} hold={strategy.get('max_hold', 72)}h")
        print(f"  Trades: {total} (WR={wr:.0%})")
        print(f"  P&L: ${pnl_usd:+.4f} (avg={avg_pnl*100:+.4f}%)")
        print(f"  Open positions: {len(open_pos)}")

        for pos in open_pos:
            entry = float(pos['entry_price'])
            print(f"    #{pos['id']}: entry=${entry:.2f} conf={float(pos['confidence']):.3f} since {pos['entry_time']}")

    print(f"\n{'='*80}")


if __name__ == "__main__":
    main()
