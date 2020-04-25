## Introduction
This is a script that identifies purchases to make to track a portfolio.
The assets in the portfolio need to be tracked by stocks or ETFs.

## Getting started
Install pyyaml and git clone the repository. Requires Python 3.6.

```sh
pip3 install pyyaml
git clone git@github.com:chriswilker/portfolio-purchase.git
cd portfolio-purchase
```

## Use
Give the path to a portfolio yaml file, dollars used for the purchase,
and dollars currently invested in the assets in the portfolio as
arguments. The suggested dollar fund purchases to track the portfolio
are displayed. In the below example, a maximum of $1000.00 will be spent
purchasing funds, $150.00 is already invested in the US stock market
(represented by the "VTI" ETF), and $50.50 are already invested in the
US bond market (represented by the "BND" ETF). The displayed output
suggests putting $570.30 in the US stock market and $429.70 in the US
bond market.

```console
$ python3 proportions.py example-portfolios/world-stock-market.yml 1000 150 50.50
"VTI": 570.30
"BND": 429.70
```

Use the -i flag to purchase assets in integer amounts. This can be
useful when investing in ETFs or stocks, which often can only be
purchased in integer amounts. The number of suggested assets to buy are
displayed. In the below example the displayed output suggests buying 3
shares of the "VTI" ETF and 5 shared of the "BND" ETF.

```console
$ python3 proportions.py -e example-portfolios/world-stock-market.yml 1000 150 50.50
"VTI": 3
"BND": 5
```

Run `python3 proportions.py -h` to get help.

## Creating a portfolio yaml file
The yaml file should be structured like this:

```yaml
"VTI": 0.60
"BND": 0.40
```

Each asset is represented by the ticker symbol of the stock, ETF, etc.
that tracks the asset. For example, the ticker VTI represents the
Vanguard Total Stock Market Index ETF, which tracks the US stock market.
The decimal on the right is the desired proportion of the portfolio
taken up by that asset. The above example represents a 60% US stocks,
40% US bonds portfolio.
