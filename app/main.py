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
    PATH = "app/images/cem.jpg"
    print(f"Running test loop with image: {PATH}")
    features, _, metadata = extract_json_description_and_metadata(PATH)
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
    detective = Detective(db=db, tools=[MainDBTool(db), WebSearchTool(), WebScraperTool(), OSMLookupTool(), PlonkitSearchTool()])

    MAX_OUTER_LOOPS = 10  # Maximum number of planner-detective-[guesser] cycles
    investigation_complete = False
    outer_iteration = 0

    print("\n" + "="*80)
    print("STARTING INVESTIGATION PIPELINE")
    print("Architecture: PLANNER → DETECTIVE → [GUESSER - TBD] → PLANNER")
    print("="*80)

    while not investigation_complete and outer_iteration < MAX_OUTER_LOOPS:
        outer_iteration += 1

        print(f"\n{'='*80}")
        print(f"PIPELINE CYCLE {outer_iteration}/{MAX_OUTER_LOOPS}")
        print(f"{'='*80}")

        # ===== PHASE 1: PLANNER =====
        # Planner analyzes current state and creates investigation strategy
        print(f"\n[PHASE 1: PLANNER]")
        print(f"Analyzing investigation state and creating plan...")
        planner_response = planner.plan(iteration=outer_iteration-1)

        print(f"✓ Plan created with {len(planner_response.get('next_steps', []))} steps")
        print(f"  State summary: {planner_response.get('state', '')[:200]}...")

        # Check if planner indicates investigation is complete
        if not planner_response.get('next_steps'):
            print("\n✓ PLANNER: No more investigation steps needed. Investigation complete.")
            investigation_complete = True
            break

        # ===== PHASE 2: DETECTIVE =====
        # Detective executes plan within iteration limit (max 10 iterations)
        # Detective is self-contained and must complete within its iteration budget
        print(f"\n[PHASE 2: DETECTIVE]")
        print(f"Executing investigation plan (max 10 iterations per cycle)...")
        detective_response = detective.investigate_with_plan(planner_response, max_iterations=10)

        # Detective execution summary
        print(f"\n✓ Detective execution complete:")
        print(f"  Status: {detective_response['status']}")
        print(f"  Iterations used: {detective_response['iterations']}/10")
        print(f"  Plan steps: {detective_response['total_steps']}")

        if detective_response['status'] == 'partial':
            print(f"  ⚠️  Warning: Detective hit iteration limit before completing all steps")
        elif detective_response['status'] == 'error':
            print(f"  ❌ Error: {detective_response.get('error', 'Unknown error')}")

        # Log tool usage per iteration
        print(f"\n  Tool usage summary:")
        for log in detective_response['execution_log']:
            tool_summary = ", ".join([tc['tool_name'] for tc in log['tool_calls']])
            print(f"    Iteration {log['iteration']}: [{tool_summary}]")

        # Detective's final reasoning
        final_response = detective_response.get('final_response', '')
        if final_response:
            print(f"\n  Detective's summary: {final_response[:300]}...")

        # ===== PHASE 3: GUESSER (FUTURE) =====
        # TODO: Add Guesser agent here
        # Guesser will:
        # 1. Review all findings from detective (from database)
        # 2. Structure and synthesize information
        # 3. Make educated guesses about location
        # 4. Pass structured findings back to planner for next iteration
        print(f"\n[PHASE 3: GUESSER - NOT IMPLEMENTED]")
        print(f"(Future: Guesser agent will structure findings before returning to Planner)")

        # For now, findings are stored directly in database
        print(f"✓ Detective findings stored in database")
        print(f"  Validated searches: {len(db.get_validated_searches())}")

        # ===== LOOP CONTINUATION =====
        print(f"\n[PIPELINE] Cycle {outer_iteration} complete. Findings available for next planner iteration.")

    # ===== FINAL SUMMARY =====
    print("\n" + "="*80)
    print("INVESTIGATION PIPELINE COMPLETE")
    print("="*80)
    print(f"Total pipeline cycles: {outer_iteration}/{MAX_OUTER_LOOPS}")
    print(f"Investigation status: {'✓ Complete' if investigation_complete else '⚠️  Stopped at max cycles'}")

    print("\n--- FINAL DATABASE STATE ---")
    final_state = db.to_dict()
    for key, value in final_state.items():
        if isinstance(value, str):
            print(f"{key}: {value[:200]}...")
        else:
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
    run_test_loop()
