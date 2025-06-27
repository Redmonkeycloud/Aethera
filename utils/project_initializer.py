import os
import json

# Define base directory for AETHERA project
base_dir = '/mnt/data/AETHERA'
project_name = 'AETHERA'

# Create core folders
folders = ['core', 'utils', 'ai', 'assets', 'data', 'outputs']
for folder in folders:
    os.makedirs(os.path.join(base_dir, folder), exist_ok=True)

# Content of project_initializer.py
initializer_code = """import os
import json

def initialize_project(base_path, project_name):
    \"\"\"
    Bootstraps AETHERA project directory structure and default configuration.

    Args:
        base_path (str): Path where the project folder will be created.
        project_name (str): Name of the project folder.
    \"\"\"
    project_dir = os.path.join(base_path, project_name)
    folders = ['core', 'utils', 'ai', 'assets', 'data', 'outputs']
    for folder in folders:
        os.makedirs(os.path.join(project_dir, folder), exist_ok=True)

    # Default configuration
    config = {
        "project_name": project_name,
        "paths": {
            "core": "core",
            "utils": "utils",
            "ai": "ai",
            "assets": "assets",
            "data": "data",
            "outputs": "outputs"
        },
        "api_keys": {
            "openai": None
        },
        "gis": {
            "protected_areas_path": None
        },
        "emissions": {
            "emission_factors_path": None
        }
    }

    # Write configuration to file
    config_path = os.path.join(project_dir, 'config.json')
    with open(config_path, 'w') as cf:
        json.dump(config, cf, indent=4)

    print(f"Project initialized at {project_dir}")

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Initialize AETHERA project structure.')
    parser.add_argument('--path', default='.', help='Base path for the project')
    parser.add_argument('--name', default='AETHERA', help='Name of the project folder')
    args = parser.parse_args()
    initialize_project(args.path, args.name)
"""

# Ensure base directory exists
os.makedirs(base_dir, exist_ok=True)

# Write the script to the utils directory
script_path = os.path.join(base_dir, 'utils', 'project_initializer.py')
with open(script_path, 'w') as f:
    f.write(initializer_code)

print(f"Created: {script_path}")
