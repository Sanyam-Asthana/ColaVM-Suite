import sys
import struct

OPCODES = {
    "PUSH8": 1,
    "PUSH32": 2,
    "POP": 3,
    "TOP": 4,
    "ADD": 5,
    "SUB": 6,
    "MUL": 7,
    "DIV": 8,
    "MOD": 9,
    "CHAR": 10,
    "PRINT8": 11,
    "PRINT32": 12,
    "JUMP8": 13,
    "JEZ8": 14,
    "JEQ8": 15,
    "JGT8": 16,
    "JLT8": 17,
    "JGE8": 18,
    "JLE8": 19,
    "JUMP32": 20,
    "JEZ32": 21,
    "JEQ32": 22,
    "JGT32": 23,
    "JLT32": 24,
    "JGE32": 25,
    "JLE32": 26,
    "STORE": 27,
    "LOAD": 28,
    "END": 29,
    "PUSHCONST0": 30,
    "PUSHCONST1": 31,
    "PUSHCONST2": 32,
    "PUSHCONST3": 33,
    "PUSHCONST4": 34,
    "PUSHCONST5": 35,
    "PUSHCONST6": 36,
    "PUSHCONST7": 37,
    "PUSHCONST8": 38,
    "PUSHCONST9": 39,
    "INC": 40,
    "DEC": 41,
}


def parse_source(file_path):
    clean_lines = []
    with open(file_path, "r") as f:
        for line in f:
            line = line.split(";")[0].strip()
            if line:
                clean_lines.append(line)
    return clean_lines


def get_instruction_size(cmd, args_str):
    """Calculates the byte size of an instruction layout during first pass"""
    if cmd in [
        "POP",
        "TOP",
        "ADD",
        "SUB",
        "MUL",
        "DIV",
        "MOD",
        "END",
        "INC",
        "DEC",
    ] or cmd.startswith("PUSHCONST"):
        return 1
    elif cmd in ["PUSH8", "STORE", "LOAD", "CHAR"]:
        return 2
    elif cmd in ["PUSH32"]:
        return 5
    elif cmd in ["PRINT8"]:
        return 2 + len(args_str.strip('"').encode("utf-8"))
    elif cmd in ["PRINT32"]:
        return 5 + len(args_str.strip('"').encode("utf-8"))
    elif cmd.endswith("8"):
        return 2
    elif cmd.endswith("32"):
        return 5
    return 0


def assemble(file_path):
    """Assembles the instruction into a compact binary"""
    raw_lines = parse_source(file_path)

    labels = {}
    intermediate_instructions = []
    pc = 0

    """
    The following is the first pass of the assembler.

    It resolves all the labels and maps them to their respective PC values.

    It also deduces whether the 8-bit or the 32-bit counterpart OpCode is to be used for a generic instruction.

    Since the labels have not been resolved at the time of the first pass, the jumps are assigned the 8-bit counterpart by default.
    """
    for line in raw_lines:
        if line.startswith(":"):
            labels[line[1:].strip()] = pc
            continue

        parts = line.split(maxsplit=1)
        cmd = parts[0].upper()
        args_str = parts[1].strip() if len(parts) > 1 else ""

        if cmd == "PUSH":
            val = int(args_str)
            if 0 <= val <= 9:
                cmd = f"PUSHCONST{val}"
                args_str = ""
            elif -128 <= val <= 127:
                cmd = "PUSH8"
            else:
                cmd = "PUSH32"

        elif cmd == "PRINT":
            clean_str = args_str.strip('"')
            str_bytes = clean_str.encode("utf-8")
            cmd = "PRINT8" if len(str_bytes) <= 255 else "PRINT32"

        elif cmd in ["JUMP", "JEZ", "JEQ", "JGT", "JLT", "JGE", "JLE"]:
            cmd = f"{cmd}8"

        size = get_instruction_size(cmd, args_str)
        intermediate_instructions.append({"cmd": cmd, "args": args_str, "pass1_pc": pc})
        pc += size

    bytecode = bytearray()

    """
    The following is the second pass, which actually packs the instructions into a binary.

    It promotes any jump instructions whose labels point to PC positions >255
    """
    for meta in intermediate_instructions:
        cmd = meta["cmd"]
        args = meta["args"]

        if any(
            cmd.startswith(j)
            for j in ["JUMP", "JEZ", "JEQ", "JGT", "JLT", "JGE", "JLE"]
        ) and cmd.endswith("8"):
            base_jump = cmd[:-1]
            target_pc = labels[args] if args in labels else int(args)

            if target_pc > 255:
                cmd = f"{base_jump}32"

        bytecode.append(OPCODES[cmd])

        if cmd.startswith("PUSHCONST") or cmd in [
            "POP",
            "TOP",
            "ADD",
            "SUB",
            "MUL",
            "DIV",
            "MOD",
            "END",
            "INC",
            "DEC",
        ]:
            continue
        elif cmd == "PUSH8":
            bytecode.extend(struct.pack("<b", int(args)))
        elif cmd in ["STORE", "LOAD", "CHAR"]:
            bytecode.extend(struct.pack("<B", int(args)))
        elif cmd == "PUSH32":
            bytecode.extend(struct.pack("<i", int(args)))
        elif cmd in ["JUMP8", "JEZ8", "JEQ8", "JGT8", "JLT8", "JGE8", "JLE8"]:
            target_pc = labels[args] if args in labels else int(args)
            bytecode.extend(struct.pack("<B", target_pc))
        elif cmd in ["JUMP32", "JEZ32", "JEQ32", "JGT32", "JLT32", "JGE32", "JLE32"]:
            target_pc = labels[args] if args in labels else int(args)
            bytecode.extend(struct.pack("<I", target_pc))
        elif cmd in ["PRINT8", "PRINT32"]:
            clean_str = args.strip('"')
            str_bytes = clean_str.encode("utf-8")
            if cmd == "PRINT8":
                bytecode.extend(struct.pack("<B", len(str_bytes)))
            else:
                bytecode.extend(struct.pack("<I", len(str_bytes)))
            bytecode.extend(str_bytes)

    return bytecode


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 <this file> <source.cola>")
        sys.exit(1)

    filename = sys.argv[1]
    output_bin = filename.rsplit(".", 1)[0] + ".can"

    try:
        print("Filling cola into a can..")
        binary_data = assemble(filename)
        with open(output_bin, "wb") as out_file:
            out_file.write(binary_data)
        print(
            f"Fill: Compiled! Cola filled to can: {output_bin} ({len(binary_data)} bytes)"
        )
    except Exception as e:
        print(f"Fill: Assembler Failure: {e}")
        sys.exit(1)
