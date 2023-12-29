# The Spymaster Bot
Telegram bot service for Codenames board game. \
Try it at [@the_spymaster_bot](https://t.me/the_spymaster_bot).

[![Lint](https://github.com/asaf-kali/the-spymaster-bot/actions/workflows/lint.yml/badge.svg)](https://github.com/asaf-kali/the-spymaster-bot/actions/workflows/lint.yml)
[![Stability](https://github.com/asaf-kali/the-spymaster-bot/actions/workflows/stability.yml/badge.svg)](https://github.com/asaf-kali/the-spymaster-bot/actions/workflows/stability.yml)
[![Delivery](https://github.com/asaf-kali/the-spymaster-bot/actions/workflows/cd.yml/badge.svg)](https://github.com/asaf-kali/the-spymaster-bot/actions/workflows/cd.yml)

# Description

The Spymaster Bot is a Telegram bot designed specifically for playing the Codenames board game.\
Key aspects of this project include:

1. Developed using Python.
2. Utilizes the [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) package to interact with the Telegram API.
3. Interacts with [the-spymaster-backend](https://github.com/asaf-kali/the-spymaster-backend) service for game state and opponent solvers (using the `the-spymaster-api` package).
4. Persistence of conversation state achieved through `DynamoDB`.
5. Deployed on AWS infrastructure using `Terraform`.
6. Operates on AWS `Lambda`, triggered via `API Gateway`.
7. Continuous delivery and linting pipeline using `GitHub Actions`.
