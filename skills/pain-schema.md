---
name: pain-schema
description: View and manage the evolving data schema — show active fields, extras in use, promote frequent extras to formal fields
---

# Schema Management

## Show current schema

Query the database for all table structures and extras in use:

```bash
curl -s http://localhost:8000/api/entries?limit=1 | python3 -c "
import json, sys
entry = json.load(sys.stdin)
if isinstance(entry, list) and entry:
    entry = entry[0]
    for key in entry:
        if isinstance(entry[key], list):
            print(f'{key}: {len(entry[key])} records')
        else:
            print(f'{key}: {entry[key]}')
"
```

## Show extras usage

```bash
curl -s "http://localhost:8000/api/entries?limit=365" | python3 -c "
import json, sys
from collections import Counter
entries = json.load(sys.stdin)
extras = Counter()
for e in entries:
    for x in e.get('extras', []):
        extras[x['key']] += 1
for key, count in extras.most_common():
    flag = ' → PROMOTE?' if count >= 5 else ''
    print(f'{key}: {count} occurrences{flag}')
"
```

## Promoting a field

When the user approves promotion of an extra field:
1. Generate and run an Alembic migration to add the new column
2. Migrate historical data from extras to the new column
3. Update the pain-checkin skill to include this field
