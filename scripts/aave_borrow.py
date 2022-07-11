from ctypes import addressof
from enum import auto
from tabnanny import check

from pyrsistent import optional
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
    approve_erc20(erc20_address, lending_pool, amount, account)
    deposit_eth(erc20_address, amount, account)
    # optional
    borrowable_data, total_debt = get_borrowable_data(account)
    dai_eth_price = get_asset_price(
        config["networks"][network.show_active()]["dai_eth_price_feed"]
    )
    # 0.95 for better health factor
    amount_to_borrow = Web3.toWei(
        (1 / float(dai_eth_price)) * (borrowable_data * 0.95), "ether"
    )
    dai_address = config["networks"][network.show_active()]["dai_address"]
    borrow_asset(dai_address, amount_to_borrow, account)
    print(f"You borrow {amount_to_borrow} of DAI")
    get_borrowable_data(account)
    repay_all(dai_address, amount, account)




def get_lending_pool():
    lending_pool_address_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_address_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool


def approve_erc20(erc20_address, spender, amount, account):
    erc20 = interface.IERC20(erc20_address)
    print("approving tokens")
    tx = erc20.approve(spender.address, amount, {"from": account})
    tx.wait(1)
    return tx


def deposit_eth(erc20_address, amount, account):
    lending_pool = get_lending_pool()
    approve_erc20(erc20_address, lending_pool, amount, account)
    tx = lending_pool.deposit(
        erc20_address, amount, account.address, 0, {"from": account}
    )
    tx.wait(1)
    print("Eth deposited, received corresponding aToken")
    return tx


def get_borrowable_data(account):
    lending_pool = get_lending_pool()
    print("getting borrowabledata")
    (
        total_eth_collateral,
        total_eth_debt,
        available_borrowable_eth,
        current_liquidation_threshold,
        ltv,
        health_factor,
    ) = lending_pool.getUserAccountData(account.address)
    available_borrowable_eth = Web3.fromWei(available_borrowable_eth, "ether")
    total_eth_collateral = Web3.fromWei(total_eth_collateral, "ether")
    total_eth_debt = Web3.fromWei(total_eth_debt, "ether")
    return float(available_borrowable_eth), float(total_eth_debt)


def get_asset_price(price_feed_address):
    asset_price_feed = interface.AggregatorV3Interface(price_feed_address)
    asset_price = asset_price_feed.latestRoundData()[1]
    converted_price = Web3.fromWei(asset_price, "ether")
    return converted_price


def borrow_asset(asset_address, amount_to_borrow, account):
    lending_pool = get_lending_pool()
    borrow_tx = lending_pool.borrow(
        asset_address.address,
        amount_to_borrow,
        1,
        0,
        account.address,
        {"from": account},
    )
    borrow_tx.wait(1)
    print("you borrowed some asset:DAI")
    return borrow_tx


def repay_all(asset_address, amount, account):
    lending_pool = get_lending_pool()
    approve_erc20(asset_address, lending_pool.address, amount, account)
    tx = lending_pool.repay(
        asset_address.address, amount, 1, account.address, {"from": account}
    )
    tx.wait(1)
    print("repaid all")
    return tx
