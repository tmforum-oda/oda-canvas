'use strict'

// Unit tests for select-features.js. They run against the real map and
// feature files, so a change to either that breaks these cases fails here.
//
//   npm run test:selection

const test = require('node:test')
const assert = require('node:assert/strict')
const {
  globToRegExp,
  changedSections,
  parsePrFiles,
  loadCanvasSectionNames,
  parseFeature,
  loadContext,
  chartUsage,
  selectFeatures,
  checkSelection
} = require('./select-features')

const context = loadContext()
const select = files => selectFeatures(files, context)
const run = (result, name) => result.runs.find(r => r.name === name)
const featureIds = r => (r ? r.features.map(f => f.name.slice(0, 10)) : [])

test('globToRegExp', async t => {
  await t.test('* stays within one path segment', () => {
    assert.ok(globToRegExp('charts/*.yaml').test('charts/values.yaml'))
    assert.ok(!globToRegExp('charts/*.yaml').test('charts/a/values.yaml'))
  })
  await t.test('** matches any number of segments', () => {
    assert.ok(globToRegExp('charts/oda-crds/**').test('charts/oda-crds/templates/a.yaml'))
    assert.ok(globToRegExp('**/*.md').test('README.md'))
    assert.ok(globToRegExp('**/*.md').test('a/b/README.md'))
    assert.ok(!globToRegExp('**/*.md').test('a/b/README.mdx'))
  })
  await t.test('regex characters are literal', () => {
    assert.ok(globToRegExp('a+b.(c)').test('a+b.(c)'))
    assert.ok(!globToRegExp('a.b').test('axb'))
  })
})

test('a PR that changes only the PDB operator runs the smoke test and @UC017', () => {
  const result = select(['source/operators/TMFOP010-Disruption-Budget-Management/pdb-management/main.go'])
  assert.equal(result.mode, 'selected')
  assert.deepEqual(result.runs.map(r => r.name), ['default'])
  assert.deepEqual(featureIds(run(result, 'default')), ['UC002-F001', 'UC017-F001', 'UC017-F002', 'UC017-F003', 'UC017-F004'])
})

test('a PR that changes the CRDs runs the full suite, including every gateway run', () => {
  const result = select(['charts/oda-crds/templates/oda-component-crd.yaml'])
  assert.equal(result.mode, 'full')
  assert.match(result.reason, /charts\/oda-crds\/templates\/oda-component-crd\.yaml/)
  assert.deepEqual(result.runs.map(r => r.name), ['default', 'kong', 'apisix'])
  const total = context.features.reduce((n, f) => n + f.scenarioTags.length, 0)
  assert.equal(result.scenarios, total)
})

