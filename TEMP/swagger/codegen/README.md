# Component Vault SideCar codegen

## convert openapi.yaml to json

Open Swagger Editor

https://developer.telekom.de/swagger-editor/

upload ../openapi.yaml

Select "File" > "Convert and Save as JSON"

--> save to ./openapi.json

## create stub

see: https://github.com/swagger-api/swagger-codegen/wiki/Server-stub-generator-HOWTO#go-server

checkout the branch 3.0.0 to support openapi 3.X.

```
git clone -b 3.0.0 https://github.com/swagger-api/swagger-codegen
cd swagger-codegen
mvn clean package
java -jar modules/swagger-codegen-cli/target/swagger-codegen-cli.jar generate -i ../openapi.json -l go-server -o ../cvsidecar
```

