# LHV Portfolio Bridge Utility

## Introduction

The LHV Portfolio Bridge Utility simplifies the integration of portfolio data from LHV Bank into backend systems
by automating data updates and sending authentication requests via Mobile ID.
This ensures backend services receive and process portfolio information efficiently.

I developed this utility to streamline the transfer of financial data into my own systems,
where I could store and analyze the data using customized metrics.
My goal was to create a robust, automated solution that not only saved time but also provided deeper insights
through enhanced data accessibility and analysis capabilities.

## Quick Start

Setup

```shell
git clone git@github.com:KasparRosin/lhv-portfolio-bridge-util.git
cd lhv-portfolio-bridge-util
```

Executing the script

```shell
# Docker
docker build -t lhv-portfolio-bridge-util . && docker run -it lhv-portfolio-bridge-util

# or Python
pip install -r requirements.txt
python main.py
```
