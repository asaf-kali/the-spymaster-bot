# The Spymaster Bot

[![Pipeline](https://github.com/asaf-kali/the-spymaster-bot/actions/workflows/pipeline.yml/badge.svg)](https://github.com/asaf-kali/the-spymaster-bot/actions/workflows/pipeline.yml)

Telegram bot service for playing Codenames board game. Try it at [@the_spymaster_bot](https://t.me/the_spymaster_bot). \
Other repositories in this project:

* [codenames](https://github.com/asaf-kali/codenames) package (core game logic)
* [codenames-solvers](https://github.com/asaf-kali/codenames-solvers) package (player algorithms)
* [the-spymaster-backend](https://github.com/asaf-kali/the-spymaster-backend) service (game state and solvers API)

## Intro

Key aspects of this project include:

1. Developed using Python.
2. Utilizes the [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) package to interact
   with the Telegram API.
3. Interacts with [the-spymaster-backend](https://github.com/asaf-kali/the-spymaster-backend) service for game state
   and opponent solvers (using the `the-spymaster-api` package).
4. Persistence of conversation state achieved through `DynamoDB`.
5. Deployed on AWS infrastructure using `Terraform`.
6. Operates on AWS `Lambda`, triggered via `API Gateway`.
7. Continuous delivery and linting pipeline using `GitHub Actions`.
