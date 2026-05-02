"use client"
import { useEffect, useState, useRef } from "react"
import { Terminal } from "lucide-react"

export function LogStream({ runId }: { runId: string }) {
  const [lines, setLines] = useState<string[]>([])
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const url = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/runs/${runId}/logs`
    const eventSource = new EventSource(url)

    eventSource.onmessage = (event) => {
      setLines((prev) => {
        const newLines = [...prev, event.data]
        return newLines.slice(-200) // Cap at 200
      })
    }

    eventSource.onerror = (error) => {
      console.error("EventSource failed:", error)
      eventSource.close()
    }

    return () => {
      eventSource.close()
    }
  }, [runId])

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [lines])

  const getLineColor = (line: string) => {
    const lower = line.toLowerCase()
    if (lower.includes("error")) return "text-red-400"
    if (lower.includes("warning")) return "text-yellow-400"
    if (line.includes("[DONE]")) return "text-green-400"
    return "text-slate-400"
  }

  return (
    <div className="flex flex-col rounded-lg border border-slate-800 overflow-hidden bg-black/80">
      <div className="flex items-center gap-2 px-4 py-2 border-b border-slate-800 bg-slate-900/50">
        <Terminal className="h-4 w-4 text-slate-500" />
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Live Logs</span>
      </div>
      
      <div 
        ref={containerRef}
        className="h-64 overflow-y-auto p-4 font-mono text-xs space-y-1 scroll-smooth"
      >
        {lines.length === 0 ? (
          <div className="text-slate-600 italic">Waiting for logs...</div>
        ) : (
          lines.map((line, i) => (
            <div key={i} className={`${getLineColor(line)} break-words whitespace-pre-wrap`}>
              {line}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
