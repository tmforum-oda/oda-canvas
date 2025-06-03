const fs = require('fs');
const yaml = require('js-yaml');
const path = require('path');

// Load and parse the OpenAPI spec
const specPath = path.join(__dirname, 'api', 'TMF639-Resource_Inventory_Management-v5.0.0.oas.yaml');
console.log('Loading spec from:', specPath);

try {
  const spec = yaml.safeLoad(fs.readFileSync(specPath, 'utf8'));
  
  console.log('OpenAPI Version:', spec.openapi);
  console.log('Title:', spec.info.title);
  console.log('Servers:', spec.servers);
  console.log('\nPaths:');
  
  for (const [path, methods] of Object.entries(spec.paths)) {
    console.log(`  ${path}:`);
    for (const [method, operation] of Object.entries(methods)) {
      if (operation.operationId) {
        console.log(`    ${method.toUpperCase()}: ${operation.operationId}`);
      }
    }
  }
  
  // Check specific /resource path
  console.log('\n/resource path details:');
  console.log(JSON.stringify(spec.paths['/resource'], null, 2));
  
} catch (error) {
  console.error('Error parsing OpenAPI spec:', error);
}
