# HFR API

A Python library to interface with [forum.hardware.fr](https://forum.hardware.fr).

## Installation

You can install the package using pip:

```bash
pip install hfr-api
```

## Usage

### Browsing a Category

You can browse topics in a specific category.

```python
from hfr import Category

# Initialize a category (e.g., category 13 for "Discussions")
# See hfr/category.py for a mapping of category IDs
category = Category(13)

# Load the first page of topics
category.load_page(1)

# Iterate through the topics found on that page
for topic in category.topics:
    print(f"Topic ID: {topic.post}, Sticky: {topic.sticky}")
    # Note: Topic title is not available until the topic itself is loaded
```

### Reading a Topic

You can access messages within a topic.

```python
from hfr import Topic

# Initialize a topic with: Category ID, Subcategory ID, Post ID
topic = Topic(cat=13, subcat=432, post=73768)

# Load the first page of the topic
topic.load_page(1)

print(f"Title: {topic.title}")

# Iterate through messages
# Messages are grouped by date (YYYY-MM-DD)
for date_str, messages_dict in topic.messages.items():
    print(f"--- Date: {date_str} ---")
    for msg_id, message in messages_dict.items():
        print(f"[{message.posted_at}] {message.author}:")
        print(message.text)
        print("-" * 20)
```


## CLI

The package includes a command-line interface to interact with the forum.

### Installation

You can install the CLI tool using `uv` or `pipx`:

```bash
uv tool install hfr-api
# or
pipx install hfr-api
```

Once installed, the `hfr` command will be available in your path.

### Get Topic Info

Retrieve metadata about a topic as JSON.

```bash
hfr info <cat> <subcat> <post>
# Example
hfr info 13 432 73768
```

### Dump Topic Content

Dump all messages from a topic (or a specific page) to JSON.

```bash
hfr dump <cat> <subcat> <post> <output_file> [--page <page_number>]

# Example: Dump all pages to a file
hfr dump 13 432 73768 my_topic.json

# Example: Dump all pages to stdout
hfr dump 13 432 73768 - > my_topic.json

# Example: Dump only page 1 to a file
hfr dump 13 432 73768 page1.json --page 1
```

## Features

- **Categories**: List topics within a forum category.
- **Topics**: Read messages, retrieve metadata (page count, dates).
- **Messages**: Parse content including BBCode strings.
- **Parsers**: Handles HTML parsing from the forum.

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](LICENSE)
