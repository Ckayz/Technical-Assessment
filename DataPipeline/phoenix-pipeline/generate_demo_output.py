"""Generate sample output for demo purposes.

This script creates realistic sample output files to demonstrate the pipeline
without needing API keys. Useful for demos when API access isn't available.

Usage:
    python generate_demo_output.py

Outputs:
    - output/swaps.json: Enriched swap data (JSON)
    - output/summary.csv: Aggregated statistics (CSV)
    - output/state.json: Pipeline state (JSON)
"""

import json
from pathlib import Path
from datetime import datetime


def generate_demo_output():
    """Generate realistic demo output files."""

    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    print("=" * 80)
    print("Phoenix Pipeline - Demo Output Generator")
    print("=" * 80)
    print()

    # Sample enriched swaps (JSON output)
    # These represent realistic Uniswap V3 swap data with price enrichment
    swaps = [
        {
            "txHash": "0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
            "blockNumber": 18500120,
            "timestamp": 1698765432,
            "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH
            "token1": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
            "amount0": "1000000000000000000",  # 1 WETH (18 decimals)
            "amount1": "-2000000000",  # -2000 USDC (6 decimals)
            "sqrtPriceX96": "1234567890123456789",
            "priceUSD0": 2000.50,  # ENRICHED: WETH price
            "priceUSD1": 1.00,     # ENRICHED: USDC price
            "usdVolume": 2000.50,  # ENRICHED: USD volume
            "pair": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        },
        {
            "txHash": "0x2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c",
            "blockNumber": 18500125,
            "timestamp": 1698765532,
            "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH
            "token1": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
            "amount0": "2000000000000000000",  # 2 WETH
            "amount1": "-4000000000",  # -4000 USDC
            "sqrtPriceX96": "1234567890123456789",
            "priceUSD0": 2000.50,
            "priceUSD1": 1.00,
            "usdVolume": 4001.00,
            "pair": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        },
        {
            "txHash": "0x3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d",
            "blockNumber": 18500130,
            "timestamp": 1698765632,
            "token0": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",  # WBTC
            "token1": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
            "amount0": "50000000",  # 0.5 WBTC (8 decimals)
            "amount1": "-20000000000",  # -20000 USDC
            "sqrtPriceX96": "9876543210987654321",
            "priceUSD0": 40000.00,  # ENRICHED: WBTC price
            "priceUSD1": 1.00,      # ENRICHED: USDC price
            "usdVolume": 20000.00,  # ENRICHED: USD volume
            "pair": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        },
        {
            "txHash": "0x4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e",
            "blockNumber": 18500135,
            "timestamp": 1698765732,
            "token0": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",  # UNI
            "token1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH
            "amount0": "1000000000000000000000",  # 1000 UNI (18 decimals)
            "amount1": "-3000000000000000000",  # -3 WETH
            "sqrtPriceX96": "5555555555555555555",
            "priceUSD0": 6.50,      # ENRICHED: UNI price
            "priceUSD1": 2000.50,   # ENRICHED: WETH price
            "usdVolume": 12501.50,  # ENRICHED: USD volume (sum both sides)
            "pair": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984-0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
        },
        {
            "txHash": "0x5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f",
            "blockNumber": 18500140,
            "timestamp": 1698765832,
            "token0": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",  # WETH
            "token1": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
            "amount0": "5000000000000000000",  # 5 WETH
            "amount1": "-10000000000",  # -10000 USDC
            "sqrtPriceX96": "1234567890123456789",
            "priceUSD0": 2000.50,
            "priceUSD1": 1.00,
            "usdVolume": 10002.50,
            "pair": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        }
    ]

    # Write JSON output
    swaps_path = output_dir / "swaps.json"
    with open(swaps_path, "w") as f:
        json.dump(swaps, f, indent=2)

    print(f"✓ Created {swaps_path}")
    print(f"  - {len(swaps)} enriched swaps")
    print(f"  - Includes: txHash, blockNumber, prices, USD volumes")
    print()

    # Write CSV summary
    # Aggregate by trading pair
    summary_csv = output_dir / "summary.csv"

    # Calculate aggregations
    pair_stats = {}
    for swap in swaps:
        pair = swap["pair"]
        volume = swap["usdVolume"]

        if pair not in pair_stats:
            pair_stats[pair] = {"count": 0, "total": 0.0}

        pair_stats[pair]["count"] += 1
        pair_stats[pair]["total"] += volume

    # Sort by total volume descending
    sorted_pairs = sorted(
        pair_stats.items(),
        key=lambda x: x[1]["total"],
        reverse=True
    )

    with open(summary_csv, "w") as f:
        # Write header
        f.write("pair,count,totalUSD,avgUSD\n")

        # Write data
        for pair, stats in sorted_pairs:
            count = stats["count"]
            total = stats["total"]
            avg = total / count
            f.write(f"{pair},{count},{total:.2f},{avg:.2f}\n")

    print(f"✓ Created {summary_csv}")
    print(f"  - {len(pair_stats)} unique trading pairs")
    print(f"  - Aggregated: count, totalUSD, avgUSD")
    print()

    # Display summary
    print("Summary Statistics:")
    print("-" * 80)
    for pair, stats in sorted_pairs:
        # Shorten address for display
        pair_display = f"{pair[:10]}...{pair[-8:]}"
        count = stats["count"]
        total = stats["total"]
        avg = total / count
        print(f"  {pair_display:30s}  Count: {count:2d}  Total: ${total:10,.2f}  Avg: ${avg:10,.2f}")
    print()

    # Write state file
    state_path = output_dir / "state.json"
    state = {
        "last_processed_block": 18500140,  # Latest block from swaps
        "last_updated": datetime.now().isoformat()
    }

    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)

    print(f"✓ Created {state_path}")
    print(f"  - Last processed block: {state['last_processed_block']}")
    print(f"  - Timestamp: {state['last_updated']}")
    print()

    # Summary
    print("=" * 80)
    print("Demo Output Generation Complete!")
    print("=" * 80)
    print()
    print("View outputs:")
    print(f"  JSON: cat {swaps_path}")
    print(f"  CSV:  cat {summary_csv}")
    print(f"  State: cat {state_path}")
    print()
    print("Pretty print JSON:")
    print(f"  cat {swaps_path} | python -m json.tool")
    print()
    print("View CSV as table:")
    print(f"  column -t -s, {summary_csv}")
    print()


if __name__ == "__main__":
    generate_demo_output()
