# Macro Replace Preparation

## Input Inventory

Collect these facts before preparing macro replacement:

- `top`: synthesis/check top module.
- `rtl_files`: ordered RTL/SystemVerilog file list, or the build command that produces one.
- `include_dirs` and `defines`: all required parser flags.
- `macro_files`: memory compiler Verilog models or blackbox stubs.
- `logical_memories`: wrapper module names, inferred memory sites, or direct instances to replace.
- `replacement_policy`: wrapper replacement, direct instance replacement, generated stubs, or project-specific flow.

Prefer reading existing project config first: filelists, FuseSoC core files, Bazel rules, Makefiles, TCL scripts, YAML/JSON manifests, or previous SRAM wrapper conventions.

## Suggested Manifest

Use the repository's existing config format if one exists. Otherwise create a small YAML or JSON manifest with one entry per logical memory:

```yaml
top: chip_top
rtl_files:
  - rtl/chip_top.sv
  - rtl/sram_1rw_1024x32.sv
include_dirs:
  - rtl/include
defines:
  - SYNTHESIS
macro_files:
  - macros/SRAM_1024x32_1RW.v
replacements:
  - logical_module: sram_1rw_1024x32
    logical_file: rtl/sram_1rw_1024x32.sv
    macro_module: SRAM_1024x32_1RW
    macro_file: macros/SRAM_1024x32_1RW.v
    depth: 1024
    data_width: 32
    address_width: 10
    style: wrapper-internal-instance
    instance_name: u_macro
    ports:
      clk: CLK
      addr: A
      wdata: D
      rdata: Q
      cs_n: CEN
      we_n: WEN
    tieoffs:
      EMA: "3'b000"
      RETN: "1'b1"
    notes:
      - "CEN/WEN are active-low in the macro."
```

The manifest should make polarity explicit. Avoid names like `enable: CEN` without recording whether either side is active-low.

## Mapping Checklist

For each replacement, verify:

- Address width equals `ceil(log2(depth))`, or the project already handles unused address values.
- Data width and write mask width match exactly, including byte/bit mask polarity.
- Logical write enable maps to macro write enable with correct active level.
- Chip enable, clock enable, sleep, retention, and shutdown ports have explicit behavior.
- Read data latency and read-during-write mode match the behavioral wrapper.
- Reset or initialization behavior is preserved or explicitly documented as unsupported by the macro.
- Test, scan, BIST, repair, redundancy, power, and ground pins are connected according to compiler docs or project conventions.

## Width Mismatch Workarounds

If exact width matching cannot be achieved because of memory compiler or available macro limitations, a workaround can be proposed instead of stopping immediately. Treat this as a soft constraint, not a default transformation.

Acceptable last-resort options include:

- Stitching multiple macros together to build the required data width or depth.
- Banking or tiling memories when the address/data split is explicit and the wrapper preserves the original interface.
- Truncating, padding, or slicing widths only when the discarded or added bits are proven unused, tied off, or explicitly accepted by the user.

Record the workaround in the manifest, including the reason exact matching failed, which bits or banks map to each macro, any truncation/padding, and whether behavior equivalence is preserved. If truncation or tiling changes observable RTL behavior, stop for explicit approval and report the impact.

## Patching Guidance

Prefer this replacement shape for wrapper modules:

```systemverilog
module sram_1rw_1024x32 (
    input  logic        clk,
    input  logic        cs,
    input  logic        we,
    input  logic [9:0]  addr,
    input  logic [31:0] wdata,
    output logic [31:0] rdata
);

  SRAM_1024x32_1RW u_macro (
      .CLK (clk),
      .CEN (~cs),
      .WEN (~we),
      .A   (addr),
      .D   (wdata),
      .Q   (rdata)
  );

endmodule
```

Keep project formatting and declaration style. If the wrapper currently contains assertions, simulation-only code, or synthesis guards, preserve the existing convention unless it conflicts with the requested replacement.

## Ambiguity Handling

Stop and ask, or leave a clearly reported blocker, when:

- A logical memory must be built from multiple macros and no local banking/tiling pattern exists.
- Macro behavior depends on compiler options not visible in the Verilog module.
- Macro model ports include undocumented controls.
- The replacement changes observable latency, reset behavior, byte-write semantics, or clock-domain assumptions.
