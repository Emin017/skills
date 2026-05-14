# Syntax Compatibility Checks

## Lint Tool Selection

Choose the syntax/lint tool according to the user's downstream flow, not only according to the parser that accepts the most SystemVerilog.

- Use `yosys-slang` first when the user plans to synthesize with Yosys. Matching the synthesis parser catches issues that a more permissive parser may miss.
- Use `sv-lang` when the immediate goal is broad SystemVerilog syntax compatibility. It usually accepts the widest syntax subset among these choices, but its behavior may differ from commercial tools such as Design Compiler (`dc`) or VCS.
- Use `verilator` when the project already uses Verilator, when simulation-oriented lint feedback is useful, or when its supported SystemVerilog subset matches the target flow.
- If the final flow is a commercial EDA tool, prefer the project's existing lint/elaboration command for that tool when available; otherwise report that open-source lint success is only a proxy.

## Cross-Check When Possible

When the environment and task budget allow, cross-check syntax compatibility with more than one tool. Prioritize the synthesis or signoff tool the user will actually use later, because passing a different parser does not prove downstream compatibility.

If the intended commercial tool is unavailable in the current environment, use open-source tools as substitutes and report that limitation. For example, combine `sv-lang` for broad SystemVerilog parsing with `yosys-slang` when the target synthesis flow is Yosys, or add `verilator` when the project already relies on Verilator lint.

## Confirm Local Command Support

Check the local plugin first because installations differ:

```bash
yosys -m slang -p 'help read_slang'
```

If that fails but the plugin is installed through a different mechanism, try:

```bash
yosys -p 'plugin -i slang; help read_slang'
```

## Confirm `SYNTHESIS` Define Behavior

When the downstream flow is Yosys synthesis, confirm whether the installed `yosys-slang` implicitly defines `SYNTHESIS`. Yosys' built-in `read_verilog` adds implicit `-D SYNTHESIS` by default and provides `-nosynthesis` to disable it; `read_verilog -formal` replaces it with `-D FORMAL`.

`yosys-slang` only gained matching default behavior after PR #254:

https://github.com/povik/yosys-slang/pull/254

That PR merged commit `8c5b73ed2f5d7d105d2fec8ab23cfdd9c066119a` and added both:

- implicit `SYNTHESIS=1` in `read_slang`
- `--no-synthesis-define` to disable the implicit define

Check local support before relying on this behavior:

```bash
yosys -m slang -p 'help read_slang' | rg -- '--no-synthesis-define'
```

If the option is missing, assume the plugin may not define `SYNTHESIS` implicitly. For synthesis checks, pass the define explicitly:

```bash
yosys -m slang -p 'read_slang -D SYNTHESIS ...; hierarchy -check -top <top>; check'
```

If the option is present, still record the observed behavior in the task summary because OSS CAD Suite or locally built plugins may lag or differ from upstream.

## Check Debug Print and Write Statements for Yosys

When preparing RTL for Yosys synthesis, check whether the design contains uncommented debug print/write system tasks. Statements such as `$display`, `$write`, `$fwrite`, `$strobe`, `$monitor`, or `$print` can be accepted by the frontend but preserved as `$print`-like intermediate representation, which may interfere with later backend steps.

Start with a source scan, then inspect each hit to distinguish real code from comments, strings, generated debug blocks, or simulation-only guards:

```bash
rg -n '\$(display|write|fwrite|strobe|monitor|print)\b' <rtl-or-filelist-paths>
```

If the statements are intended only for simulation/debug, gate them out of synthesis using the project's existing convention, such as ``ifndef SYNTHESIS``, `translate_off/translate_on`, or generator options for Chisel/firtool debug output. Directly commenting out confirmed debug-only statements is also acceptable when it matches the project's style. Do not delete or comment them blindly; report any behavioral or verification impact.

## Syntax and Hierarchy Template

Use the same file order, include paths, and defines as the RTL build. A typical check is:

```bash
yosys -m slang -p 'read_slang -I rtl/include -D SYNTHESIS macros/SRAM_1024x32_1RW.v rtl/chip_top.sv rtl/sram_1rw_1024x32.sv; hierarchy -check -top chip_top; check'
```

If the macro Verilog model contains timing checks, `specify` blocks, unsupported primitives, encrypted content, or simulation-only constructs, generate or use exact-port blackbox stubs for syntax/hierarchy checking:

```systemverilog
(* blackbox *)
module SRAM_1024x32_1RW (
    input  logic        CLK,
    input  logic        CEN,
    input  logic        WEN,
    input  logic [9:0]  A,
    input  logic [31:0] D,
    output logic [31:0] Q
);
endmodule
```

Only use stubs for syntax/hierarchy validation; do not treat a blackbox stub as proof that macro behavior matches the RTL wrapper.

## Failure Triage

- Unknown module: ensure macro files or stubs are read before RTL that instantiates them, and confirm generated module names match exactly.
- Port not found: compare named connections against `scripts/extract_memory_ports.py --json <macro.v>` output and the source declaration.
- Width mismatch: inspect packed dimensions and any parameters; do not paper over mismatches with casts until the memory shape is confirmed.
- Parse error in macro model: retry with a blackbox stub if the project only needs syntax/hierarchy checking.
- Missing include or package: add the same `-I`, `-D`, package files, and file order used by the normal build.

## Reporting

Record the exact command and whether it passed. If it fails, include the first actionable error and the file/line it points to.
