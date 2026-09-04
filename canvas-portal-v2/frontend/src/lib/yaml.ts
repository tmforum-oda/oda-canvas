function isPlainObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value)
}

function isYamlBareString(value: string) {
  if (!value) return false
  if (/^(true|false|null|undefined|nan|inf|-inf|yes|no|on|off|y|n|~)$/i.test(value)) return false
  if (/^-?\d+(\.\d+)?$/.test(value)) return false
  if (/^\d{4}-\d{2}-\d{2}([T\s].*)?$/.test(value)) return false
  if (/^[-?:,[\]{}#&*!|>'"%@`]/.test(value)) return false
  return /^[A-Za-z0-9_./:@-]+$/.test(value)
}

function formatScalar(value: unknown) {
  if (value === null || value === undefined) return 'null'
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  if (typeof value === 'string' && isYamlBareString(value)) return value
  return JSON.stringify(String(value))
}

export function toYaml(value: unknown, indent = 0): string {
  const padding = ' '.repeat(indent)

  if (Array.isArray(value)) {
    if (value.length === 0) return `${padding}[]`
    return value
      .map((item) => {
        if (Array.isArray(item) || isPlainObject(item)) {
          return `${padding}-\n${toYaml(item, indent + 2)}`
        }
        return `${padding}- ${formatScalar(item)}`
      })
      .join('\n')
  }

  if (isPlainObject(value)) {
    const entries = Object.entries(value)
    if (entries.length === 0) return `${padding}{}`
    return entries
      .map(([key, item]) => {
        if (Array.isArray(item) || isPlainObject(item)) {
          return `${padding}${key}:\n${toYaml(item, indent + 2)}`
        }
        return `${padding}${key}: ${formatScalar(item)}`
      })
      .join('\n')
  }

  return `${padding}${formatScalar(value)}`
}
