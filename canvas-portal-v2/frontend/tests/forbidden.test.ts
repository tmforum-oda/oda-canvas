// Run with `npm test` (Node's built-in test runner, Node 22.6 or later).
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { adminAccessMessage, isForbiddenError } from '../src/lib/forbidden.ts'

test('isForbiddenError is true for a 403 response', () => {
  assert.equal(isForbiddenError({ response: { status: 403, data: { detail: 'nope' } } }), true)
})

test('isForbiddenError is false for other errors', () => {
  assert.equal(isForbiddenError({ response: { status: 401 } }), false)
  assert.equal(isForbiddenError({ response: { status: 404 } }), false)
  assert.equal(isForbiddenError({ response: { status: 500 } }), false)
  assert.equal(isForbiddenError({ response: { status: '403' } }), false)
  assert.equal(isForbiddenError(new Error('Network Error')), false)
  assert.equal(isForbiddenError(null), false)
  assert.equal(isForbiddenError(undefined), false)
  assert.equal(isForbiddenError('403'), false)
})

test('adminAccessMessage names the feature, the default admin group and the setting', () => {
  const text = adminAccessMessage('Deploying components with Helm')
  assert.match(text, /^Deploying components with Helm is limited to Canvas admins\./)
  assert.match(text, /"canvas-admin" group/)
  assert.match(text, /"canvas-admin" realm role/)
  assert.match(text, /backend\.auth\.adminGroups/)
  assert.match(text, /sign out and sign in again/)
})
