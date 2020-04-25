import argparse
import yaml
from typing import Dict, List, Tuple
import urllib.request
import json
from collections import OrderedDict
import math


def main() -> None:
    parser = argparse.ArgumentParser(
        description="""Display dollars of assets to purchase to track a
        portfolio. See https://github.com/chriswilker/portfolio-purchases for
        more information.
        """
    )
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
    parser.add_argument(
        "-i",
        help="display integer amounts of assets to purchase",
        action="store_true",
    )
    args = parser.parse_args()
    with open(args.portfolio_file, "r") as stream:
        portfolio = yaml.safe_load(stream)
        owned = OrderedDict()
        for i, asset in enumerate(portfolio):
            owned[asset] = args.amounts_owned[i]

        if args.i:
            ep = etf_purchases(portfolio, args.purchase_amount, owned)
            print(etf_output(ep), end="")
        else:
            fp = fund_purchases(portfolio, args.purchase_amount, owned)
            print(fund_output(fp), end="")


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


def etf_purchases(
    desired_proportions: Dict,
    purchase_amount: float,
    amounts_owned: OrderedDict,
) -> OrderedDict:
    money_remaining = purchase_amount

    purchases = OrderedDict()
    for etf in desired_proportions.keys():
        purchases[etf] = 0

    prices = OrderedDict()
    for etf in desired_proportions.keys():
        prices[etf] = current_price(etf)

    while etf:
        etf = etf_to_purchase(
            desired_proportions, money_remaining, amounts_owned, prices,
        )
        if etf:
            money_remaining = money_remaining - prices[etf]
            amounts_owned[etf] += prices[etf]
            purchases[etf] += 1
    return purchases


def current_price(ticker: str) -> float:
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker}"
    contents = urllib.request.urlopen(url).read()
    response = json.loads(contents)["quoteResponse"]
    error = response["error"]
    if error:
        raise ValueError(f"Response from {url} contains an error:\n{error}")
    else:
        return response["result"][0]["regularMarketPrice"]


def etf_to_purchase(
    desired_proportions: Dict,
    purchase_amount: float,
    amounts_owned: OrderedDict,
    prices: OrderedDict,
) -> Tuple[float, OrderedDict, OrderedDict]:
    # Get the proportional amounts of the assets owned, factoring in the
    # additional money used for the purchase
    total_owned = sum(amounts_owned.values()) + purchase_amount
    props = OrderedDict()
    for etf in amounts_owned.keys():
        props[etf] = amounts_owned[etf] / total_owned

    # figure out which purchases move closest to their ideal proportions
    max_diff_reduction_per_dollar = 0.0
    max_diff_reduction_etfs = []
    for etf in props.keys():
        if prices[etf] < purchase_amount:
            prop_after_purchase = props[etf] + prices[etf] / total_owned
            prop_diff_reduction = abs(
                desired_proportions[etf] - props[etf]
            ) - abs(desired_proportions[etf] - prop_after_purchase)
            diff_reduction_per_dollar = prop_diff_reduction / prices[etf]
            if diff_reduction_per_dollar > max_diff_reduction_per_dollar:
                max_prop_diff_reduction_per_dollar = diff_reduction_per_dollar
                max_diff_reduction_etfs.append(etf)

    min_prop_after_purchase = 1.01
    min_prop_etf = ""
    for etf in max_diff_reduction_etfs:
        prop_after_purchase = props[etf] + prices[etf] / total_owned
        if prop_after_purchase < min_prop_after_purchase:
            min_prop_after_purchase = prop_after_purchase
            min_prop_etf = etf

    return min_prop_etf


def etf_output(purchases: Dict) -> str:
    out = ""
    for asset, purchase in purchases.items():
        out += f'"{asset}": {purchase}\n'
    return out


def fund_output(purchases: Dict) -> str:
    out = ""
    for asset, purchase in purchases.items():
        out += f'"{asset}": {purchase:.2f}\n'
    return out


if __name__ == "__main__":
    main()
