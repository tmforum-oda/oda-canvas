import React, { useState, useRef, useEffect } from 'react'
import { Select, Spin, Button, Tooltip, Switch } from 'antd'
import {
  DownloadOutlined,
  ReloadOutlined,
  VerticalAlignBottomOutlined,
} from '@ant-design/icons'
import { colors } from '@/theme'

interface StreamControls {
  onChunk: (text: string) => void
  onError?: (err: Error) => void
  onClose?: () => void
  tail: number
}

interface LogViewerProps {
  /** Async function that fetches a full log buffer for the given tail count */
  fetchLogs: (tail: number) => Promise<string>
  /** Optional: open a live tail stream. Return an AbortController to cancel. */
  streamLogs?: (opts: StreamControls) => AbortController
  /** Filename used when downloading */
  filename?: string
  title?: string
  initialTail?: number
}

const TAIL_OPTIONS = [
  { value: 50, label: '50 lines' },
  { value: 200, label: '200 lines' },
  { value: 500, label: '500 lines' },
  { value: 1000, label: '1000 lines' },
]

export default function LogViewer({
  fetchLogs,
  streamLogs,
  filename = 'pod-logs.txt',
  title,
  initialTail = 200,
}: LogViewerProps) {
  const [tail, setTail] = useState(initialTail)
  const [logs, setLogs] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [live, setLive] = useState(false)
  const [streamingActive, setStreamingActive] = useState(false)
  const logRef = useRef<HTMLPreElement>(null)
  const abortRef = useRef<AbortController | null>(null)
  const followBottomRef = useRef<boolean>(true)

  async function loadLogs(tailCount: number) {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchLogs(tailCount)
      setLogs(data)
    } catch (err: unknown) {
      const msg = (err as Error)?.message || 'Failed to load logs'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  function stopStream() {
    if (abortRef.current) {
      abortRef.current.abort()
      abortRef.current = null
    }
    setStreamingActive(false)
  }

  function startStream() {
    if (!streamLogs) return
    stopStream()
    setError(null)
    setLogs('')
    followBottomRef.current = true
    setStreamingActive(true)

    abortRef.current = streamLogs({
      tail,
      onChunk: (text) => {
        setLogs((prev) => prev + text)
        if (followBottomRef.current) {
          requestAnimationFrame(() => {
            if (logRef.current && followBottomRef.current) {
              logRef.current.scrollTop = logRef.current.scrollHeight
            }
          })
        }
      },
      onError: (err) => setError(err.message || 'Live stream error'),
      onClose: () => setStreamingActive(false),
    })
  }

  useEffect(() => {
    if (live) {
      startStream()
    } else {
      stopStream()
      loadLogs(tail)
    }
    return stopStream
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [live, tail])

  function scrollToBottom() {
    followBottomRef.current = true
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }

  function handleScroll() {
    if (!logRef.current) return
    const el = logRef.current
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 24
    followBottomRef.current = atBottom
  }

  function handleDownload() {
    const blob = new Blob([logs], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  function colorizeLogLine(line: string): React.ReactNode {
    if (/\b(error|err|fatal|panic|exception)\b/i.test(line)) {
      return <span style={{ color: colors.statusDown }}>{line}</span>
    }
    if (/\b(warn|warning)\b/i.test(line)) {
      return <span style={{ color: colors.statusDeprecated }}>{line}</span>
    }
    if (/\b(info|debug)\b/i.test(line)) {
      return <span style={{ color: colors.codeTextMuted }}>{line}</span>
    }
    return <span style={{ color: colors.codeText }}>{line}</span>
  }

  return (
    <div
      style={{
        background: colors.codeBg,
        border: `1px solid ${colors.border}`,
        borderRadius: 8,
        overflow: 'hidden',
      }}
    >
      {/* Toolbar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '10px 16px',
          borderBottom: `1px solid ${colors.border}`,
          background: colors.codeHeaderBg,
          gap: 12,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: streamingActive ? colors.statusLive : colors.textMuted,
              display: 'inline-block',
              boxShadow: streamingActive ? `0 0 8px ${colors.statusLive}` : 'none',
              animation: streamingActive ? 'logviewer-pulse 1.2s ease-in-out infinite' : 'none',
            }}
          />
          <span style={{ fontSize: 12, color: colors.textSecondary, fontFamily: 'monospace' }}>
            {title || 'Log Output'}
          </span>
          {streamingActive && (
            <span style={{ fontSize: 11, color: colors.statusLive, fontWeight: 700, letterSpacing: 0.6 }}>
              ● LIVE
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {streamLogs && (
            <Tooltip title={live ? 'Stop live tail' : 'Stream logs live (follow)'}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: 11, color: colors.textSecondary }}>Live</span>
                <Switch size="small" checked={live} onChange={setLive} />
              </span>
            </Tooltip>
          )}
          <Select
            value={tail}
            onChange={(v) => setTail(v)}
            options={TAIL_OPTIONS}
            size="small"
            style={{ width: 120 }}
            variant="outlined"
          />
          <Tooltip title={live ? 'Restart stream' : 'Refresh logs'}>
            <Button
              icon={<ReloadOutlined />}
              size="small"
              onClick={() => (live ? startStream() : loadLogs(tail))}
              loading={loading}
              style={{
                background: 'transparent',
                border: `1px solid ${colors.border}`,
                color: colors.textSecondary,
              }}
            />
          </Tooltip>
          <Tooltip title="Scroll to bottom">
            <Button
              icon={<VerticalAlignBottomOutlined />}
              size="small"
              onClick={scrollToBottom}
              style={{
                background: 'transparent',
                border: `1px solid ${colors.border}`,
                color: colors.textSecondary,
              }}
            />
          </Tooltip>
          <Tooltip title="Download logs">
            <Button
              icon={<DownloadOutlined />}
              size="small"
              onClick={handleDownload}
              disabled={!logs}
              style={{
                background: 'transparent',
                border: `1px solid ${colors.border}`,
                color: colors.textSecondary,
              }}
            />
          </Tooltip>
        </div>
      </div>

      {/* Log content */}
      <div style={{ position: 'relative', minHeight: 200, maxHeight: 480 }}>
        {loading && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(7,7,26,0.8)',
              zIndex: 1,
            }}
          >
            <Spin />
          </div>
        )}
        {error ? (
          <div
            style={{
              padding: 24,
              color: colors.statusDown,
              fontFamily: 'monospace',
              fontSize: 13,
            }}
          >
            Error: {error}
          </div>
        ) : (
          <pre
            ref={logRef}
            onScroll={handleScroll}
            style={{
              margin: 0,
              padding: '12px 16px',
              overflowY: 'auto',
              overflowX: 'auto',
              maxHeight: 480,
              fontFamily: "'Fira Code', 'Consolas', 'Monaco', monospace",
              fontSize: 12,
              lineHeight: 1.6,
              color: colors.codeText,
              background: 'transparent',
              whiteSpace: 'pre',
            }}
          >
            {logs
              ? logs.split('\n').map((line, idx) => (
                  <div key={idx}>{colorizeLogLine(line)}</div>
                ))
              : !loading && (
                  <span style={{ color: colors.textMuted }}>No log output available.</span>
                )}
          </pre>
        )}
      </div>

      {/* Footer */}
      <div
        style={{
          padding: '6px 16px',
          borderTop: `1px solid ${colors.border}`,
          background: colors.codeHeaderBg,
          fontSize: 11,
          color: colors.textMuted,
          display: 'flex',
          justifyContent: 'space-between',
        }}
      >
        <span>
          {live
            ? `Live · history ${tail} lines${streamingActive ? '' : ' (disconnected)'}`
            : `Showing last ${tail} lines`}
        </span>
        <span>{logs ? `${logs.split('\n').length} lines loaded` : '—'}</span>
      </div>

      <style>
        {`@keyframes logviewer-pulse { 0%, 100% { opacity: 1 } 50% { opacity: 0.45 } }`}
      </style>
    </div>
  )
}
