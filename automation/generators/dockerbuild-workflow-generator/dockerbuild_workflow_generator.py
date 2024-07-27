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

    with open(config_filename, 'r') as f:
        config = yaml.safe_load(f)

    template_names = ["dockerbuild-prerelease", "dockerbuild-release"]
    for template_name in template_names:
        template = env.get_template(f"{template_name}.yml.jinja2")
        for filename,cfg in config.items():
            if "fileName" not in cfg:
                cfg["filename"] = name
            output_filename = f"{output_folder}/{template_name}-{filename}.yml"
            print(f"generating {output_filename}")
            template.stream(cfg).dump(output_filename)

    template_names = ["check-no-prerelease-suffixes-in-PR"]
    for template_name in template_names:
        template = env.get_template(f"{template_name}.yml.jinja2")
        output_filename = f"{output_folder}/{template_name}.yml"
        print(f"generating {output_filename}")
        template.stream(config=config).dump(output_filename)
        #print(template.render(config=config))


if __name__ == '__main__':
    run("dockerbuild-config.yaml")

