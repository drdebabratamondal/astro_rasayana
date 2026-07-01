# Astro Rasayana: Multi Agent Space Medicine System

This project builds a data driven bridge between traditional medicine and aerospace biology. Synthetic pharmaceuticals degrade rapidly during space travel due to cosmic radiation. Long duration missions require self sustaining biological countermeasures. This architecture automates drug discovery by proving specific herbs possess the biochemical compounds required to treat cellular degradation in microgravity.

This repository provides the complete source code so you can reproduce the automated drug discovery pipeline. 

## System Orchestration

The system deploys three distinct Model Context Protocol servers orchestrated by a Supervisor Agent.

*   **The Botanist Agent:** Extracts classical Rasayana herbs and active compounds from a structured Himalayan flora dataset.
*   **The Clinician Agent:** Queries the live PubMed API to validate these compounds against modern clinical trials targeting oxidative stress.
*   **The Flight Surgeon Agent:** Queries the NASA GeneLab API to retrieve aerospace datasets related to microgravity stress factors.

The Supervisor Agent enforces the Triangulation Mandate. It refuses to recommend a botanical countermeasure unless it successfully links a Rasayana herb, a verified PubMed clinical trial, and a NASA GeneLab dataset. 

## A. Installation

You must install Python 3.10 or higher. 

### 1. Clone this repository to your local machine.

```
git clone [https://github.com/drdebabratamondal/astro_rasayana.git](https://github.com/drdebabratamondal/astro_rasayana.git)
cd astro_rasayana
```

### 2. Install the required dependencies.

PowerShell

```
pip install -r requirements.txt
```

### 3.Create a `.env` file in the root directory. Add your Google Gemini API key.

Plaintext

```
GEMINI_API_KEY="your_api_key_here"
```

## B. Execution

### 1. Run the supervisor script to start the multi-agent pipeline.

PowerShell

```
python agents/supervisor.py
```

The terminal will output a statistical therapeutic viability report confirming the efficacy of specific plants for spaceflight application.

## About the Author

Dr. Debabrata Mondal is an Ayurvedic Physician. This project scales clinical methodologies used for scientific validation of traditional formulations into aerospace applications.

--------------
