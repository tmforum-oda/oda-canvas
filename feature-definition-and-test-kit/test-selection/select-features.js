#!/usr/bin/env node
'use strict'

// Selects the BDD features a pull request should run, from the paths it
// changes and the map in ../test-selection.yaml. See that file for the rules.
//
//   node test-selection/select-features.js --base origin/main
//   git diff --name-only main | node test-selection/select-features.js --files -
//   node test-selection/select-features.js --check

const fs = require('fs')
const path = require('path')
const { execFileSync } = require('child_process')
const YAML = require('yaml')
const { Parser, AstBuilder, GherkinClassicTokenMatcher, compile } = require('@cucumber/gherkin')
const { IdGenerator } = require('@cucumber/messages')
const parseTagExpression = require('@cucumber/tag-expressions').default
const { formatComment } = require('./format-comment')

const KIT_DIR = path.resolve(__dirname, '..')
const REPO_ROOT = path.resolve(KIT_DIR, '..')
const KIT_PATH = path.relative(REPO_ROOT, KIT_DIR).split(path.sep).join('/')
const CONFIG_FILE = path.join(KIT_DIR, 'test-selection.yaml')

// Converts a path glob to a RegExp: `*` matches within one path segment,
// `**` matches any number of segments and `?` matches one character. Matching
// ignores case, so `**/*.png` also matches `Issues.PNG`.
function globToRegExp (glob) {
  let re = ''
  for (let i = 0; i < glob.length; i++) {
    const c = glob[i]
    if (c === '*' && glob[i + 1] === '*') {
      i++
      if (glob[i + 1] === '/') {
        i++
        re += '(?:.*/)?'
      } else {
        re += '.*'
      }
    } else if (c === '*') {
      re += '[^/]*'
    } else if (c === '?') {
      re += '[^/]'
    } else {
      re += c.replace(/[.+^${}()|[\]\\]/g, '\\$&')
    }
  }
  return new RegExp('^' + re + '$', 'i')
}

function matchesAny (file, globs) {
  return (globs || []).some(glob => globToRegExp(glob).test(file))
}

function loadConfig (file = CONFIG_FILE) {
  return YAML.parse(fs.readFileSync(file, 'utf8'))
}

function parseFeature (name, text) {
  const newId = IdGenerator.uuid()
  const doc = new Parser(new AstBuilder(newId), new GherkinClassicTokenMatcher()).parse(text)
  return {
    name,
    path: `${KIT_PATH}/features/${name}`,
    featureTags: doc.feature ? doc.feature.tags.map(t => t.name) : [],
    scenarioTags: compile(doc, name, newId).map(p => p.tags.map(t => t.name)),
    text
  }
}

function loadFeatures (kitDir = KIT_DIR) {
  const dir = path.join(kitDir, 'features')
  return fs.readdirSync(dir)
    .filter(name => name.endsWith('.feature'))
    .sort()
    .map(name => parseFeature(name, fs.readFileSync(path.join(dir, name), 'utf8')))
}

function loadCharts (kitDir = KIT_DIR) {
  const dir = path.join(kitDir, 'testData')
  return fs.readdirSync(dir, { withFileTypes: true })
    .filter(entry => entry.isDirectory())
    .map(entry => entry.name)
    .sort()
}

// `UC015-F002-Create-KongApiGateway-Route.feature` -> `@UC015-F002`
function featureTagFromName (name) {
  const match = /^(UC\d+-F\d+)-/.exec(name)
  return match ? '@' + match[1] : null
}

