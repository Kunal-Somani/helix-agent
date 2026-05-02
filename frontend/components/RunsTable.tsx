"use client"
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  flexRender,
  createColumnHelper,
} from "@tanstack/react-table"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { StatusBadge } from "@/components/StatusBadge"
import { formatRelativeTime, calculateDuration, truncate } from "@/lib/utils"
import type { Run } from "@/lib/api"
import { Inbox, Eye } from "lucide-react"
import Link from "next/link"

const columnHelper = createColumnHelper<Run>()

const columns = [
  columnHelper.accessor("id", {
    header: "ID",
    cell: (info) => <span className="font-mono text-xs">{info.getValue().slice(0, 8)}...</span>,
  }),
  columnHelper.accessor("url", {
    header: "URL",
    cell: (info) => (
      <span title={info.getValue()} className="text-slate-300">
        {truncate(info.getValue(), 45)}
      </span>
    ),
  }),
  columnHelper.display({
    id: "status",
    header: "Status",
    cell: (info) => (
      <StatusBadge 
        status={info.row.original.status} 
        finalStatus={info.row.original.final_status} 
      />
    ),
  }),
  columnHelper.accessor("started_at", {
    header: "Started",
    cell: (info) => <span className="text-slate-400">{formatRelativeTime(info.getValue())}</span>,
  }),
  columnHelper.display({
    id: "duration",
    header: "Duration",
    cell: (info) => (
      <span className="text-slate-400 font-mono text-xs">
        {calculateDuration(info.row.original.started_at, info.row.original.completed_at)}
      </span>
    ),
  }),
  columnHelper.display({
    id: "actions",
    header: "Actions",
    cell: (info) => (
      <Link href={`/runs/${info.row.original.id}`}>
        <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-slate-400 hover:text-slate-100">
          <span className="sr-only">View</span>
          <Eye className="h-4 w-4" />
        </Button>
      </Link>
    ),
  }),
]

export function RunsTable({ runs }: { runs: Run[] }) {
  const table = useReactTable({
    data: runs,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: {
        pageSize: 10,
      },
    },
  })

  return (
    <div className="space-y-4">
      <div className="rounded-md border border-slate-800 bg-slate-900 overflow-hidden">
        <Table>
          <TableHeader className="bg-slate-950">
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id} className="border-slate-800 hover:bg-transparent">
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id} className="text-slate-400 font-medium">
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                  className="border-slate-800 hover:bg-slate-800/50 transition-colors"
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-32 text-center">
                  <div className="flex flex-col items-center justify-center text-slate-500 gap-2">
                    <Inbox className="h-8 w-8 mb-2 opacity-50" />
                    <span>No runs found. Submit a new one above.</span>
                  </div>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      
      {runs.length > 0 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-slate-500">
            Showing {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1} to{" "}
            {Math.min((table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize, runs.length)} of{" "}
            {runs.length} runs
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800 hover:text-slate-100"
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800 hover:text-slate-100"
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
