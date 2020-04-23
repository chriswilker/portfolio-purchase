import argparse
import yaml
from typing import Dict, List, Tuple
from collections import OrderedDict
import math


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "portfolio_file",
        type=str,
        help="path to a yaml file representing a portfolio",
    )
    parser.add_argument(
        "purchase_amount",
        type=float,
        help="money available to purchase securities",
    )
    parser.add_argument(
        "amounts_owned",
        metavar="amount_owned",
        type=float,
        nargs="+",
        help="money invested in security (same order as securities in portfolio yaml)",
    )
    args = parser.parse_args()
    with open(args.portfolio_file, "r") as stream:
        portfolio = yaml.safe_load(stream)
        owned = OrderedDict()
        for i, asset in enumerate(portfolio):
            owned[asset] = args.amounts_owned[i]

        fp = fund_purchases(portfolio, args.purchase_amount, owned)
        print(output(fp), end="")


def fund_purchases(
    desired_proportions: Dict,
    purchase_amount: float,
    amounts_owned: OrderedDict,
) -> OrderedDict:
    money_remaining = purchase_amount

    purchases = OrderedDict()
    for asset in desired_proportions.keys():
        purchases[asset] = 0.0
    while money_remaining > 0.01:
        money_remaining, amounts_owned, purchases = make_purchases(
            desired_proportions, money_remaining, amounts_owned, purchases
        )
    return purchases


def make_purchases(
    desired_proportions: Dict,
    purchase_amount: float,
    amounts_owned: OrderedDict,
    purchases: OrderedDict,
) -> Tuple[float, OrderedDict, OrderedDict]:
    # Get the proportional amounts of the assets owned, factoring in the
    # additional money used for the purchase
    total_owned = sum(amounts_owned.values()) + purchase_amount
    props = OrderedDict()
    for asset in amounts_owned.keys():
        props[asset] = amounts_owned[asset] / total_owned

    (
        assets_to_buy,
        amount_to_try_to_buy,
    ) = assets_and_amount_to_buy_to_close_gap(
        desired_proportions, props, total_owned
    )

    # determine how much can be afforded to purchase
    amount_to_buy = min(purchase_amount, amount_to_try_to_buy)
    purchase_amount_per_asset = amount_to_buy / len(assets_to_buy)
    money_remaining = max(0, purchase_amount - amount_to_try_to_buy)

    # update amounts owned and purchases
    for asset in assets_to_buy:
        purchases[asset] += purchase_amount_per_asset
        amounts_owned[asset] += purchase_amount_per_asset

    return money_remaining, amounts_owned, purchases


def assets_and_amount_to_buy_to_close_gap(
    desired_proportions: Dict, proportions: OrderedDict, total_owned: float
) -> Tuple[List[str], float]:
    greatest_prop_diff_from_desired = 0.0
    assets_to_buy = []
    second_greatest_prop_diff_from_desired = 0.0
    for asset, prop in proportions.items():
        diff_from_desired = desired_proportions[asset] - prop
        if math.isclose(diff_from_desired, greatest_prop_diff_from_desired):
            assets_to_buy.append(asset)
        elif diff_from_desired > greatest_prop_diff_from_desired:
            second_greatest_prop_diff_from_desired = (
                greatest_prop_diff_from_desired
            )
            greatest_prop_diff_from_desired = diff_from_desired
            lowest_prop = prop
            assets_to_buy = [asset]
    purchase_amount_to_close_gap = total_owned * (
        greatest_prop_diff_from_desired
        - second_greatest_prop_diff_from_desired
    )
    return assets_to_buy, purchase_amount_to_close_gap


def output(purchases: Dict) -> str:
    out = ""
    for asset, purchase in purchases.items():
        out += f'"{asset}": {purchase:.2f}\n'
    return out


if __name__ == "__main__":
    main()