// Returns a Map of chart name -> names of the features that use it. A feature
// uses a chart when the chart name appears as a whole word in it, for example
// as a table cell or a quoted step argument.
function chartUsage (features, charts) {
  const usage = new Map(charts.map(chart => [chart, []]))
  for (const feature of features) {
    const words = new Set(feature.text.split(/[\s|'"`,()]+/))
    for (const chart of charts) {
      if (words.has(chart)) usage.get(chart).push(feature.name)
    }
  }
  return usage
}

// Returns the features with at least one scenario that the tag expression
// selects, and their number of selected scenarios.
function featuresInScope (features, tagExpression) {
  const node = tagExpression ? parseTagExpression(tagExpression) : null
  return features
    .map(feature => ({
      name: feature.name,
      scenarios: feature.scenarioTags.filter(tags => !node || node.evaluate(tags)).length
    }))
    .filter(feature => feature.scenarios > 0)
}

function classifyPath (file, context) {
  const { config, features, usage } = context
  if (matchesAny(file, config.docs)) return { path: file, category: 'docs', matched: ['documentation'], tags: [] }
  if (matchesAny(file, config.noTests)) return { path: file, category: 'noTests', matched: ['no BDD features'], tags: [] }
  if (matchesAny(file, config.fullSuite)) return { path: file, category: 'fullSuite', matched: ['full suite'], tags: [] }
  if ((config.canvasChart || []).includes(file)) return classifyCanvasChartPath(file, context)

  const featurePrefix = `${KIT_PATH}/features/`
  if (file.startsWith(featurePrefix) && file.endsWith('.feature') && !file.slice(featurePrefix.length).includes('/')) {
    const name = file.slice(featurePrefix.length)
    const tag = featureTagFromName(name)
    if (tag) {
      const exists = features.some(feature => feature.name === name)
      return { path: file, category: 'feature', matched: [exists ? `feature ${tag}` : 'deleted feature'], tags: exists ? [tag] : [] }
    }
  }

  const chartMatch = new RegExp(`^${KIT_PATH}/testData/([^/]+)/`).exec(file)
  if (chartMatch) {
    const users = usage.get(chartMatch[1]) || []
    return {
      path: file,
      category: 'testData',
      matched: [users.length ? `test chart ${chartMatch[1]}` : `test chart ${chartMatch[1]} (no feature uses it)`],
      tags: users.map(featureTagFromName)
    }
  }

  const rules = (config.rules || []).filter(rule => matchesAny(file, rule.paths))
  if (rules.length) {
    return { path: file, category: 'rule', matched: rules.map(rule => rule.name), tags: rules.map(rule => rule.tags).filter(Boolean) }
  }

  return { path: file, category: 'unmapped', matched: [], tags: [] }
}

const TOP_LEVEL_KEY = /^([A-Za-z0-9_.-]+)\s*:/
const DEPENDENCY_NAME = /^\s*-\s+name:\s*['"]?([^'"\s#]+)/

// Returns the sections of a canvas-oda chart file that a unified diff changes.
// In values.yaml a section is a top-level key, such as `component-operator`.
// In Chart.yaml it's the name of a dependency, or `chart-metadata` for the
// chart's own fields, such as its version. Blank and comment-only lines are
// ignored. `unknown` is true when a changed line can't be placed in a section.
function changedSections (patch, isChartYaml) {
  const sections = new Set()
  let unknown = false
  let inHunk = false
  let top = null
  let dependency = null
  for (const line of patch.split(/\r?\n/)) {
    const hunk = /^@@ [^@]* @@ ?(.*)$/.exec(line)
    if (hunk) {
      // git puts the last top-level line before the hunk in its header
      const key = TOP_LEVEL_KEY.exec(hunk[1])
      top = key ? key[1] : null
      dependency = null
      inHunk = true
      continue
    }
    if (!inHunk || !line || !' +-'.includes(line[0])) continue
    const marker = line[0]
    const text = line.slice(1)
    const key = TOP_LEVEL_KEY.exec(text)
    if (key) {
      top = key[1]
      dependency = null
    }
    const name = DEPENDENCY_NAME.exec(text)
    if (name && top === 'dependencies') dependency = name[1]
    if (marker === ' ' || /^\s*(#.*)?$/.test(text)) continue

    if (isChartYaml && top === 'dependencies' && !key) {
      if (dependency) sections.add(dependency)
      else unknown = true
    } else if (isChartYaml) {
      sections.add(top === 'dependencies' ? 'dependencies' : 'chart-metadata')
    } else if (top) {
      sections.add(top)
    } else {
      unknown = true
    }
  }
  return { sections, unknown }
}

// Classifies a change to a canvas-oda chart file by the sections it changes,
// so that bumping one operator's values runs that operator's features. A
// section that no rule lists, or a change without a diff, runs the full suite.
function classifyCanvasChartPath (file, context) {
  const unmapped = reason => ({ path: file, category: 'unmapped', matched: [reason], tags: [] })
  const patch = context.patches && context.patches.get(file)
  if (typeof patch !== 'string') return unmapped('canvas chart file, but no diff was available')

  const { sections, unknown } = changedSections(patch, /(^|\/)Chart\.yaml$/.test(file))
  if (unknown) return unmapped('canvas chart lines outside any section')
  if (!sections.size) return { path: file, category: 'noTests', matched: ['comments or blank lines only'], tags: [] }

  const rules = (context.config.rules || []).filter(rule => (rule.canvasSections || []).some(s => sections.has(s)))
  const listed = new Set(rules.flatMap(rule => rule.canvasSections))
  const unlisted = [...sections].filter(s => !listed.has(s)).sort()
  if (unlisted.length) return unmapped(`canvas chart sections not in the map: ${unlisted.join(', ')}`)

  return {
    path: file,
    category: 'rule',
    matched: rules.map(rule => `${rule.name} (${rule.canvasSections.filter(s => sections.has(s)).join(', ')})`),
    tags: rules.map(rule => rule.tags).filter(Boolean)
  }
}

// Reads the output of the GitHub "list pull request files" API, saved by
// `gh api --paginate --slurp`, or a single page of it. Returns the changed
// paths (renamed files under both names) and a Map of path -> patch.
function parsePrFiles (text) {
  const parsed = JSON.parse(text)
  const entries = Array.isArray(parsed) ? parsed.flat() : []
  const files = []
  const patches = new Map()
  for (const entry of entries) {
    files.push(entry.filename)
    if (entry.previous_filename) files.push(entry.previous_filename)
    if (typeof entry.patch === 'string') patches.set(entry.filename, entry.patch)
  }
  return { files, patches }
}

// Splits a selection into runs: the default run on the Istio canvas, and one
// run for each gateway in the map that has features in scope. A null
// selection means every feature. Runs with no scenarios are left out.
function buildRuns (selection, context) {
  const gateways = context.config.gateways || []
  const base = selection ? `(${selection})` : null
  const defaultExpression = [base, ...gateways.map(g => `not ${g.tag}`)].filter(Boolean).join(' and ')
  const runs = [
    { name: 'default', helmSet: [], preInstall: [], tagExpression: defaultExpression || null },
    ...gateways.map(g => ({
      name: g.name,
      helmSet: g.helmSet || [],
      preInstall: g.preInstall || [],
      tagExpression: base ? `${base} and ${g.tag}` : g.tag
    }))
  ]
  return runs
    .map(run => {
      const features = featuresInScope(context.features, run.tagExpression)
      return { ...run, features, scenarios: features.reduce((n, f) => n + f.scenarios, 0) }
    })
    .filter(run => run.scenarios > 0)
}

// Works out which features to run for a list of changed paths.
//
// Returns { mode, reason, tagExpression, paths, runs, scenarios }, where mode
// is 'skip' (no runs), 'selected' (the features tagExpression selects) or
// 'full' (every feature; tagExpression is null). Each run has its own
// tagExpression, the helmSet values and preInstall commands for its canvas,
// and its features in scope.
function selectFeatures (changedFiles, context) {
  const files = [...new Set(changedFiles.map(f => f.trim().replace(/\\/g, '/')).filter(Boolean))].sort()
  const paths = files.map(file => classifyPath(file, context))
  const result = (mode, reason, tagExpression) => {
    const runs = mode === 'skip' ? [] : buildRuns(tagExpression, context)
    return { mode, reason, tagExpression, paths, runs, scenarios: runs.reduce((n, r) => n + r.scenarios, 0) }
  }

  if (!paths.length) return result('skip', 'No changed files.', null)

  const crdPaths = paths.filter(p => p.category === 'fullSuite')
  const unmapped = paths.filter(p => p.category === 'unmapped')
  if (crdPaths.length || unmapped.length) {
    const reasons = []
    if (crdPaths.length) reasons.push(`${crdPaths.length} changed path(s) always run the full suite: ${crdPaths.map(p => p.path).join(', ')}`)
    if (unmapped.length) {
      const described = unmapped.map(p => p.matched.length ? `${p.path} (${p.matched.join('; ')})` : p.path)
      reasons.push(`${unmapped.length} changed path(s) aren't in the test-selection map: ${described.join(', ')}`)
    }
    return result('full', 'Full suite. ' + reasons.join('. ') + '.', null)
  }

  if (paths.every(p => p.category === 'docs')) return result('skip', 'Documentation only.', null)
  if (paths.every(p => p.category === 'docs' || p.category === 'noTests')) {
    return result('skip', 'No changed path is covered by the BDD features.', null)
  }

  const expressions = [...new Set([context.config.smoke, ...paths.flatMap(p => p.tags)])]
  const tagExpression = expressions.map(e => `(${e})`).join(' or ')
  return result('selected', 'Selected from the test-selection map, plus the smoke test.', tagExpression)
}

// A full run of every feature, whatever changed. Used for on-demand runs.
function selectAll (reason, context) {
  const runs = buildRuns(null, context)
  return { mode: 'full', reason, tagExpression: null, paths: [], runs, scenarios: runs.reduce((n, r) => n + r.scenarios, 0) }
}

// Checks the map and the feature files. Returns a list of error messages.
function checkSelection (context) {
  const { config, features, charts, usage, trackedFiles } = context
  const errors = []
  const selects = (expression, label) => {
    try {
      if (!featuresInScope(features, expression).length) errors.push(`${label}: tag expression "${expression}" selects no scenarios`)
    } catch (err) {
      errors.push(`${label}: invalid tag expression "${expression}": ${err.message}`)
    }
  }

  // Each feature file carries its own use case and feature tags, and no other
  // feature file uses the same feature tag.
  for (const feature of features) {
    const tag = featureTagFromName(feature.name)
    if (!tag) {
      errors.push(`${feature.name}: file name doesn't start with UCnnn-Fnnn-`)
      continue
    }
    for (const required of [tag.split('-')[0], tag]) {
      if (!feature.featureTags.includes(required)) errors.push(`${feature.name}: missing feature-level tag ${required}`)
    }
    for (const other of features) {
      if (other !== feature && other.featureTags.includes(tag)) errors.push(`${other.name}: has feature tag ${tag}, which belongs to ${feature.name}`)
    }
  }

  if (!config.smoke) errors.push('smoke: missing')
  else selects(config.smoke, 'smoke')

  for (const [index, gateway] of (config.gateways || []).entries()) {
    const label = `gateways[${index}] ${gateway.name || '(no name)'}`
    if (!gateway.name) errors.push(`${label}: missing name`)
    if (!gateway.helmSet || !gateway.helmSet.length) errors.push(`${label}: missing helmSet`)
    if (!gateway.tag) errors.push(`${label}: missing tag`)
    else selects(gateway.tag, label)
  }

  const knownSections = context.canvasSectionNames || new Set()
  for (const [index, rule] of (config.rules || []).entries()) {
    const label = `rules[${index}] ${rule.name || '(no name)'}`
    if (!rule.name) errors.push(`${label}: missing name`)
    if (!rule.paths || !rule.paths.length) errors.push(`${label}: missing paths`)
    if (rule.tags) selects(rule.tags, label)
    for (const section of rule.canvasSections || []) {
      if (!knownSections.has(section)) errors.push(`${label}: canvas chart section "${section}" isn't a top-level key or dependency in ${(config.canvasChart || []).join(' or ')}`)
    }
  }

  // Every glob matches a tracked file, so a renamed or removed path is noticed.
  const sections = [
    ['docs', config.docs],
    ['noTests', config.noTests],
    ['fullSuite', config.fullSuite],
    ['canvasChart', config.canvasChart],
    ...(config.rules || []).map(rule => [`rule "${rule.name}"`, rule.paths])
  ]
  for (const [label, globs] of sections) {
    for (const glob of globs || []) {
      const re = globToRegExp(glob)
      if (!trackedFiles.some(file => re.test(file))) errors.push(`${label}: "${glob}" matches no file in the repository`)
    }
  }

  for (const chart of charts) {
    if (!usage.get(chart).length) errors.push(`testData/${chart}: no feature uses this chart`)
  }

  // Every feature is selected by some rule, so a new feature can't be left
  // out of the runs for the code it tests. Features with no scenarios yet
  // are placeholders and are skipped.
  const ruleTags = (config.rules || []).map(rule => rule.tags).filter(Boolean)
  for (const feature of features.filter(f => f.scenarioTags.length)) {
    const covered = ruleTags.some(expression => {
      try {
        return feature.scenarioTags.some(tags => parseTagExpression(expression).evaluate(tags))
      } catch (err) {
        return false
      }
    })
    if (!covered) errors.push(`${feature.name}: no rule in test-selection.yaml selects this feature`)
  }

  return errors
}

function git (args) {
  return execFileSync('git', args, { cwd: REPO_ROOT, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 })
}

// The section names a rule can list in canvasSections: the top-level keys of
// the canvas chart's values files, the dependency names in its Chart.yaml,
// and `chart-metadata`.
function loadCanvasSectionNames (config, repoRoot = REPO_ROOT) {
  const names = new Set(['chart-metadata'])
  for (const file of config.canvasChart || []) {
    const fullPath = path.join(repoRoot, file)
    if (!fs.existsSync(fullPath)) continue
    const doc = YAML.parse(fs.readFileSync(fullPath, 'utf8')) || {}
    if (/(^|\/)Chart\.yaml$/.test(file)) {
      for (const dependency of doc.dependencies || []) names.add(dependency.name)
    } else {
      for (const key of Object.keys(doc)) names.add(key)
    }
  }
  return names
}

function loadContext () {
  const config = loadConfig()
  const features = loadFeatures()
  const charts = loadCharts()
  return { config, features, charts, usage: chartUsage(features, charts), canvasSectionNames: loadCanvasSectionNames(config) }
}

function formatText (result) {
  const lines = [`Mode: ${result.mode}`, `Reason: ${result.reason}`]
  if (result.tagExpression) lines.push(`Tag expression: ${result.tagExpression}`)
  lines.push('', 'Changed paths:')
  for (const p of result.paths) {
    const matched = p.matched.length ? p.matched.join(', ') : 'not in the map'
    lines.push(`  ${p.path}  ->  ${p.category === 'unmapped' ? `full suite: ${matched}` : matched}`)
  }
  for (const run of result.runs) {
    lines.push('', `Run "${run.name}" (${run.features.length} features, ${run.scenarios} scenarios)`)
    lines.push(`  Tag expression: ${run.tagExpression || '(all)'}`)
    for (const command of run.preInstall) lines.push(`  Before the canvas install: ${command}`)
    if (run.helmSet.length) lines.push(`  Canvas install: --set ${run.helmSet.join(' --set ')}`)
    for (const f of run.features) lines.push(`  ${f.name} (${f.scenarios})`)
  }
  return lines.join('\n')
}

// Step outputs for trigger_tests.yml, as name=value lines for $GITHUB_OUTPUT.
// GATEWAY_RUNS is the matrix for the gateway runs, one entry per run.
function formatGithubOutput (result) {
  const defaultRun = result.runs.find(run => run.name === 'default')
  const gatewayRuns = result.runs
    .filter(run => run.name !== 'default')
    .map(run => ({ name: run.name, tags: run.tagExpression || '', helmSet: run.helmSet.join('\n'), preInstall: run.preInstall.join('\n') }))
  return [
    `MODE=${result.mode}`,
    `RUN_DEFAULT=${Boolean(defaultRun)}`,
    `DEFAULT_TAGS=${(defaultRun && defaultRun.tagExpression) || ''}`,
    `GATEWAY_RUNS=${JSON.stringify(gatewayRuns)}`
  ].join('\n')
}

const FORMATTERS = {
  text: formatText,
  json: result => JSON.stringify(result, null, 2),
  'github-output': formatGithubOutput,
  markdown: result => formatComment(result)
}

function parseArgs (argv) {
  const args = { format: 'text' }
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i]
    if (arg === '--check') args.check = true
    else if (arg === '--all') args.all = true
    else if (arg === '--base') args.base = argv[++i]
    else if (arg === '--files') args.files = argv[++i]
    else if (arg === '--pr-files') args.prFiles = argv[++i]
    else if (arg === '--format') args.format = argv[++i]
    else throw new Error(`Unknown argument: ${arg}`)
  }
  if (!FORMATTERS[args.format]) throw new Error(`Unknown format: ${args.format}`)
  if (!args.check && !args.all && !args.base && !args.files && !args.prFiles) {
    throw new Error('Pass --base <ref>, --files <file|->, --pr-files <file>, --all or --check')
  }
  return args
}

// Reads the changed paths, and the diffs of the canvas chart files, from the
// arguments: a git ref to diff against, a GitHub PR files API response, or a
// plain list of paths (which has no diffs, so a canvas chart change in it runs
// the full suite).
function readChanges (args, config) {
  if (args.prFiles) return parsePrFiles(fs.readFileSync(args.prFiles, 'utf8'))
  if (args.files) {
    return { files: fs.readFileSync(args.files === '-' ? 0 : args.files, 'utf8').split(/\r?\n/), patches: new Map() }
  }
  const range = `${args.base}...HEAD`
  const files = git(['diff', '--name-only', '--no-renames', range]).split('\n').filter(Boolean)
  const patches = new Map()
  for (const file of files.filter(f => (config.canvasChart || []).includes(f))) {
    patches.set(file, git(['diff', '--no-renames', range, '--', file]))
  }
  return { files, patches }
}

function main (argv) {
  const args = parseArgs(argv)
  const context = loadContext()

  if (args.check) {
    const errors = checkSelection({ ...context, trackedFiles: git(['ls-files']).split('\n').filter(Boolean) })
    if (errors.length) {
      console.error(`test-selection check failed (${errors.length}):`)
      for (const error of errors) console.error(`  - ${error}`)
      return 1
    }
    console.log(`test-selection check passed: ${context.features.length} features, ${(context.config.rules || []).length} rules, ${context.charts.length} test charts.`)
    return 0
  }

  let result
  if (args.all) {
    result = selectAll('Full suite requested.', context)
  } else {
    const { files, patches } = readChanges(args, context.config)
    result = selectFeatures(files, { ...context, patches })
  }
  console.log(FORMATTERS[args.format](result))
  return 0
}

if (require.main === module) {
  try {
    process.exitCode = main(process.argv.slice(2))
  } catch (err) {
    console.error(err.message)
    process.exitCode = 2
  }
}

module.exports = {
  globToRegExp,
  changedSections,
  parsePrFiles,
  loadCanvasSectionNames,
  parseFeature,
  loadContext,
  featureTagFromName,
  chartUsage,
  featuresInScope,
  buildRuns,
  selectFeatures,
  selectAll,
  formatGithubOutput,
  checkSelection
}
