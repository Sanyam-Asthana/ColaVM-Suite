use std::env;
use std::fs;
use std::process;

mod run;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("cola error: no input file specified");
        eprintln!("usage: colavm <path_to_binary.bin>");
        process::exit(1);
    }

    let file_path = &args[1];

    let program_bytes = fs::read(file_path).unwrap_or_else(|err| {
        eprintln!("cola error: could not read file '{}'", file_path);
        eprintln!("reason: {}", err);
        process::exit(1);
    });

    if program_bytes.is_empty() {
        eprintln!("cola error: specified target file is empty.");
        process::exit(1);
    }

    run::execute_program(program_bytes);
}
