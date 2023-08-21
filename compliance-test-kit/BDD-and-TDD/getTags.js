const fs = require('fs');
const path = require('path');

function extractTags(directory) {
  const featureFiles = fs.readdirSync(directory).filter(file => file.endsWith('.feature'));
  let tags = [];

  featureFiles.forEach(file => {
    const content = fs.readFileSync(path.join(directory, file), 'utf-8');
    const matches = content.match(/@\w+/g);
    if (matches) {
      tags = tags.concat(matches);
    }
    const featureMatches = content.match(/@\w+\-\w+/g);
    if (featureMatches) {
      tags = tags.concat(featureMatches);
    }
  });

  // Remove duplicates
  return [...new Set(tags)];
}

console.log('Tags in features/ directory: @UC001 is a tag for a use case; @UC001-F001 is a tag for a feature within a use case.');
console.log('');
let tags = extractTags('features/');
for (let tag of tags) {
  console.log(tag);
}
