'use strict'

// Unit tests for format-comment.js, using real selections from the map and
// feature files.
//
//   npm run test:selection

const test = require('node:test')
const assert = require('node:assert/strict')
const { MARKER, formatComment } = require('./format-comment')
const { loadContext, selectFeatures, selectAll } = require('./select-features')

const context = loadContext()
const select = files => selectFeatures(files, context)

test('the comment starts with the marker the workflow looks for', () => {
  assert.ok(formatComment(select(['README.md'])).startsWith(MARKER + '\n'))
})

test('a selection lists the runs, the features in scope and the changed paths', () => {
  const text = formatComment(select(['charts/pdb-management-operator/values.yaml', 'README.md']))
  assert.match(text, /\*\*Selected:\*\* 5 features, 49 scenarios, chosen from the paths this PR changes\./)
  assert.match(text, /\| default \| Istio \| 5 \| 49 \| `\(\(@UC002-F001\) or \(@UC017\)\) and not @KongGateway and not @ApisixGateway` \|/)
  assert.match(text, /- `UC017-F002-PDB-Management-Policy-Based\.feature` \(10 scenarios\)/)
  assert.match(text, /\| `charts\/pdb-management-operator\/values\.yaml` \| Disruption Budget Management operator \|/)
  assert.match(text, /\| `README\.md` \| documentation \|/)
})

test('a gateway selection names each cluster', () => {
  const text = formatComment(select(['charts/kong-gateway/values.yaml']))
  assert.match(text, /on 2 clusters \(Istio, Kong\)/)
  assert.match(text, /\| kong \| Kong \| 2 \| 4 \|/)
})

test('a full run says which paths caused it and why', () => {
  const text = formatComment(select(['charts/oda-crds/templates/oda-component-crd.yaml', 'feature-definition-and-test-kit/features/step-definition/PDBManagementSteps.js']))
  assert.match(text, /\*\*Full suite:\*\* .* on 3 clusters \(Istio, Kong, APISIX\)\./)
  assert.match(text, /- `charts\/oda-crds\/templates\/oda-component-crd\.yaml`: always runs the full suite/)
  assert.match(text, /- `feature-definition-and-test-kit\/features\/step-definition\/PDBManagementSteps\.js`: not in the test-selection map/)
})

test('a full run requested from the Actions tab says so', () => {
  assert.match(formatComment(selectAll('Full suite requested.', context)), /The full suite was requested: Full suite requested\./)
})

test('a skipped selection gives the reason and no runs', () => {
  const text = formatComment(select(['README.md', 'docs/a.md']))
  assert.match(text, /\*\*No BDD tests run:\*\* Documentation only\./)
  assert.doesNotMatch(text, /\| Run \|/)
})

test('a skip reason from trigger_test overrides the selection', () => {
  const text = formatComment(select(['charts/oda-crds/Chart.yaml']), { skipReason: '[skip tests] is in the PR title' })
  assert.match(text, /\*\*No BDD tests run:\*\* \\\[skip tests\\\] is in the PR title\./)
  assert.doesNotMatch(text, /Full suite/)
  assert.match(text, /Changed paths \(1\)/)
})

test('the footer shows only a valid commit and run link', () => {
  const ok = formatComment(select(['README.md']), { headSha: 'abcdef1234567890', runUrl: 'https://github.com/tmforum-oda/oda-canvas/actions/runs/123' })
  assert.match(ok, /for abcdef1 · \[workflow run\]\(https:\/\/github\.com\/tmforum-oda\/oda-canvas\/actions\/runs\/123\)/)
  const bad = formatComment(select(['README.md']), { headSha: 'not a sha', runUrl: 'https://example.com/x' })
  assert.doesNotMatch(bad, /example\.com|not a sha/)
})

test('untrusted paths cannot break out of the table or inject markup', () => {
  const evil = 'docs/a`|<img src=x>\n# heading.md'
  const text = formatComment(select([evil]))
  const row = text.split('\n').find(line => line.includes('<img'))
  assert.ok(row.startsWith('| `docs/a\'\\|<img src=x> # heading.md`'), row)
  assert.doesNotMatch(text, /^# heading/m)
})

test('long lists are capped', () => {
  const files = Array.from({ length: 150 }, (_, i) => `docs/page-${i}.md`)
  const text = formatComment(select(files))
  assert.match(text, /Changed paths \(150\)/)
  assert.match(text, /\| and 50 more \| \|/)
})
