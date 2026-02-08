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
    path = "app/images/podatkova.jpg"
    print(f"Running test loop with image: {path}")
    features, _, metadata = extract_json_description_and_metadata(path)
    print("Extracted features:")
    print(features)
    print("Extracted metadata:")
    print(metadata)

    db = InvestigationDB(initial_photo=path, initial_text=features, metadata=metadata)

    planner = PlannerAgent(client, db, model=settings.default_model)
    detective = Detective(
        db=db,
        tools=[
            MainDBTool(db),
            WebSearchTool(),
            WebScraperTool(),
            OSMLookupTool(),
            PlonkitSearchTool(),
        ],
    )
    summarizer = Summarizer(client, db, model=settings.default_model)

    max_outer_loops = 5  # Maximum number of planner-detective-summarizer cycles
    investigation_complete = False
    outer_iteration = 0
    final_summary = None

    print("\n" + "=" * 80)
    print("STARTING INVESTIGATION PIPELINE")
    print("=" * 80)

    while not investigation_complete and outer_iteration < max_outer_loops:
        outer_iteration += 1

        print(f"\n{'=' * 80}")
        print(f"PIPELINE CYCLE {outer_iteration}/{max_outer_loops}")
        print(f"{'=' * 80}")

        print("\n[PHASE 1: PLANNER]")
        print("Analyzing investigation state and creating plan...")
        planner_response = planner.plan(iteration=outer_iteration - 1)

        print(f"  Plan created with {len(planner_response.get('next_steps', []))} steps")
        print(f"  State summary: {planner_response.get('state', '')[:200]}...")

        # Check if planner indicates investigation is complete
        if not planner_response.get("next_steps"):
            print("\n✓ PLANNER: No more investigation steps needed. Investigation complete.")
            investigation_complete = True
            break


        print("\n[PHASE 2: DETECTIVE]")
        print("Executing investigation plan (max 10 iterations per cycle)...")
        detective_response = detective.investigate_with_plan(planner_response, max_iterations=10)

        print("\n  Detective execution complete:")
        print(f"  Status: {detective_response['status']}")
        print(f"  Iterations used: {detective_response['iterations']}/10")
        print(f"  Plan steps: {detective_response['total_steps']}")

        if detective_response["status"] == "partial":
            print(" Warning: Detective hit iteration limit before completing all steps")
        elif detective_response["status"] == "error":
            print(f"Error: {detective_response.get('error', 'Unknown error')}")

        print("\n  Tool usage summary:")
        for log in detective_response["execution_log"]:
            tool_summary = ", ".join([tc["tool_name"] for tc in log["tool_calls"]])
            print(f"Iteration {log['iteration']}: [{tool_summary}]")

        final_response = detective_response.get("final_response", "")
        if final_response:
            print(f"\n  Detective's summary: {final_response[:300]}...")

        print("\n[PHASE 3: SUMMARIZER]")
        print("Extracting key findings and checking for redundancy...")

        summary = summarizer.summarize(detective_response, check_similarity=True)

        print("Summary generated:")
        print(f"  Overview: {summary.get('summary', 'N/A')[:150]}...")
        print(f"  Key points: {len(summary.get('key_points', []))}")
        print(f"  Similarity score: {summary.get('similarity_score', 0.0):.2f}")
        print(f"  Is redundant: {summary.get('is_redundant', False)}")

        if summary.get("key_points"):
            print("\n  Key findings this iteration:")
            for i, point in enumerate(summary.get("key_points", [])[:3], 1):
                category = point.get("category", "unknown")
                finding = point.get("finding", "")[:80]
                confidence = point.get("confidence", "unknown")
                print(f"{i}. [{category}] {finding}... (confidence: {confidence})")

        if summary.get("is_redundant", False):
            print("\n" + "!" * 80)
            print("STOP CONDITION MET: FINDINGS ARE REDUNDANT")
            print("Investigation has converged - no new meaningful progress detected.")
            print("!" * 80)
            investigation_complete = True
            final_summary = summary
            db.add_summary(summary)
            break

        db.add_summary(summary)
        final_summary = summary
        print(f" Summary saved to database ({len(db.get_summaries())} total summaries)")

        print(
            f"\n[PIPELINE] Cycle {outer_iteration} complete. "
            "Findings show progress - continuing to next iteration."
        )

    # ===== FINAL SUMMARY =====
    print("\n" + "=" * 80)
    print("INVESTIGATION PIPELINE COMPLETE")
    print("=" * 80)
    print(f"Total pipeline cycles: {outer_iteration}/{max_outer_loops}")

    if investigation_complete:
        stop_reason = "Redundancy detected (findings converged)"
    else:
        stop_reason = "Maximum cycles reached"
    print(f"Stop reason: {stop_reason}")

    if final_summary:
        print("\n" + "=" * 80)
        print("FINAL INVESTIGATION SUMMARY")
        print("=" * 80)

        print("\nOverall Summary:")
        print(f"  {final_summary.get('summary', 'N/A')}")

        print("\n--- KEY FINDINGS ---")
        for i, point in enumerate(final_summary.get("key_points", []), 1):
            print(f"\n{i}. [{point.get('category', 'unknown').upper()}]")
            print(f"   Finding: {point.get('finding', '')}")

        print("\n--- LOCATION GUESS ---")
        point = final_summary.get("final_guess", [])
            
        print(f"   Coordinates: {point.get('latitude', '')} {point.get('longitude', '')}")
        print(f"   Confidence radius: {point.get('confidence_radius_km', '')}")
        print(f"   Location name: {point.get('location_name', '')}")
        print(f"   Reasoning: {point.get('reasoning', '')}")

        if final_summary.get("next_actions"):
            print("\n--- RECOMMENDED NEXT ACTIONS ---")
            for i, action in enumerate(final_summary.get("next_actions", []), 1):
                print(f"{i}. {action}")

        # Display investigation progression
        all_summaries = db.get_summaries()
        print("\n--- INVESTIGATION PROGRESSION ---")
        print(f"Total summaries: {len(all_summaries)}")
        for idx, summ in enumerate(all_summaries):
            print(
                f"  Iteration {idx}: {summ.get('summary', 'N/A')[:200]}... "
            )

    print("\n--- DATABASE STATE ---")
    print(f"Validated searches: {len(db.get_validated_searches())}")
    print(f"Summaries: {len(db.get_summaries())}")
    print(f"User corrections: {len(db.get_wrongs())}")
    print(f"Context hints: {len(db.get_context())}")

    return final_summary


if __name__ == "__main__":
    main()
    run_test_loop()
