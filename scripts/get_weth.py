from brownie import interface
from scripts.utils import *


def main():
    get_weth()


# minting weth
# an ERC20 token
# to interact with the aave protocol
def get_weth():
    """
    Mints WETH by depositing ETH
    {getting} weth for depositing eth,
    so we need to interact with this WETH contract
    we need(an address and abi) to ineract with
    contracts
    """
    # but we are going to be using an interface
    account = get_account()
    print(f"from get_weth: {account.address}")
    # using weth gateway interface to interact
    # with weth contracts on dynamic network
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    # now accessing the deposit function in
    # the weth contract through the interface.
    # where the minting starts. it takes the specified
    # amount of eth and gives us weth(after you added
    # it as atoken on your wallet)
    # Minting
    print("==============================================")
    print("Minting Weth...")
    tx = weth.deposit({"from": account, "value": 0.1 * 10**18})
    tx.wait(1)
    print("Receieved 0.1 Weth!")
    print("==============================================")
    return tx
