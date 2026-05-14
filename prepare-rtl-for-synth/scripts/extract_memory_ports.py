#!/usr/bin/env python3
"""Extract module port metadata from memory compiler Verilog files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class Port:
    name: str
    direction: str
    width: str
    bits: int | None


@dataclass
class Module:
    name: str
    ports: list[Port]


DECL_KEYWORDS = {
    "wire",
    "reg",
    "logic",
    "signed",
    "unsigned",
    "tri",
    "supply0",
    "supply1",
}


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//.*", "", text)


def strip_attributes(text: str) -> str:
    return re.sub(r"\(\*.*?\*\)", "", text, flags=re.S).strip()


def split_top_level(text: str, separator: str = ",") -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    for index, char in enumerate(text):
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth = max(0, depth - 1)
        elif char == separator and depth == 0:
            parts.append(text[start:index].strip())
            start = index + 1
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def bits_from_width(width: str) -> int | None:
    if not width:
        return 1
    total = 1
    for msb, lsb in re.findall(r"\[\s*(-?\d+)\s*:\s*(-?\d+)\s*\]", width):
        total *= abs(int(msb) - int(lsb)) + 1
    return total if total != 1 else None


def clean_name(token: str) -> str:
    token = token.split("=", 1)[0].strip()
    token = re.sub(r"\[[^\]]+\]\s*$", "", token).strip()
    return token.rstrip(",")


def parse_decl_prefix(text: str) -> tuple[str, str]:
    text = strip_attributes(text)
    dims = " ".join(re.findall(r"\[[^\]]+\]", text))
    without_dims = re.sub(r"\[[^\]]+\]", " ", text)
    words = without_dims.split()
    direction = ""
    for word in words:
        if word in {"input", "output", "inout"}:
            direction = word
            break
    return direction, dims


def names_from_decl_tail(text: str) -> list[str]:
    text = strip_attributes(text)
    text = re.sub(r"\[[^\]]+\]", " ", text)
    words = [word for word in text.split() if word not in DECL_KEYWORDS]
    if words and words[0] in {"input", "output", "inout"}:
        words = words[1:]
    joined = " ".join(words)
    return [clean_name(part) for part in split_top_level(joined) if clean_name(part)]


def parse_ansi_ports(port_text: str) -> list[Port]:
    ports: list[Port] = []
    current_direction = ""
    current_width = ""
    for item in split_top_level(port_text):
        item = strip_attributes(item)
        if not item:
            continue
        direction, width = parse_decl_prefix(item)
        if direction:
            current_direction = direction
            current_width = width
        if not current_direction:
            return []
        names = names_from_decl_tail(item)
        for name in names:
            ports.append(
                Port(
                    name=name,
                    direction=current_direction,
                    width=current_width,
                    bits=bits_from_width(current_width),
                )
            )
    return ports


def parse_body_ports(port_text: str, body: str) -> list[Port]:
    ordered_names = [clean_name(part) for part in split_top_level(port_text)]
    by_name: dict[str, Port] = {}
    for match in re.finditer(r"\b(input|output|inout)\b\s+([^;]+);", body, flags=re.S):
        direction = match.group(1)
        decl = match.group(2)
        _, width = parse_decl_prefix(decl)
        for name in names_from_decl_tail(decl):
            by_name[name] = Port(
                name=name,
                direction=direction,
                width=width,
                bits=bits_from_width(width),
            )
    return [by_name[name] for name in ordered_names if name in by_name]


def find_modules(text: str) -> list[Module]:
    clean = strip_comments(text)
    pattern = re.compile(
        r"\bmodule\s+"
        r"(?P<name>\\\S+\s|[A-Za-z_][A-Za-z0-9_$]*)\s*"
        r"(?:#\s*\((?P<params>.*?)\)\s*)?"
        r"\((?P<ports>.*?)\)\s*;"
        r"(?P<body>.*?)\bendmodule\b",
        flags=re.S,
    )
    modules: list[Module] = []
    for match in pattern.finditer(clean):
        name = match.group("name").strip()
        port_text = match.group("ports")
        body = match.group("body")
        ports = parse_ansi_ports(port_text) or parse_body_ports(port_text, body)
        modules.append(Module(name=name, ports=ports))
    return modules


def module_to_dict(module: Module) -> dict[str, object]:
    return {
        "module": module.name,
        "ports": [
            {
                "name": port.name,
                "direction": port.direction,
                "width": port.width or "1",
                "bits": port.bits,
            }
            for port in module.ports
        ],
    }


def read_inputs(paths: Iterable[str]) -> str:
    chunks: list[str] = []
    for raw_path in paths:
        if raw_path == "-":
            chunks.append(sys.stdin.read())
        else:
            chunks.append(Path(raw_path).read_text())
    return "\n".join(chunks)


def run_self_test() -> None:
    sample = """
module SRAM_8x32 (
    input logic CLK,
    input [2:0] A,
    input [31:0] D,
    output logic [31:0] Q,
    input CEN, WEN
);
endmodule

module SRAM_NA (CLK, A, D, Q, CEN);
input CLK;
input [3:0] A;
input [7:0] D;
output reg [7:0] Q;
input CEN;
endmodule
"""
    modules = find_modules(sample)
    assert [module.name for module in modules] == ["SRAM_8x32", "SRAM_NA"]
    assert modules[0].ports[1].bits == 3
    assert modules[0].ports[3].direction == "output"
    assert modules[1].ports[3].width == "[7:0]"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract module port metadata from memory compiler Verilog files."
    )
    parser.add_argument("paths", nargs="*", help="Verilog files to parse, or '-' for stdin")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table")
    parser.add_argument("--module", help="Only emit modules whose name matches this regex")
    parser.add_argument("--self-test", action="store_true", help="Run parser self-test")
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        print("self-test passed")
        return 0
    if not args.paths:
        parser.error("provide at least one Verilog file, or use --self-test")

    modules = find_modules(read_inputs(args.paths))
    if args.module:
        module_re = re.compile(args.module)
        modules = [module for module in modules if module_re.search(module.name)]

    if args.json:
        print(json.dumps([module_to_dict(module) for module in modules], indent=2))
        return 0

    for module in modules:
        print(f"module {module.name}")
        for port in module.ports:
            width = port.width or "1"
            bits = "" if port.bits is None else f" ({port.bits} bits)"
            print(f"  {port.direction:6} {width:12} {port.name}{bits}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
