"use client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Activity, CheckCircle2, List, Percent } from "lucide-react"
import type { Run } from "@/lib/api"

interface Props {
  runs: Run[]
}

export function StatsCards({ runs }: Props) {
  const total = runs.length
  const completed = runs.filter((r) => r.final_status === "success").length
  const active = runs.filter((r) => r.status === "running" || r.status === "queued").length
  const successRate = total > 0 ? Math.round((completed / total) * 100) : 0

  return (
    <div className="flex flex-col gap-4">
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-400">Total Runs</CardTitle>
          <List className="h-4 w-4 text-slate-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-slate-100">{total}</div>
        </CardContent>
      </Card>

      <Card className="bg-slate-900 border-slate-800">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-400">Completed</CardTitle>
          <CheckCircle2 className="h-4 w-4 text-green-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-slate-100">{completed}</div>
        </CardContent>
      </Card>

      <Card className="bg-slate-900 border-slate-800">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-400">Success Rate</CardTitle>
          <Percent className="h-4 w-4 text-amber-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-slate-100">{successRate}%</div>
        </CardContent>
      </Card>

      <Card className="bg-slate-900 border-slate-800">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-slate-400">Active Now</CardTitle>
          <Activity className="h-4 w-4 text-blue-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-slate-100">{active}</div>
        </CardContent>
      </Card>
    </div>
  )
}
