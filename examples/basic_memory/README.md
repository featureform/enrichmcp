# Basic Memory Example

This example ships with a tiny note storage implementation found in
`memory.py`. Notes are stored as Markdown files with YAML front matter using
`FileMemoryStore`. Everything lives in the `data` directory so you can open and
edit the notes by hand. Listing notes only returns their IDs and titles with
simple pagination.

```bash
cd basic_memory
python app.py
```
