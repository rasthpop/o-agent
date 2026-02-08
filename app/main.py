from anthropic import Anthropic

from app.agents.detective import Detective
from app.agents.planner import PlannerAgent
from app.agents.summarizer import Summarizer
from app.config import settings
from app.data.maindb import InvestigationDB
from app.tools.image_to_text.image_to_text import extract_json_description_and_metadata
from app.tools.maindb_tool import MainDBTool
from app.tools.osm_search import OSMLookupTool
from app.tools.plonkit_search.plonkit_search import PlonkitSearchTool
from app.tools.web_scraper import WebScraperTool
from app.tools.web_search import WebSearchTool

client = Anthropic(api_key=settings.anthropic_api_key)


def main():
    print("Hello from o-agent!")


def run_test_loop():

    path = "app/images/20230920_081157.jpg"
    print(f"Running test loop with image: {path}")
    features, img, metadata = extract_json_description_and_metadata(path)
    print("Extracted features:")
    print(features)
    print("Extracted metadata:")
    print(metadata)

    db = InvestigationDB(initial_photo=path, initial_text=features, metadata=metadata)

    planner = PlannerAgent(client, db, model=settings.default_model)
    agent = Detective(
        tools=[
            MainDBTool(db),
            WebSearchTool(),
            WebScraperTool(),
            OSMLookupTool(),
            PlonkitSearchTool(),
        ]
    )
    summarizer = Summarizer(client, db, model=settings.default_model)

    planner_response = planner.plan(db)
    print("Planner response:")
    print(planner_response)

    print("\nStarting detective agent execution...")

    detective_response = agent.investigate_with_plan(planner_response)

    print("\n" + "=" * 60)
    print("INVESTIGATION COMPLETE")
    print("=" * 60)
    print(f"Status: {detective_response['status']}")
    print(f"Total Steps: {detective_response['total_steps']}")
    print(f"Iterations: {detective_response['iterations']}")

    if detective_response["error"]:
        print(f"Error: {detective_response['error']}")

    print("\n--- EXECUTION LOG ---")
    for log in detective_response["execution_log"]:
        print(f"\nIteration {log['iteration']}:")
        print(f"  Reasoning: {log['agent_reasoning'][:200]}...")
        print(f"  Tool Calls: {len(log['tool_calls'])}")
        for tc in log["tool_calls"]:
            status = "✓" if tc["success"] else "✗"
            print(f"    {status} {tc['tool_name']}: {tc['error'] if tc['error'] else 'Success'}")

    print("\n--- FINAL RESPONSE ---")
    print(detective_response["final_response"])

    # Generate summary with key points
    print("\n" + "=" * 60)
    print("GENERATING SUMMARY")
    print("=" * 60)

    summary = summarizer.summarize(detective_response, check_similarity=True)

    print(f"\nSummary: {summary.get('summary', 'N/A')}")
    print(f"Similarity Score: {summary.get('similarity_score', 0.0):.2f}")
    print(f"Is Redundant: {summary.get('is_redundant', False)}")

    print("\n--- KEY POINTS ---")
    for i, point in enumerate(summary.get("key_points", []), 1):
        print(f"{i}. [{point.get('category', 'unknown')}] {point.get('finding', '')}")
        confidence = point.get("confidence", "unknown")
        source = point.get("source", "unknown")
        print(f"   Confidence: {confidence} | Source: {source}")

    if summary.get("next_actions"):
        print("\n--- NEXT ACTIONS ---")
        for i, action in enumerate(summary.get("next_actions", []), 1):
            print(f"{i}. {action}")

    # Save summary to database only if not redundant
    if not summary.get("is_redundant", False):
        db.add_summary(summary)
        print("\n✓ Summary saved to database")
    else:
        print("\n⚠ Summary not saved (too similar to previous findings)")


if __name__ == "__main__":
    main()
    run_test_loop()
