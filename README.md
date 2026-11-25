# A(muni)tion

predict buses from your terminal with ease

## Introduction

A(muni)tion is a transit app running on the bay's* 511 API. With it, you can easily determine when the next bus will arrive at the stop of your choosing. You can also search
for lines and operators.

## Installation

To begin using A(muni)tion, you will have to download it via PyPI. For this example, I will be using `uv`.

`uv tool install amunition`

After this, you will have to get an API key from [511](https://511.org/open-data/token). (this will take a few days)

At first run, A(muni)tion will say `KEY_511 not found in ~/.amunition, please set it using 'key <your-key>'.`

To fix this, type `> key <your-valid-key>`. If the key is valid, it will exit and you will have to start A(muni)tion again.

## Footnotes

A(muni)tion is NOT affiliated with the MTC, 511, SFMTA, or any other transit agency.
(c) 2026 goldcoin10

*not chesapeake ffs