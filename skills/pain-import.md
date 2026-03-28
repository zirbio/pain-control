---
name: pain-import
description: Import Apple Health data from XML export files in the data/imports directory
---

# Apple Health Import

## Process

1. Check for XML files:
   ```bash
   ls -la data/imports/*.xml 2>/dev/null
   ```

2. If files found, trigger import:
   ```bash
   curl -X POST http://localhost:8000/api/imports/apple-health
   ```

3. Report results: files processed, days imported, any errors.

4. Suggest running `/pain-report` to see updated data.
