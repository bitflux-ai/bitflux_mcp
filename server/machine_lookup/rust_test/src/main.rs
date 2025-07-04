use sha2::{Sha256, Digest};
use std::env;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        eprintln!("Usage: {} <instance_id>", args[0]);
        std::process::exit(1);
    }
    let instance_id = &args[1];
    let mut hasher = Sha256::new();
    hasher.update(instance_id.as_bytes());
    let result = hasher.finalize();
    println!("{:x}", result);
}