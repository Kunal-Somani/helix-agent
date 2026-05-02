"use client"
import { useParams, useRouter } from "next/navigation"
import { useQuery } from "@tanstack/react-query"
import { getRun } from "@/lib/api"
import { StatusBadge } from "@/components/StatusBadge"
import { IterationTimeline } from "@/components/IterationTimeline"
import { LogStream } from "@/components/LogStream"
import { calculateDuration, formatRelativeTime } from "@/lib/utils"
import { ChevronLeft, Clock, Cpu, FileJson, Activity } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"

export default function RunDetail() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string

  const { data: run, isLoading, isError } = useQuery({
    queryKey: ["run", id],
    queryFn: () => getRun(id),
    refetchInterval: 3000,
  })

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-slate-400 flex items-center gap-2">
          <Activity className="h-5 w-5 animate-spin" />
          Loading run details...
        </div>
      </div>
    )
  }

  if (isError || !run) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center gap-4">
        <div className="text-red-400">Failed to load run details.</div>
        <Button onClick={() => router.back()} variant="outline" className="border-slate-800 text-slate-300">
          Go Back
        </Button>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 flex flex-col">
      {/* Top Navigation */}
      <header className="border-b border-slate-800 bg-slate-900/50 px-6 py-4 sticky top-0 z-10 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto flex items-center gap-4">
          <Button 
            onClick={() => router.back()} 
            variant="ghost" 
            size="icon"
            className="text-slate-400 hover:text-slate-100 hover:bg-slate-800"
          >
            <ChevronLeft className="h-5 w-5" />
          </Button>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="text-lg font-mono tracking-tight text-slate-200">
                {run.id}
              </h1>
              <StatusBadge status={run.status} finalStatus={run.final_status} />
            </div>
            <div className="flex items-center gap-4 mt-1 text-sm text-slate-500">
              <div className="flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5" />
                {formatRelativeTime(run.started_at)} 
                <span className="text-slate-600 px-1">•</span>
                {calculateDuration(run.started_at, run.completed_at)}
              </div>
              <Badge variant="outline" className="bg-slate-900 border-slate-700 text-slate-400 font-normal">
                <Cpu className="h-3 w-3 mr-1.5" />
                claude-sonnet-4-20250514
              </Badge>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto w-full p-6 space-y-8">
        
        {/* Layout: Two columns */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Column (60%): Iterations */}
          <div className="lg:col-span-7 space-y-6">
            <h2 className="text-xl font-semibold text-slate-100 flex items-center gap-2">
              Execution Path
            </h2>
            <IterationTimeline iterations={run.iterations || []} />
          </div>

          {/* Right Column (40%): Live Logs */}
          <div className="lg:col-span-5 space-y-6">
            <div className="sticky top-28 space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
                  Live Logs
                  {run.status === "running" && (
                    <span className="relative flex h-2.5 w-2.5 ml-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500" />
                    </span>
                  )}
                </h2>
              </div>
              
              <LogStream runId={run.id} />

              <Collapsible className="border border-slate-800 rounded-lg bg-slate-900/30 overflow-hidden">
                <CollapsibleTrigger asChild>
                  <Button variant="ghost" className="w-full flex items-center justify-between p-4 h-auto text-slate-300 hover:text-slate-100 hover:bg-slate-800/50 rounded-none">
                    <span className="flex items-center gap-2">
                      <FileJson className="h-4 w-4" />
                      Raw Payload
                    </span>
                  </Button>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <div className="p-4 border-t border-slate-800 bg-slate-950">
                    <pre className="text-xs font-mono text-slate-400 overflow-x-auto">
                      {JSON.stringify(run, null, 2)}
                    </pre>
                  </div>
                </CollapsibleContent>
              </Collapsible>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
