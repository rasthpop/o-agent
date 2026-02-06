# OSINT Agent

Multi-agent OSINT system that autonomously plans investigations, collects open-source intelligence, validates findings, and generates structured reports.

## Features

- Investigation planning agent
- Multi-source OSINT data collection
- Fact validation & correlation
- Explainable intelligence reporting

---

## Setup


`git clone https://github.com/rasthpop/o-agent`

`python -m venv venv`
`source venv/bin/activate`
`pip install -r requirements.txt`
`playwright install`


Create `.env` file:
`ANTHROPIC_API_KEY=your_key`



Run:
`python main.py`