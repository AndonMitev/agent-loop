# Third-party notices

`agent-loop` bundles companion skills used by the loop tick. They are redistributed under their original
MIT licenses, with attribution below.

## addyosmani/agent-skills (MIT)
The following skills are vendored from https://github.com/addyosmani/agent-skills :
- `plugins/agent-loop/skills/doubt-driven-development`
- `plugins/agent-loop/skills/test-driven-development`
- `plugins/agent-loop/skills/debugging-and-error-recovery`

```
MIT License

Copyright (c) 2025 Addy Osmani

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Original to agent-loop
- `plugins/agent-loop/skills/grill-ai` — original (MIT, © 2026 Andon Mitev), the AI-to-AI self-interrogation
  used as the loop's critique second brain.

## Techniques adapted (concept, not code)
- The in-session **Stop-hook self-firing loop** (`hooks/stop-hook.sh` + `loop.py auto`) adapts the technique from
  Anthropic's `ralph-wiggum` plugin (https://github.com/anthropics/claude-code, MIT) — re-implemented over our
  substrate with iteration + dispatch-flip token rails.
- The **zoom-out / re-orient** rule in `loop-tick` adapts the principle from `zoom-out` in
  https://github.com/mattpocock/skills (MIT).
- The **simplicity ladder** ("stop at the first rung that holds") and the **`// shortcut: … — upgrade: …`**
  convention in `code-standards` adapt ideas from https://github.com/DietrichGebert/ponytail (MIT).

## Optional companions (not bundled)
- `handoff` and `observability-and-instrumentation` pair well with loops but aren't required by the tick.
  Sources: https://github.com/mattpocock/skills (MIT) and https://github.com/addyosmani/agent-skills (MIT).
