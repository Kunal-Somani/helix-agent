"use client"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { RunStatus, FinalStatus } from "@/lib/api"

interface Props {
  status: RunStatus
  finalStatus: FinalStatus
}

export function StatusBadge({ status, finalStatus }: Props) {
  if (status === "running") {
    return (
      <Badge className="bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center gap-1.5 hover:bg-blue-500/20 w-fit">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
        </span>
        Running
      </Badge>
    )
  }
  if (status === "queued") return <Badge variant="outline" className="text-yellow-400 border-yellow-500/30">Queued</Badge>
  if (finalStatus === "success") return <Badge className="bg-green-500/10 text-green-400 border border-green-500/20 hover:bg-green-500/20">Completed</Badge>
  if (finalStatus === "failed") return <Badge className="bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20">Failed</Badge>
  if (finalStatus === "error") return <Badge className="bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20">Error</Badge>
  return <Badge variant="outline">{status}</Badge>
}
