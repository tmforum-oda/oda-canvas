#!/usr/bin/env node

/**
 * PlantUML to SVG Converter using Kroki API
 * 
 * Converts a single PlantUML (.puml) file to SVG format using the Kroki online service.
 * The script uses only Node.js built-in modules (no external dependencies required).
 * 
 * Usage: node scripts/plantuml-to-svg.js <path-to-puml-file>
 * 
 * Example: node scripts/plantuml-to-svg.js usecase-library/pumlFiles/exposed-API-create.puml
 * 
 * The generated SVG file will be saved in the same directory with the same name but .svg extension.
 */

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const https = require('https');

/**
 * Encodes PlantUML source to base64url format required by Kroki
 * @param {string} source - PlantUML source code
 * @returns {string} - Base64url encoded string
 */
function encodeToKroki(source) {
  // Compress using deflate
  const compressed = zlib.deflateSync(Buffer.from(source, 'utf8'));
  
  // Convert to base64
  const base64 = compressed.toString('base64');
  
  // Convert to base64url (URL-safe variant)
  const base64url = base64
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, ''); // Remove padding
  
  return base64url;
}

/**
 * Fetches SVG from Kroki API
 * @param {string} encoded - Base64url encoded PlantUML
 * @returns {Promise<string>} - SVG content
 */
function fetchSvgFromKroki(encoded) {
  return new Promise((resolve, reject) => {
    const url = `https://kroki.io/plantuml/svg/${encoded}`;
    
    https.get(url, (res) => {
      if (res.statusCode !== 200) {
        reject(new Error(`Kroki API returned status ${res.statusCode}`));
        return;
      }
      
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        resolve(data);
      });
    }).on('error', (err) => {
      reject(new Error(`Failed to fetch from Kroki: ${err.message}`));
    });
  });
}

/**
 * Validates SVG content
 * @param {string} svgContent - SVG content to validate
 * @returns {boolean} - True if valid, false otherwise
 */
function validateSvg(svgContent) {
  // Check if content is not empty
  if (!svgContent || svgContent.length === 0) {
    console.error('Validation failed: SVG content is empty');
    return false;
  }
  
  // Check if content contains <svg tag
  if (!svgContent.includes('<svg')) {
    console.error('Validation failed: SVG content does not contain <svg tag');
    return false;
  }
  
  // Basic XML structure check - should have opening and closing svg tags
  if (!svgContent.includes('</svg>')) {
    console.error('Validation failed: SVG content does not have closing </svg> tag');
    return false;
  }
  
  // Check minimum size (a valid SVG should be at least a few hundred bytes)
  if (svgContent.length < 100) {
    console.error('Validation failed: SVG content is suspiciously small');
    return false;
  }
  
  return true;
}

/**
 * Main conversion function
 * @param {string} pumlFilePath - Path to the .puml file
 */
async function convertPumlToSvg(pumlFilePath) {
  try {
    // Validate input file path
    if (!pumlFilePath) {
      console.error('Error: No file path provided');
      console.log('Usage: node scripts/plantuml-to-svg.js <path-to-puml-file>');
      process.exit(1);
    }
    
    // Check if file exists
    if (!fs.existsSync(pumlFilePath)) {
      console.error(`Error: File not found: ${pumlFilePath}`);
      process.exit(1);
    }
    
    // Check if file has .puml extension
    if (path.extname(pumlFilePath) !== '.puml') {
      console.error(`Error: File must have .puml extension: ${pumlFilePath}`);
      process.exit(1);
    }
    
    console.log(`Converting: ${pumlFilePath}`);
    
    // Read PlantUML source
    const pumlSource = fs.readFileSync(pumlFilePath, 'utf8');
    
    if (!pumlSource || pumlSource.trim().length === 0) {
      console.error('Error: PlantUML file is empty');
      process.exit(1);
    }
    
    // Encode for Kroki
    console.log('Encoding PlantUML source...');
    const encoded = encodeToKroki(pumlSource);
    
    // Fetch SVG from Kroki
    console.log('Fetching SVG from Kroki API...');
    const svgContent = await fetchSvgFromKroki(encoded);
    
    // Validate SVG
    console.log('Validating SVG content...');
    if (!validateSvg(svgContent)) {
      console.error('Error: Generated SVG failed validation');
      process.exit(1);
    }
    
    // Generate output path (same directory, same name, .svg extension)
    const outputPath = pumlFilePath.replace(/\.puml$/, '.svg');
    
    // Write SVG file
    fs.writeFileSync(outputPath, svgContent, 'utf8');
    
    console.log(`✓ Successfully created: ${outputPath}`);
    console.log(`  Size: ${svgContent.length} bytes`);
    
    process.exit(0);
    
  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
}

// Run the conversion
const pumlFilePath = process.argv[2];
convertPumlToSvg(pumlFilePath);
