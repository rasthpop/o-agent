from app.data.maindb import InvestigationDB
from app.tools.image_to_text.image_to_text import extract_json_description_and_metadata
from app.agents.planner import PlannerAgent
from anthropic import Anthropic
from app.config import settings
from app.agents.detective import Detective

from app.tools.maindb_tool import MainDBTool
from app.tools.web_search import WebSearchTool
from app.tools.web_scraper import WebScraperTool
from app.tools.osm_search import OSMLookupTool
from app.tools.plonkit_search.plonkit_search import PlonkitSearchTool

client = Anthropic(api_key=settings.anthropic_api_key)
def main():
    print("Hello from o-agent!")

def run_test_loop():


    PATH = "app/images/col.HEIC"
    print(f"Running test loop with image: {PATH}")
    features, img, metadata = extract_json_description_and_metadata(PATH)
    print("Extracted features:")
    print(features)
    print("Extracted metadata:")
    print(metadata)


    db = InvestigationDB(
        initial_photo=PATH,
        initial_text=features,
        metadata=metadata
    )

    planner = PlannerAgent(client, db, model=settings.default_model)
    agent = Detective(tools = [MainDBTool(db), WebSearchTool(), WebScraperTool(), OSMLookupTool(), PlonkitSearchTool()])
    planner_response = planner.plan(db)
    print("Planner response:")
    print(planner_response)

    print("\nStarting detective agent execution...")

    detective_response = agent.investigate_with_plan(planner_response)

    print("\n" + "="*60)
    print("INVESTIGATION COMPLETE")
    print("="*60)
    print(f"Status: {detective_response['status']}")
    print(f"Total Steps: {detective_response['total_steps']}")
    print(f"Iterations: {detective_response['iterations']}")

    if detective_response['error']:
        print(f"Error: {detective_response['error']}")

    print("\n--- EXECUTION LOG ---")
    for log in detective_response['execution_log']:
        print(f"\nIteration {log['iteration']}:")
        print(f"  Reasoning: {log['agent_reasoning'][:200]}...")
        print(f"  Tool Calls: {len(log['tool_calls'])}")
        for tc in log['tool_calls']:
            status = "✓" if tc['success'] else "✗"
            print(f"    {status} {tc['tool_name']}: {tc['error'] if tc['error'] else 'Success'}")

    print("\n--- FINAL RESPONSE ---")
    print(detective_response['final_response'])


if __name__ == "__main__":
    main()
    run_test_loop()
