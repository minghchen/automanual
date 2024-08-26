from importlib import import_module

def load_examples(site):
    try:
        module = import_module(f".{site}_examples", package='prompts.examples')
        return module
    except ImportError:
        print(f"Module for {site} not found.")
        return None