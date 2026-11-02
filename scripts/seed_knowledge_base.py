from pathlib import Path

from app import db


def parse(path: Path) -> list[tuple[str, str, str]]:
    """Split a section file into (section, title, content) rows, one per ## heading."""
    entries = []
    for block in path.read_text(encoding="utf-8").split("\n## ")[1:]:
        title, _, content = block.partition("\n")
        entries.append((path.stem, title.strip(), content.strip()))
    return entries


with db.connect() as conn:
    for path in sorted(Path("knowledge_base").glob("*.md")):
        rows = parse(path)
        for section, title, content in rows:
            conn.execute(
                """
                insert into knowledge_base (section, title, content) values (%s, %s, %s)
                on conflict (section, title) do update
                  set content = excluded.content, updated_at = now()
                """,
                (section, title, content),
            )
        print(f"{path.stem}: {len(rows)} entries")
