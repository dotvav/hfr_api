import json
from enum import Enum
from typing import Optional

import typer
from rich.console import Console
from rich.syntax import Syntax

from .topic import Topic

app = typer.Typer()
console = Console()


@app.command()
def info(cat: int, subcat: int, post: int):
    """
    Get info about a topic.
    """
    topic = Topic(cat=cat, subcat=subcat, post=post)
    try:
        topic.load_page(1)
        console.print_json(data=topic.to_dict())
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


@app.command()
def dump(
    cat: int,
    subcat: int,
    post: int,
    page: Optional[int] = typer.Option(None, help="Specific page to dump. If not provided, dumps all pages."),
):
    """
    Dump the content of a topic (all messages).
    """
    topic = Topic(cat=cat, subcat=subcat, post=post)
    try:
        # Load first page to get metadata (and content if page 1 is requested or all pages)
        res = topic.load_page(1)
        
        # If a specific page is requested and it's not 1, we need to clear and reload
        if page is not None:
            if page != 1:
                # Re-initialize or just clear messages? Topic accumulates messages.
                # But load_page(1) was needed to get max_page potentially? 
                # Actually topic logic adds messages.
                # If we only want page X, we should probably start fresh if X != 1, 
                # but we needed X=1 to know if X is valid? 
                # Let's just load the requested page. If page is passed, we trust user or we check max_page after load.
                # However, Topic.load_page implementation sleeps and fetches.
                # If we want ONLY page X, we should have avoided loading page 1 if possible, 
                # but we usually need metadata from page 1? 
                # The prompt says "result is the json serialization of the content of the topic (respectively the 1 page)"
                # which implies if page is specified, dump that page.
                
                # If we loaded page 1, we have messages from page 1.
                # If user wants page 2, we should probably discard page 1 messages if "dump that page" means ONLY that page.
                # But the Topic class accumulates.
                # Let's create a new topic instance to be clean if page != 1
                 topic = Topic(cat=cat, subcat=subcat, post=post)
                 topic.load_page(page)

        else:
            # All pages
            # We already loaded page 1.
            # topic.max_page should be set.
            for p in range(2, topic.max_page + 1):
                topic.load_page(p)

        # Construct the output structure
        # The prompt asks for "json serialization of the content of the topic ... including all the messages"
        # topic.to_dict only gives metadata. We need to add messages.
        
        data = topic.to_dict()
        data["messages"] = []
        
        # topic.messages is a dict of date -> dict of id -> Message
        for date_str, messages_by_id in topic.messages.items():
            for msg_id, message in messages_by_id.items():
                data["messages"].append(message.to_dict())

        console.print_json(data=data)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


if __name__ == "__main__":
    app()
