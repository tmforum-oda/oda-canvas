#!/usr/bin/env node
'use strict'

// Formats a BDD test selection (the JSON from `select-features.js --format
// json`) as the Markdown of the PR comment and the job summary.
//
//   node test-selection/format-comment.js <selection.json> [<meta.json>]
//
// meta.json can add { skipReason, headSha, runUrl }. skipReason is set when
// trigger_test skips the tests whatever the selection, for example for
// `[skip tests]` in the PR title.
//
// This module has no dependencies, so the comment workflow can run it from
// the default branch without installing anything. Its input comes from the
// PR, so it treats every string in it as untrusted text.

const fs = require('fs')

const MARKER = '<!-- bdd-test-selection -->'
const MAX_PATHS = 100
const MAX_FEATURES = 200
const MAX_LENGTH = 60000

const CANVAS = { default: 'Istio', kong: 'Kong', apisix: 'APISIX' }

// Makes untrusted text safe inside an inline code span in a table cell.
function code (text) {
  const clean = String(text).replace(/[\r\n]+/g, ' ').replace(/`/g, "'").replace(/\|/g, '\\|').slice(0, 300)
  return '`' + clean + '`'
}

// Makes untrusted text safe as plain Markdown text.
function plain (text) {
  return String(text).replace(/[\r\n]+/g, ' ').replace(/[\\`*_[\]<>|#!]/g, c => '\\' + c).slice(0, 500)
}

function plural (n, word) {
  return `${n} ${word}${n === 1 ? '' : 's'}`
}

function headline (selection, meta) {
  const runs = selection.runs || []
  const features = runs.reduce((n, r) => n + (r.features || []).length, 0)
  const scenarios = runs.reduce((n, r) => n + (r.scenarios || 0), 0)
  if (meta.skipReason) return `**No BDD tests run:** ${plain(meta.skipReason)}.`
  if (selection.mode === 'skip') return `**No BDD tests run:** ${plain(selection.reason)}`
  const scope = `${plural(features, 'feature')}, ${plural(scenarios, 'scenario')}`
  const where = runs.length > 1 ? ` on ${runs.length} clusters (${runs.map(r => CANVAS[r.name] || plain(r.name)).join(', ')})` : ''
  if (selection.mode === 'full') return `**Full suite:** ${scope}${where}.`
  return `**Selected:** ${scope}${where}, chosen from the paths this PR changes.`
}

// The paths that caused a full run, with why.
function fullRunCauses (selection) {
  const causes = (selection.paths || []).filter(p => p.category === 'fullSuite' || p.category === 'unmapped')
  if (!causes.length) return selection.mode === 'full' ? [`The full suite was requested: ${plain(selection.reason)}`] : []
  const lines = ['The full suite runs because of these paths:', '']
  for (const p of causes.slice(0, MAX_PATHS)) {
    const why = p.category === 'fullSuite' ? 'always runs the full suite' : (p.matched || []).length ? plain(p.matched.join('; ')) : 'not in the test-selection map'
    lines.push(`- ${code(p.path)}: ${why}`)
  }
  if (causes.length > MAX_PATHS) lines.push(`- and ${causes.length - MAX_PATHS} more`)
  return lines
}

function runsTable (selection) {
  const runs = selection.runs || []
  if (!runs.length) return []
  const lines = ['| Run | Canvas | Features | Scenarios | Tag expression |', '| --- | --- | --- | --- | --- |']
  for (const run of runs) {
    const tags = run.tagExpression ? code(run.tagExpression) : '(all)'
    lines.push(`| ${plain(run.name)} | ${CANVAS[run.name] || plain(run.name)} | ${(run.features || []).length} | ${run.scenarios || 0} | ${tags} |`)
  }
  return lines
}

function featureList (selection) {
  const runs = (selection.runs || []).filter(r => (r.features || []).length)
  if (!runs.length) return []
  const total = runs.reduce((n, r) => n + r.features.length, 0)
  const lines = ['<details>', `<summary>Features in scope (${total})</summary>`, '']
  let shown = 0
  for (const run of runs) {
    if (shown >= MAX_FEATURES) break
    lines.push(`**${plain(run.name)}**`, '')
    for (const feature of run.features.slice(0, MAX_FEATURES - shown)) {
      lines.push(`- ${code(feature.name)} (${plural(feature.scenarios, 'scenario')})`)
      shown++
    }
    lines.push('')
  }
  if (total > shown) lines.push(`and ${total - shown} more`, '')
  lines.push('</details>')
  return lines
}

function pathTable (selection) {
  const paths = selection.paths || []
  if (!paths.length) return []
  const lines = ['<details>', `<summary>Changed paths (${paths.length})</summary>`, '', '| Path | Matched |', '| --- | --- |']
  for (const p of paths.slice(0, MAX_PATHS)) {
    const matched = (p.matched || []).length ? plain(p.matched.join(', ')) : 'not in the map'
    lines.push(`| ${code(p.path)} | ${p.category === 'unmapped' ? `**full suite:** ${matched}` : matched} |`)
  }
  if (paths.length > MAX_PATHS) lines.push(`| and ${paths.length - MAX_PATHS} more | |`)
  lines.push('', '</details>')
  return lines
}

function formatComment (selection, meta = {}) {
  const sections = [
    [MARKER, '### BDD test selection', '', headline(selection, meta)],
    meta.skipReason ? [] : selection.mode === 'full' ? fullRunCauses(selection) : [],
    meta.skipReason ? [] : runsTable(selection),
    meta.skipReason ? [] : featureList(selection),
    pathTable(selection)
  ]
  const footer = []
  if (meta.headSha && /^[0-9a-f]{7,40}$/i.test(meta.headSha)) footer.push(`for ${meta.headSha.slice(0, 7)}`)
  if (meta.runUrl && /^https:\/\/github\.com\/[\w.-]+\/[\w.-]+\/actions\/runs\/\d+$/.test(meta.runUrl)) footer.push(`[workflow run](${meta.runUrl})`)
  sections.push([`<sub>Selected by feature-definition-and-test-kit/test-selection.yaml${footer.length ? ' ' + footer.join(' · ') : ''}. This comment is updated on every push.</sub>`])

  let text = sections.filter(s => s.length).map(s => s.join('\n')).join('\n\n') + '\n'
  if (text.length > MAX_LENGTH) text = text.slice(0, MAX_LENGTH) + '\n\n(truncated)\n'
  return text
}

function main (argv) {
  if (!argv[0]) throw new Error('Usage: format-comment.js <selection.json> [<meta.json>]')
  const selection = JSON.parse(fs.readFileSync(argv[0], 'utf8'))
  const meta = argv[1] && fs.existsSync(argv[1]) ? JSON.parse(fs.readFileSync(argv[1], 'utf8')) : {}
  process.stdout.write(formatComment(selection, meta))
}

if (require.main === module) {
  try {
    main(process.argv.slice(2))
  } catch (err) {
    console.error(err.message)
    process.exitCode = 2
  }
}

module.exports = { MARKER, formatComment }
