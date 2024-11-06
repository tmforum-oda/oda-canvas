# Command-line tool for Conversion Webhook

This is a simple command-line tool that uses the conversion webhook to convert a component (from a YAML file) to a requested version. It can be used to test the conversion webhook as well as to upgrade component YAML files.

## Usage

Run the conversion webhook in `../implementation` in local test mode:

```
cd ../implementation
npm install
npm test
```

The console should show something like:

```
Running in test mode
Server running on port 8002
```

Then in a separate console: Run the command-line tool using `npm start <component-filename.yaml> <requested-version>`. There is a `v1beta3` and `v1beta4` example component file in this folder. e.g.

```
npm start productcatalog-v1beta3.yaml v1beta4
```

The module should output the updated YAML file to the console. You can see comments on the conversion in progress in the first console.