import argparse
from pathlib import Path

from langgraph_email.workflow.graph import build_graph


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export the email workflow diagram."
    )
    parser.add_argument(
        "--png",
        action="store_true",
        help="Also render a PNG using the Mermaid.ink service.",
    )
    arguments = parser.parse_args()

    graph = build_graph()
    diagram = graph.get_graph()

    project_root = Path(__file__).resolve().parents[1]
    output_directory = project_root / "docs"
    output_directory.mkdir(parents=True, exist_ok=True)

    markdown_path = output_directory / "email-workflow.md"

    markdown_path.write_text(
        "# Email workflow\n\n"
        "```mermaid\n"
        + diagram.draw_mermaid()
        + "\n```\n",
        encoding="utf-8",
    )

    print("Markdown diagram saved:", markdown_path)

    if arguments.png:
        png_path = output_directory / "email-workflow.png"

        try:
            png_path.write_bytes(diagram.draw_mermaid_png())
        except Exception as error:
            print(f"PNG rendering failed: {type(error).__name__}.")
            print("The Markdown diagram is still available.")
        else:
            print("PNG diagram saved:", png_path)


if __name__ == "__main__":
    main()