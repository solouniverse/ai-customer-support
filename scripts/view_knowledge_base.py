from app import db


sections = db.list_sections()
print(f"Knowledge base: {sum(len(db.get_section(section)) for section in sections)} rows")

for section in sections:
    rows = db.get_section(section)
    print(f"\n{section}: {len(rows)} entries")
    for row in rows:
        print(f"- {row['title']}")
