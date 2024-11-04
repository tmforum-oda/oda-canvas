// FILE: app.js
const fs = require('fs');
const yaml = require('js-yaml');
const http = require('http');

// Function to load and parse YAML file
function loadYamlFile(filePath) {
    try {
        // console.log(`Loading file: ${filePath}`);
        const fileContents = fs.readFileSync(filePath);
        // console.log(fileContents);
        return yaml.load(fileContents);
    } catch (e) {
        console.error(`Error loading YAML file: ${e.message}`);
        process.exit(1);
    }
}


// Function to create ConversionReview object
function createConversionReview(component, inDesiredVersion) {
    return {
        apiVersion: 'apiextensions.k8s.io/v1',
        kind: 'ConversionReview',
        request: {
            uid: '0000',
            desiredAPIVersion: 'oda.tmforum.org/' + inDesiredVersion,
            apiVersion: component.apiVersion,
            objects: [component],
        },
    };
}

// Main function
function main() {
    const args = process.argv.slice(2);
    if (args.length < 2) {
        console.error('Usage: npm start <path-to-yaml-file> <new-version>');
        process.exit(1);
    }

    const yamlFilePath = args[0];
    const newVersion = args[1];

    const component = loadYamlFile(yamlFilePath);
    const conversionReview = createConversionReview(component, newVersion);

    // console.log(JSON.stringify(conversionReview, null, 2));

    const postData = JSON.stringify(conversionReview);

    const options = {
        hostname: 'localhost',
        port: 8002,
        path: '/',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(postData),
        },
    };
    
    const req = http.request(options, (res) => {
        // console.log(`statusCode: ${res.statusCode}`);
    
        // store the result in a variable
        let data = '';
        res.on('data', (chunk) => {
            data += chunk;
        });

        res.on('end', () => {
            const result = JSON.parse(data);
            const convertedObject = result.response.convertedObjects[0];
            // print as YAML
            console.log(Buffer.from(yaml.dump(convertedObject)).toString());
        });
        
    });
    
    req.on('error', (e) => {
        console.error(`Problem with request: ${e.message}`);
    });
    
    // Write data to request body
    req.write(postData);
    req.end();
}

main();