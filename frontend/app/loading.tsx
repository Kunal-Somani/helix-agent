import { Activity } from "lucide-react";

export default function Loading() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-950 text-slate-50">
      <Activity className="h-10 w-10 text-blue-500 animate-spin" />
    </div>
  );
}
