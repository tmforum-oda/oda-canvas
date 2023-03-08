import yaml
import requests


def loadSwaggerYAML(inSwaggerUrl, inBasePath, inProductionEndpoints, inAPIName):

  f = requests.get(inSwaggerUrl)

  try:
    swaggerYAML = yaml.safe_load(f.text)
  except yaml.YAMLError as exc:
    print(exc)

  # add wso2 specific fields to swagger
  swaggerYAML['x-wso2-basePath'] = inBasePath
  swaggerYAML['x-wso2-production-endpoints'] = {'urls': inProductionEndpoints}

  # create configmap from template
  with open("./apiOperator-wso2/configmap-swagger-template.yaml", 'r') as stream:
    try:
        configMap = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

  # add name
  configMap['metadata']['name'] = inAPIName


  # add swagger
  configMap['data']['swagger.yaml'] = yaml.dump(swaggerYAML)




  return (configMap)



if __name__ == '__main__':
    configMap = loadSwaggerYAML("https://raw.githubusercontent.com/tmforum-rand/oda-component-definitions/wso2APIOperator/components/vodafone-next-productcatalog.swagger.json?token=ABYIJPQH7KR75YX44JF62XS626XTA")
    with open('output.yml', 'w') as outfile:
      yaml.dump(configMap, outfile, default_flow_style=False)
