# Repository Instructions

## Savegame Format Safety

The existing savegame transformation behavior is a compatibility contract. Refactoring may rename variables and functions, improve structure, and remove empty comment-only lines, but it must not change or invent what is matched, edited, or written to `.eu4` files.

Preserve the exact match conditions, replacement values, tab indentation, spaces, line endings, `cp1252` output encoding, and `_mod.eu4` output naming unless the user explicitly approves a behavioral change. Keep characterization tests that compare representative edited saves byte for byte when modifying transformation code.
