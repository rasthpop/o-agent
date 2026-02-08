"""Example usage of PlonkitSearchTool for detective agent."""

from app.tools.plonkit_search.plonkit_search import PlonkitSearchTool


def example_basic_search():
    """Example: Basic keyword search."""
    print("=" * 60)
    print("Example 1: Basic keyword search")
    print("=" * 60)

    tool = PlonkitSearchTool()

    # Search for yellow license plates
    result = tool.execute(keywords=["yellow license plate", "yellow plate"])

    if result.success:
        print(f"Found {result.data['total_matches']} countries")
        for country_result in result.data["results"][:3]:  # Show top 3
            print(f"\n{country_result['country']} ({country_result['code']})")
            print(f"  Matched keywords: {country_result['matched_keywords']}")
            print(f"  Number of matching sections: {country_result['match_count']}")
    else:
        print(f"Search failed: {result.error}")


def example_multi_feature_search():
    """Example: Search with multiple visual features."""
    print("\n" + "=" * 60)
    print("Example 2: Multi-feature search")
    print("=" * 60)

    tool = PlonkitSearchTool()

    # Searching for Cyrillic script + red soil + wooden poles
    result = tool.execute(keywords=["cyrillic", "red soil", "wooden poles"], max_results=5)

    if result.success:
        print(f"Found {result.data['total_matches']} countries")
        for country_result in result.data["results"]:
            print(f"\n{country_result['country']}:")
            print(f"  Matched: {', '.join(country_result['matched_keywords'])}")
    else:
        print(f"Search failed: {result.error}")


def example_filtered_search():
    """Example: Search within specific countries."""
    print("\n" + "=" * 60)
    print("Example 3: Filtered search (South American countries)")
    print("=" * 60)

    tool = PlonkitSearchTool()

    # Search only in South American countries
    result = tool.execute(
        keywords=["red soil", "wooden poles"],
        country_filter=["Argentina", "Brazil", "Chile", "Peru", "Bolivia"],
        max_results=5,
    )

    if result.success:
        print(f"Found {result.data['total_matches']} matching countries")
        for country_result in result.data["results"]:
            print(f"\n{country_result['country']}:")
            for section in country_result["sections"][:1]:  # Show first section
                print(f"  Section: {section['title']}")
                # Print first 200 chars of description
                desc = section["description"][:200] + "..."
                print(f"  {desc}")
    else:
        print(f"Search failed: {result.error}")


def example_architecture_search():
    """Example: Search for architecture patterns."""
    print("\n" + "=" * 60)
    print("Example 4: Architecture search")
    print("=" * 60)

    tool = PlonkitSearchTool()

    result = tool.execute(
        keywords=["orange tiled roofs", "pastel colours", "balconies"], max_results=5
    )

    if result.success:
        print(f"Found {result.data['total_matches']} countries")
        for country_result in result.data["results"]:
            print(f"  - {country_result['country']}: {len(country_result['sections'])} sections")
    else:
        print(f"Search failed: {result.error}")


if __name__ == "__main__":
    example_basic_search()
    example_multi_feature_search()
    example_filtered_search()
    example_architecture_search()
