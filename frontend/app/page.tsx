"use client"
import { useQuery } from "@tanstack/react-query"
import { getRuns, getHealth } from "@/lib/api"
import { StatsCards } from "@/components/StatsCards"
import { RunsTable } from "@/components/RunsTable"
import { SubmitForm } from "@/components/SubmitForm"
import { Activity, Server } from "lucide-react"

export default function Dashboard() {
  const { data: runs = [], isLoading: runsLoading } = useQuery({
    queryKey: ["runs"],
    queryFn: getRuns,
    refetchInterval: 4000,
  })

  const { data: health, isLoading: healthLoading, isError: healthError } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 10000,
    retry: false,
  })

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 flex flex-col">
      {/* Top Navigation */}
      <header className="border-b border-slate-800 bg-slate-900/50 px-6 py-4 sticky top-0 z-10 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-blue-500/20 p-2 rounded-lg border border-blue-500/30">
              <Activity className="h-5 w-5 text-blue-400" />
            </div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
              QuizSolver AI
            </h1>
          </div>
          
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-slate-800 bg-slate-900 text-sm">
            <Server className="h-4 w-4 text-slate-400" />
            {healthLoading ? (
              <span className="text-slate-400">Checking...</span>
            ) : healthError ? (
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-red-500"></span>
                <span className="text-red-400 font-medium">API Offline</span>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-green-500"></span>
                <span className="text-green-400 font-medium">API Online ({health.version || 'v1.0'})</span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto w-full p-6 space-y-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left Column (60%) */}
          <div className="lg:col-span-7 space-y-8">
            <SubmitForm />
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-slate-100 flex items-center gap-2">
                  <Activity className="h-5 w-5 text-slate-400" />
                  Recent Runs
                </h2>
              </div>
              
              {runsLoading ? (
                <div className="h-64 flex items-center justify-center border border-slate-800 rounded-md bg-slate-900/50">
                  <div className="flex flex-col items-center gap-3 text-slate-400">
                    <Activity className="h-8 w-8 animate-pulse text-blue-500/50" />
                    <span>Loading runs...</span>
                  </div>
                </div>
              ) : (
                <RunsTable runs={runs} />
              )}
            </div>
          </div>

          {/* Right Column (40%) */}
          <div className="lg:col-span-5 space-y-6">
            <div className="sticky top-24">
              <h2 className="text-lg font-semibold text-slate-100 mb-4 px-1">Overview</h2>
              <StatsCards runs={runs} />
            </div>
          </div>

        </div>
      </main>
    </div>
  )
}