test('a changed path that is not in the map runs the full suite and is named', () => {
  const result = select(['charts/canvas-oda/templates/prehook.yaml', 'docs/README.md'])
  assert.equal(result.mode, 'full')
  assert.match(result.reason, /aren't in the test-selection map: charts\/canvas-oda\/templates\/prehook\.yaml\./)
  assert.equal(result.paths.find(p => p.path === 'charts/canvas-oda/templates/prehook.yaml').category, 'unmapped')
})

test('canvas-oda chart files are mapped by the sections that changed', async t => {
  const VALUES = 'charts/canvas-oda/values.yaml'
  const CHART = 'charts/canvas-oda/Chart.yaml'
  const selectWith = (patches, extra = []) => selectFeatures([...Object.keys(patches), ...extra], { ...context, patches: new Map(Object.entries(patches)) })

  // Hunk headers carry the last top-level line before the hunk, as git writes them
  const componentOperatorBump = [
    '@@ -177,7 +177,7 @@ component-operator:',
    '     compopVersion: 1.1.2',
    '-    compopPrereleaseSuffix: -rc1',
    '+    compopPrereleaseSuffix: -rc2',
    '     imagePullPolicy: IfNotPresent'
  ].join('\n')
  const chartVersionBump = [
    '@@ -16,7 +16,8 @@ type: application',
    ' ',
    '-version: 1.2.6-rc4',
    '+version: 1.2.6-rc5',
    '+# version: 1.2.6-rc5 - issue 615 - bug-fix for canvas images'
  ].join('\n')

  await t.test('an operator bump in values.yaml and Chart.yaml runs that operator\'s features', () => {
    const result = selectWith({ [VALUES]: componentOperatorBump, [CHART]: chartVersionBump })
    assert.equal(result.mode, 'selected')
    assert.equal(result.tagExpression, '(@UC002-F001) or (@UC002 or @UC013)')
    assert.match(result.paths.find(p => p.path === VALUES).matched[0], /Component Management operator \(component-operator\)/)
  })

  await t.test('a chart version bump on its own runs only the smoke test', () => {
    const result = selectWith({ [CHART]: chartVersionBump })
    assert.equal(result.mode, 'selected')
    assert.equal(result.tagExpression, '(@UC002-F001)')
  })

  await t.test('a Chart.yaml dependency bump runs that dependency\'s features', () => {
    const patch = [
      '@@ -60,7 +60,7 @@ dependencies:',
      '     condition: dependency-management-keycloak-authz.enabled',
      '   - name: pdb-management-operator',
      '-    version: "0.1.1"',
      '+    version: "0.1.2"',
      "     repository: 'file://../pdb-management-operator'"
    ].join('\n')
    assert.equal(selectWith({ [CHART]: patch }).tagExpression, '(@UC002-F001) or (@UC017)')
  })

  await t.test('a section no rule lists runs the full suite and is named', () => {
    const patch = ['@@ -7,4 +7,4 @@ global:', '   certificate:', '-    enabled: true', '+    enabled: false'].join('\n')
    const result = selectWith({ [VALUES]: patch })
    assert.equal(result.mode, 'full')
    assert.match(result.reason, /charts\/canvas-oda\/values\.yaml \(canvas chart sections not in the map: global\)/)
  })

  await t.test('a hunk that spans sections selects each one', () => {
    const patch = [
      '@@ -180,10 +180,10 @@ component-operator:',
      '-    istioGateway: true',
      '+    istioGateway: false',
      ' ',
      ' identityconfig-operator-keycloak:',
      '   deployment:',
      '-    imagePullPolicy: IfNotPresent',
      '+    imagePullPolicy: Always'
    ].join('\n')
    assert.equal(selectWith({ [VALUES]: patch }).tagExpression, '(@UC002-F001) or (@UC002 or @UC013) or (@UC005 or @UC010)')
  })

  await t.test('a Kong section selects the Kong gateway run', () => {
    const patch = ['@@ -474,2 +474,2 @@ kong-gateway-install:', '-  enabled: false', '+  enabled: true'].join('\n')
    const result = selectWith({ [VALUES]: patch })
    assert.deepEqual(result.runs.map(r => r.name), ['default', 'kong'])
  })

  await t.test('comment-only changes run nothing', () => {
    const patch = ['@@ -173,3 +173,3 @@ component-operator:', '-  # old comment', '+  # new comment', '   deployment:'].join('\n')
    assert.equal(selectWith({ [VALUES]: patch }).mode, 'skip')
  })

  await t.test('a change outside any section runs the full suite', () => {
    const patch = ['@@ -1,3 +1,3 @@', '-  indented: before-any-key', '+  indented: changed'].join('\n')
    assert.equal(selectWith({ [VALUES]: patch }).mode, 'full')
  })

  await t.test('a Chart.yaml dependency change whose name is outside the hunk runs the full suite', () => {
    const patch = ['@@ -61,4 +61,4 @@ dependencies:', "     repository: 'file://../x'", '-    condition: x.enabled', '+    condition: y.enabled'].join('\n')
    assert.equal(selectWith({ [CHART]: patch }).mode, 'full')
  })

  await t.test('without a diff the file runs the full suite', () => {
    const result = select([VALUES])
    assert.equal(result.mode, 'full')
    assert.match(result.reason, /no diff was available/)
  })
})

test('changedSections reads git diff output, headers included', () => {
  const patch = [
    'diff --git a/charts/canvas-oda/values.yaml b/charts/canvas-oda/values.yaml',
    'index 1111111..2222222 100644',
    '--- a/charts/canvas-oda/values.yaml',
    '+++ b/charts/canvas-oda/values.yaml',
    '@@ -405,3 +405,3 @@ pdb-management-operator:',
    '-  enabled: true',
    '+  enabled: false'
  ].join('\r\n')
  const { sections, unknown } = changedSections(patch, false)
  assert.deepEqual([...sections], ['pdb-management-operator'])
  assert.equal(unknown, false)
})

test('parsePrFiles reads the GitHub PR files API, paginated or not', () => {
  const page = [
    { filename: 'charts/canvas-oda/values.yaml', patch: '@@ -1 +1 @@ x:' },
    { filename: 'charts/new-name/Chart.yaml', previous_filename: 'charts/old-name/Chart.yaml' },
    { filename: 'images/big.png' }
  ]
  for (const text of [JSON.stringify(page), JSON.stringify([page, [{ filename: 'README.md' }]])]) {
    const { files, patches } = parsePrFiles(text)
    assert.ok(files.includes('charts/old-name/Chart.yaml'))
    assert.ok(files.includes('charts/new-name/Chart.yaml'))
    assert.equal(patches.get('charts/canvas-oda/values.yaml'), '@@ -1 +1 @@ x:')
    assert.equal(patches.has('images/big.png'), false)
  }
})

test('canvas chart sections are checked against the chart', () => {
  const names = loadCanvasSectionNames({ canvasChart: ['charts/canvas-oda/values.yaml', 'charts/canvas-oda/Chart.yaml'] })
  for (const name of ['component-operator', 'global', 'kongnamespace', 'oda-crds', 'keycloak', 'chart-metadata']) assert.ok(names.has(name), name)
  const errors = checkSelection({
    ...context,
    config: { ...context.config, rules: [{ name: 'Typo', paths: ['charts/component-operator/**'], canvasSections: ['component-operatr'], tags: '@UC002' }] },
    trackedFiles: ['charts/component-operator/Chart.yaml', 'charts/canvas-oda/values.yaml', 'charts/canvas-oda/Chart.yaml', 'README.md', 'docs/a', 'images/a.png', 'charts/oda-crds/Chart.yaml']
  })
  assert.ok(errors.some(e => /canvas chart section "component-operatr"/.test(e)), errors.join('\n'))
})

test('step definitions are shared, so changing them runs the full suite', () => {
  const result = select(['feature-definition-and-test-kit/features/step-definition/PDBManagementSteps.js'])
  assert.equal(result.mode, 'full')
})

test('a documentation-only PR runs nothing', () => {
  const result = select(['README.md', 'docs/developer/guide.md', 'charts/component-operator/README.md', 'images/a.png'])
  assert.equal(result.mode, 'skip')
  assert.equal(result.reason, 'Documentation only.')
  assert.deepEqual(result.runs, [])
})

test('code the BDD suite does not install runs nothing', () => {
  const result = select(['canvas-portal-v2/backend/app.py', 'README.md'])
  assert.equal(result.mode, 'skip')
  assert.match(result.reason, /No changed path is covered/)
})

test('no changed files runs nothing', () => {
  assert.equal(select(['', '  ']).mode, 'skip')
})

test('documentation alongside code does not stop the selection', () => {
  const result = select(['charts/pdb-management-operator/values.yaml', 'charts/pdb-management-operator/README.md'])
  assert.equal(result.mode, 'selected')
  assert.match(result.tagExpression, /@UC017/)
})

test('a changed feature file runs that feature and the smoke test', () => {
  const result = select(['feature-definition-and-test-kit/features/UC007-F002-Dependent-APIs-Configure-Dependent-APIs-Single-Downstream.feature'])
  assert.equal(result.mode, 'selected')
  assert.equal(result.tagExpression, '(@UC002-F001) or (@UC007-F002)')
  assert.deepEqual(featureIds(run(result, 'default')), ['UC002-F001', 'UC007-F002'])
})

test('a deleted feature file runs only the smoke test', () => {
  const result = select(['feature-definition-and-test-kit/features/UC099-F001-Removed.feature'])
  assert.equal(result.mode, 'selected')
  assert.equal(result.tagExpression, '(@UC002-F001)')
})

test('a changed test chart runs the features that use it', () => {
  const result = select(['feature-definition-and-test-kit/testData/productcatalog-dynamic-roles-v1/values.yaml'])
  assert.equal(result.mode, 'selected')
  assert.deepEqual(featureIds(run(result, 'default')), ['UC002-F001', 'UC005-F002'])
})

test('chart names are matched as whole words', () => {
  // productcatalog-v1beta3 is a prefix of productcatalog-v1beta3-plugin
  const result = select(['feature-definition-and-test-kit/testData/productcatalog-v1beta3-plugin/values.yaml'])
  assert.deepEqual(result.runs.map(r => r.name), ['default', 'kong', 'apisix'])
  assert.deepEqual(featureIds(run(result, 'default')), ['UC002-F001'])
  assert.deepEqual(featureIds(run(result, 'kong')), ['UC015-F004'])
  assert.deepEqual(featureIds(run(result, 'apisix')), ['UC015-F003'])
})

test('a Kong change runs the Kong features on a Kong canvas', () => {
  const result = select(['source/operators/TMFOP002-API-Management/kong/docker/src/kongOperator.py'])
  assert.equal(result.mode, 'selected')
  assert.deepEqual(result.runs.map(r => r.name), ['default', 'kong'])
  assert.deepEqual(featureIds(run(result, 'default')), ['UC002-F001'])
  const kong = run(result, 'kong')
  assert.deepEqual(featureIds(kong), ['UC015-F002', 'UC015-F004'])
  assert.ok(kong.helmSet.includes('kong-gateway-install.enabled=true'))
  assert.ok(kong.helmSet.includes('api-operator-istio.enabled=false'))
})

test('an APISIX change runs the APISIX features on an APISIX canvas', () => {
  const result = select(['charts/apisix-gateway/values.yaml'])
  assert.deepEqual(result.runs.map(r => r.name), ['default', 'apisix'])
  const apisix = run(result, 'apisix')
  assert.deepEqual(featureIds(apisix), ['UC015-F001', 'UC015-F003'])
  assert.ok(apisix.helmSet.includes('apisix-gateway-install.enabled=true'))
})

test('the default run never includes gateway features', () => {
  const result = select(['feature-definition-and-test-kit/features/UC015-F002-Create-KongApiGateway-Route.feature'])
  assert.deepEqual(featureIds(run(result, 'default')), ['UC002-F001'])
  assert.deepEqual(featureIds(run(result, 'kong')), ['UC015-F002'])
})

test('a path that matches several rules runs all of them', () => {
  const result = select(['source/operators/TMFOP005-Dependency-Management/README.md', 'charts/canvas-info-service/values.yaml', 'charts/component-registry/values.yaml'])
  assert.equal(result.mode, 'selected')
  assert.equal(result.tagExpression, '(@UC002-F001) or (@UC007) or (@UC016)')
})

test('a rule with no tags runs only the smoke test', () => {
  const result = select(['charts/canvas-vault/values.yaml'])
  assert.equal(result.mode, 'selected')
  assert.equal(result.tagExpression, '(@UC002-F001)')
})

test('Windows path separators are normalised', () => {
  const result = select(['charts\\pdb-management-operator\\values.yaml'])
  assert.equal(result.paths[0].path, 'charts/pdb-management-operator/values.yaml')
  assert.equal(result.mode, 'selected')
})

test('checkSelection passes for the map and features in the repository', () => {
  const { execFileSync } = require('child_process')
  const path = require('path')
  const trackedFiles = execFileSync('git', ['ls-files'], { cwd: path.resolve(__dirname, '../..'), encoding: 'utf8' }).split('\n').filter(Boolean)
  assert.deepEqual(checkSelection({ ...context, trackedFiles }), [])
})

test('checkSelection reports broken tags, rules and charts', () => {
  const feature = (name, tags) => parseFeature(name, `${tags}\nFeature: x\n  Scenario: y\n    Given z\n`)
  const features = [
    feature('UC001-F001-A.feature', '@UC001 @UC001-F001'),
    feature('UC001-F002-B.feature', '@UC001 @UC001-F001'),
    feature('UC002-F001-C.feature', '@UC002 @UC002-F001'),
    feature('Unnamed.feature', '@UC003')
  ]
  const config = {
    smoke: '@UC001-F001',
    docs: ['**/*.md'],
    gateways: [{ name: 'kong', tag: '@KongGateway' }],
    rules: [
      { name: 'Covers UC001', paths: ['src/a/**'], tags: '@UC001' },
      { name: 'Bad expression', paths: ['src/missing/**'], tags: '@UC001 and (' }
    ]
  }
  const charts = ['chart-unused']
  const errors = checkSelection({ config, features, charts, usage: chartUsage(features, charts), trackedFiles: ['README.md', 'src/a/x.js'] })
  const expected = [
    /UC001-F002-B\.feature: missing feature-level tag @UC001-F002/,
    /UC001-F002-B\.feature: has feature tag @UC001-F001, which belongs to UC001-F001-A\.feature/,
    /Unnamed\.feature: file name doesn't start with UCnnn-Fnnn-/,
    /gateways\[0\] kong: missing helmSet/,
    /gateways\[0\] kong: tag expression "@KongGateway" selects no scenarios/,
    /rules\[1\] Bad expression: invalid tag expression/,
    /rule "Bad expression": "src\/missing\/\*\*" matches no file/,
    /testData\/chart-unused: no feature uses this chart/,
    /UC002-F001-C\.feature: no rule in test-selection\.yaml selects this feature/,
    /Unnamed\.feature: no rule in test-selection\.yaml selects this feature/
  ]
  for (const pattern of expected) {
    assert.ok(errors.some(e => pattern.test(e)), `expected an error matching ${pattern}, got:\n${errors.join('\n')}`)
  }
  assert.equal(errors.length, expected.length, errors.join('\n'))
})
