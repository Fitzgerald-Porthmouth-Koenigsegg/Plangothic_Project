fn main() {
    if std::env::var("CARGO_CFG_WINDOWS").is_ok() {
        embed_resource::compile("resource.rc");
    }
}
