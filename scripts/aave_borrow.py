from ctypes import addressof
from enum import auto
from tabnanny import check
from brownie import network, config, interface, accounts
from scripts.utils import get_account, local_dev_env
from scripts.get_weth import get_weth
from web3 import Web3

amount = Web3.toWei(0.1, "ether")


def main():
    account = get_account()
    erc20_address = config["networks"][network.show_active()]["weth_token"]

    if network.show_active() in ["mainnet-fork", "kovan"]:
        get_weth()
    print("interacting with the aave contract...")
    lending_pool = get_lending_pool()
    approve_erc20(lending_pool.address, erc20_address, amount, account)
    deposit_eth(erc20_address, amount, account)
    borrowable_data, total_debt = get_borrowable_data(account)
    dai_eth_price = get_asset_price(
        config["networks"][network.show_active()]["dai_eth_price_feed"]
    )
    amount_to_borrow = Web3.toWei(
        (1 / float(dai_eth_price)) * (borrowable_data * 0.95), "ether"
    )
    dai_address = config["networks"][network.show_active()]["dai_address"]
    borrow_asset(dai_address, amount_to_borrow, account)
    get_borrowable_data(account)
    repay_all(dai_address, amount, account)


def get_lending_pool():
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool


def approve_erc20(spender, erc20_address, amount, account):
    erc20 = interface.IERC20(erc20_address)
    print("Approving token...")
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Token approved!")
    return tx


def deposit_eth(erc20_address, amount, account):
    lending_pool = get_lending_pool()
    print("Minting weth...")
    tx = lending_pool.deposit(
        erc20_address, amount, account.address, 0, {"from": account}
    )
    tx.wait(1)
    print("mint successful!")
    return tx


def get_borrowable_data(account):
    lending_pool = get_lending_pool()
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrowable_eth,
        current_liquidation_threshold,
        ltv,
        health_factor,
    ) = lending_pool.getUserAccountData(account.address)
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
    available_borrowable_eth = Web3.fromWei(available_borrowable_eth, "ether")
    print(f"You have {total_collateral_eth} worth of ETH deposited.")
    print(f"You have {total_debt_eth} worth of ETH borrowed.")
    print(f"You have {available_borrowable_eth} worth of borrowing power")

    return (float(available_borrowable_eth), float(total_debt_eth))


def get_asset_price(price_feed_address):
    dai_price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_dai_price = dai_price_feed.latestRoundData()[1]
    converted_dai_price = Web3.fromWei(latest_dai_price, "ether")
    return converted_dai_price


def borrow_asset(dai_address, amount_to_borrow, account):
    lending_pool = get_lending_pool()
    print("borrowing asset...")
    borrow_tx = lending_pool.borrow(
        dai_address,
        amount_to_borrow,
        1,
        0,
        account.address,
        {"from": account},
    )
    borrow_tx.wait(1)
    return borrow_tx


def repay_all(dai_address, amount, account):
    lending_pool = get_lending_pool()
    approve_erc20(lending_pool.address, dai_address, amount, account)
    print("repaying everything borrowed...")
    tx = lending_pool.repay(dai_address, amount, 1, account.address, {"from": account})
    tx.wait(1)
    print("repayment successful!")
    return tx
