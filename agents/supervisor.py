import os
from dotenv import load_dotenv
load_dotenv()
from google import genai
from google.genai import types

# Import your local tool functions
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from mcp_servers.botanist import filter_rasayana_herbs
from mcp_servers.clinician import search_pubmed_clinical_trials
from mcp_servers.flight_surgeon import search_genelab_biomarkers

def run_supervisor():
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    system_instruction = (
        "You are the Astro Pharmacognosy Supervisor Agent. "
        "Your mission is to formulate biological countermeasures for spaceflight oxidative stress. "
        "You must enforce the Triangulation Mandate. You cannot recommend a botanical countermeasure "
        "unless you successfully link a Rasayana herb, a verified PubMed clinical trial, and a NASA GeneLab dataset. "
        "Follow these steps exactly. "
        "First, call the botanist tool to get Rasayana herbs from the CSV. "
        "Second, call the clinician tool to find PubMed trials for those specific herbs regarding oxidative stress. "
        "Third, call the flight surgeon tool to find NASA GeneLab datasets for oxidative stress. "
        "Finally, synthesize this data into a statistical therapeutic viability report."
    )

    # Pass the functions directly to the SDK
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=[filter_rasayana_herbs, search_pubmed_clinical_trials, search_genelab_biomarkers],
        temperature=0.2
    )

    print("Initializing Supervisor Agent...")
    print("Enforcing Triangulation Mandate...")
    print("Executing multi agent tool calls... Please wait.\n")
    
    # Use a chat session for automatic tool calling
    chat = client.chats.create(model='gemini-2.5-flash', config=config)
    response = chat.send_message("Begin the Astro Pharmacognosy analysis using data/himalayan_flora.csv and target oxidative stress.")
    
    print("=== FINAL ASTRO PHARMACOGNOSY REPORT ===")
    print(response.text)

if __name__ == "__main__":
    run_supervisor()