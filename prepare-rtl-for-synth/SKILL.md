---
name: prepare-rtl-for-synth
description: Prepare Verilog/SystemVerilog RTL for synthesis. Use when adapting handwritten or generated RTL for Yosys, yosys-slang, Verilator, sv-lang, Design Compiler, VCS, or similar EDA flows; handling Chisel/FIRRTL/firtool generated code; making syntax compatibility changes; inspecting memory compiler SRAM outputs; preparing macro replacement manifests; or running syntax, lint, hierarchy, and synthesis-front-end checks.
---

# Prepare RTL for Synthesis

## Overview

Prepare RTL for a target synthesis or lint flow without changing described hardware behavior. Use two tracks: syntax compatibility and macro replacement preparation.

## Workflow

1. Gather the target flow, top, file order, includes, defines, generated-code source, memory compiler outputs, and existing scripts; choose one or both tracks.
2. Prefer build/generator options over hand-editing generated RTL, and keep edits behavior-preserving and narrow.
3. Validate with the parser closest to the downstream flow; for Yosys, prioritize yosys-slang/Yosys and confirm `SYNTHESIS` behavior.
4. Report modified paths, commands/results, and unresolved semantic assumptions.

## Anti Patterns

- Do not modify RTL behavior or functionality; the described hardware circuit should remain equivalent.
- Do not use broad rewrites for local syntax/config issues, or automatically replace every behavioral memory.
- Do not guess tool options or trust the most permissive parser as downstream compatibility proof.
- Do not add memory compiler generated Verilog models to the synthesis RTL filelist; add the corresponding library in the synthesis script instead, or the netlist may retain macro module parameters.
- Do not delete, gate, or comment simulation/debug code blindly.

## Track 1: Syntax Compatibility Changes

Use when RTL fails to parse, elaborate, lint, or enter the synthesis frontend because of syntax, generated-code style, defines, includes, packages, unsupported constructs, or tool dialect differences.

- Read `references/syntax-compatibility.md` for parser choice, cross-check policy, Yosys/yosys-slang caveats, debug print handling, and check command templates.
- Read `references/chisel-generated-rtl.md` when the source is Chisel/FIRRTL/firtool generated.
- Return the exact compatibility changes made and the check commands/results.

## Track 2: Macro Replace Preparation

Use when preparing RTL to instantiate memory compiler macros, SRAMs, or blackbox memory modules. Do not assume every behavioral memory should be replaced.

- Read `references/macro-replace-prep.md` for the manifest shape, mapping checklist, width mismatch workarounds, and wrapper replacement guidance.
- Read `references/chisel-generated-rtl.md` before replacing memories in Chisel/FIRRTL/firtool output.
- Use `scripts/extract_memory_ports.py` for memory compiler port inventory.
- Return the prepared manifest/config changes and unresolved macro semantic assumptions.

## Bundled Resources

- `references/syntax-compatibility.md`: parser selection, Yosys/yosys-slang caveats, debug prints, and check templates.
- `references/macro-replace-prep.md`: macro manifest and SRAM mapping checks.
- `references/chisel-generated-rtl.md`: Chisel/FIRRTL/firtool notes, `.conf` files, and CIRCT codegen options.
- `scripts/extract_memory_ports.py`: memory compiler module port inventory.
