import json
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

from .topic import Topic

app = typer.Typer()
# Use stderr for logging/progress so distinct from data output if directed to stdout
err_console = Console(stderr=True)
console = Console()


@app.command()
def info(cat: int, subcat: int, post: int):
    """
    Get info about a topic.
    """
    topic = Topic(cat=cat, subcat=subcat, post=post)
    try:
        with err_console.status("[bold green]Fetching topic info..."):
            topic.load_page(1)
        console.print_json(data=topic.to_dict())
    except Exception as e:
        err_console.print(f"[bold red]Error:[/bold red] {e}")


@app.command()
def dump(
    cat: int,
    subcat: int,
    post: int,
    output: str = typer.Argument(..., help="Output file path, or '-' for stdout."),
    page: Optional[int] = typer.Option(None, help="Specific page to dump. If not provided, dumps all pages."),
):
    """
    Dump the content of a topic (all messages).
    """
    topic = Topic(cat=cat, subcat=subcat, post=post)
    try:
        # Load first page to get metadata
        with err_console.status("[bold green]Fetching metadata and page 1..."):
            topic.load_page(1)

        if page is not None:
            if page != 1:
                # If specific page needed and it wasn't 1, load it specifically
                with err_console.status(f"[bold green]Fetching page {page}..."):
                    topic = Topic(cat=cat, subcat=subcat, post=post)
                    topic.load_page(page)
        elif topic.max_page > 1:
            # All pages
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=err_console
            ) as progress:
                task = progress.add_task(f"[cyan]Downloading {topic.max_page} pages...", total=topic.max_page)
                progress.update(task, completed=1) # We already have page 1
                
                for p in range(2, topic.max_page + 1):
                    topic.load_page(p)
                    progress.update(task, advance=1)

        # Construct data
        data = topic.to_dict()
        data["messages"] = []
        for date_str, messages_by_id in topic.messages.items():
            for msg_id, message in messages_by_id.items():
                data["messages"].append(message.to_dict())
        
        # Output
        if output == "-":
            console.print_json(data=data)
        else:
            with open(output, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            err_console.print(f"[bold green]Successfully wrote {len(data['messages'])} messages to {output}[/bold green]")

    except Exception as e:
        err_console.print(f"[bold red]Error:[/bold red] {e}")


if __name__ == "__main__":
    app()
