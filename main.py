import asyncio
import json
import os
import random

from prettytable import PrettyTable
from core import execute_swap, track_mempool
from eth_utils import to_hex
from services import (
    establish_quicknode_http_connection,
    initialize_uniswap_router,
)
from services.get_liquidity_weth_usdc import get_liquidity_and_price
from utils import get_transaction_gas_price

web3_http = establish_quicknode_http_connection()
router = initialize_uniswap_router(web3_http)


async def main():
    ready = asyncio.Event()
    listener = asyncio.create_task(
        track_mempool(
            max_swaps=20,
            max_seconds=60,
            subscription_ready=ready,
            router=router,
            web3_http=web3_http,
        )
    )
    weth_address = web3_http.to_checksum_address(os.getenv("WETH_TOKEN"))
    usdc_address = web3_http.to_checksum_address(os.getenv("USDC_TOKEN"))
    #get_liquidity_and_price(web3_http, weth_address, usdc_address, 8543949317590771002000)
    #execute_swap(web3_http, router, 8543949317590771002000)
    await ready.wait()
    for _ in range(3):
        if random.random() < 0.9:
            amount_eth = round(random.uniform(0.0003, 0.002), 6)
        else:
            amount_eth = round(random.uniform(0.005, 0.02), 6)
        execute_swap(web3_http, router, amount_eth)
        await asyncio.sleep(0.5)
    swaps = await listener
    print(
        f"🎯 Successfully captured {len(swaps)} router {'swap' if len(swaps) == 1 else 'swaps'}! 🚀"
    )
    swaps.sort(key=get_transaction_gas_price, reverse=True)

    t = PrettyTable(["Transaction Hash", "Gas Price"])
    t.hrules = True
    for tx in swaps:
        t.add_row([to_hex(tx["hash"]), get_transaction_gas_price(tx)])
    print(t)

    with open("output/swaps.json", "w") as f:
        json.dump([dict(tx) for tx in swaps], f, indent=2, default=to_hex)


if __name__ == "__main__":
    asyncio.run(main())
