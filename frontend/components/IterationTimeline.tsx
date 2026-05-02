"use client"
import type { Iteration } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Check, X, CornerDownRight } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"

export function IterationTimeline({ iterations }: { iterations: Iteration[] }) {
  if (!iterations || iterations.length === 0) {
    return (
      <div className="space-y-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex gap-4">
            <div className="w-1 bg-slate-800 rounded-full" />
            <div className="flex-1 space-y-3 p-4 bg-slate-900/50 border border-slate-800 rounded-lg">
              <Skeleton className="h-4 w-1/4 bg-slate-800" />
              <Skeleton className="h-8 w-full bg-slate-800" />
              <Skeleton className="h-4 w-3/4 bg-slate-800" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {iterations.map((it, i) => (
        <div key={i} className="flex gap-4">
          <div className={`w-1 rounded-full ${it.correct ? 'bg-green-500/50' : 'bg-red-500/50'}`} />
          <div className="flex-1 space-y-3 p-4 bg-slate-900 border border-slate-800 rounded-lg shadow-sm">
            <div className="flex items-center justify-between">
              <Badge variant="outline" className="bg-slate-950 text-slate-300 border-slate-700">
                Step {it.step}
              </Badge>
              <Badge className={it.correct 
                ? "bg-green-500/10 text-green-400 border border-green-500/20" 
                : "bg-red-500/10 text-red-400 border border-red-500/20"
              }>
                {it.correct ? <Check className="w-3 h-3 mr-1" /> : <X className="w-3 h-3 mr-1" />}
                {it.correct ? "Correct" : "Wrong"}
              </Badge>
            </div>
            
            <div className="text-xs font-mono text-slate-400 break-all bg-slate-950 px-2 py-1 rounded border border-slate-800">
              {it.url}
            </div>

            <div className="font-mono text-sm text-slate-200 bg-slate-950 p-3 rounded-md border border-slate-800 whitespace-pre-wrap">
              {it.answer}
            </div>

            {it.explanation && (
              <div className="text-sm text-slate-400 leading-relaxed">
                {it.explanation}
              </div>
            )}

            {it.next_url && (
              <div className="flex items-center gap-2 text-xs text-blue-400 mt-2">
                <CornerDownRight className="w-3 h-3" />
                <span className="font-mono truncate">{it.next_url}</span>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
