from app.data.maindb import InvestigationDB
from app.tools.image_to_text.image_to_text import extract_json_description_and_metadata
from app.agents.planner import PlannerAgent
from anthropic import Anthropic
from app.config import settings

client = Anthropic(api_key=settings.anthropic_api_key)
def main():
    print("Hello from o-agent!")

def run_test_loop():


    PATH = "app/images/col.jpg"
    print(f"Running test loop with image: {PATH}")
    features, img, metadata = extract_json_description_and_metadata(PATH)
    print("Extracted features:")
    print(features)
    print("Extracted metadata:")
    print(metadata)


    # db = InvestigationDB(
    #     initial_photo=PATH,
    #     initial_text=features,
    #     metadata=metadata
    # )

    # planner = PlannerAgent(client=client, model=settings.default_model)
    # planner_response = planner.plan(db)
    # print("Planner response:")
    # print(planner_response)


if __name__ == "__main__":
    main()
    run_test_loop()
