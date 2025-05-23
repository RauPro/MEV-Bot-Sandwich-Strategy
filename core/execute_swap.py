import json
import os
import random
import time
from config import ACCOUNT, CHAIN_ID
from eth_utils import to_hex


def execute_swap(web3, router, amount_eth):
    """
    Executes a test swap transaction on the Uniswap router.

    Args:
        web3: Web3 instance
        router_contract: Contract instance of the Uniswap router

    Returns:
        str: Transaction hash of the executed swap
    """

    deadline = int(time.time()) + 900
    nonce = web3.eth.get_transaction_count(ACCOUNT.address, "pending")
    weth_address = web3.to_checksum_address(os.getenv("WETH_TOKEN"))
    usdc_address = web3.to_checksum_address(os.getenv("USDC_TOKEN"))
    # get_liquidity(web3, weth_address, usdc_address)
    amount_in_wei = web3.to_wei(amount_eth, "ether")
    amounts_out = router["contract"].functions.getAmountsOut(amount_in_wei, [usdc_address, weth_address]).call()
    min_amount_out = int(amounts_out[-1] * (1 - 0.01))
    gas_estimate = router["contract"].functions.swapExactETHForTokens(min_amount_out, [weth_address, usdc_address],
        ACCOUNT.address, deadline).estimate_gas({"from": ACCOUNT.address, "value": amount_in_wei, })
    gas_limit = int(gas_estimate * 1.2)
    latest = web3.eth.get_block("latest")
    base_fee = latest["baseFeePerGas"]
    tip = web3.to_wei(2, "gwei")
    max_fee = base_fee + tip
    tx = (router["contract"].functions.swapExactETHForTokens(min_amount_out, [weth_address, usdc_address],
        ACCOUNT.address, deadline).build_transaction({
    "from":                   ACCOUNT.address,
    "value":                  amount_in_wei,
    "nonce":                  nonce,
    "gas":                    gas_limit,
    "maxPriorityFeePerGas":   tip,
    "maxFeePerGas":           max_fee,
    "chainId":                CHAIN_ID,
    }))
    signed = ACCOUNT.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    print("💸 Sent test swap:", to_hex(tx_hash))
    return tx_hash
