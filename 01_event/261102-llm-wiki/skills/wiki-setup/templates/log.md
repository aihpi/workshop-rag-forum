# Log

Append-only record of changes to this wiki. One entry per operation, newest at the bottom, never edited afterwards. Each entry starts with `## [YYYY-MM-DD] <op> | <source> | <pages>`, so that `grep "^## \[" log.md | tail -5` shows the latest entries. One to three lines below the heading say what changed and why.
