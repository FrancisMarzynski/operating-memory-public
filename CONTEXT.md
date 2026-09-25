# Context: Operating Memory (public)

Shared language from the code and README.

- **Notes root**: configured folder of source Markdown and decision-log files.
- **Entity**: durable record imported from a note, identified by kind and source-relative key.
- **Decision**: dated, append-only line associated with an entity.
- **Journal entry**: dated Markdown file used as a temporal record.
- **Import plan**: records and changes calculated from source files before an apply.
- **Memory store**: local SQLite projection of the notes; it can be recreated by importing again.
- **Dry run / apply**: explicit CLI modes for previewing or writing an import.
