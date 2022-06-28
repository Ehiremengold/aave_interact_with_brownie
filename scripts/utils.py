from brownie import accounts, network, config

forked_dev_env = ["mainnet-fork"]

local_dev_env = ["development", "mainnet-fork"]


def get_account(id=None, index=None):
    if id:
        return accounts.load(id)
    if index:
        return accounts[index]
    if network.show_active() in local_dev_env:
        return accounts[0]
    return accounts.add(config["wallets"]["from_key"])
