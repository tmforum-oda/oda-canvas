from jinja2 import Template, Environment, PackageLoader, select_autoescape
import yaml
import os

def to_yaml(data):
    return yaml.dump(data)

def run(config_filename:str):
    output_folder = "output"
    os.makedirs(output_folder, exist_ok=True)   

    env = Environment(
        loader=PackageLoader("dockerbuild_workflow_generator"),
        autoescape=select_autoescape()
    )
    env.filters.update({'to_yaml': to_yaml})

    
    template_names = ["dockerbuild-prerelease", "dockerbuild-release"]
    for template_name in template_names:
        template = env.get_template(f"{template_name}.yml.jinja2")
        with open(config_filename, 'r') as f:
            cfgs = yaml.safe_load(f)
        for filename,cfg in cfgs.items():
            if "fileName" not in cfg:
                cfg["filename"] = name
            output_filename = f"{output_folder}/{template_name}-{filename}.yml"
            print(f"generating {output_filename}")
            template.stream(cfg).dump(output_filename)

if __name__ == '__main__':
    run("dockerbuild-config.yaml")

