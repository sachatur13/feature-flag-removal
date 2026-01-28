import yaml

with open("feature_flags.yml") as f:
    FLAGS = yaml.safe_load(f)["flags"]

def search():
    if "search_v2" in FLAGS:
        return "Using new search"
    return "Using old search"

def checkout():
    if "checkout_refactor" in FLAGS:
        return "Using new checkout"
    return "Using old checkout"
