"use client"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Loader2, Plus } from "lucide-react"
import { useQueryClient, useMutation } from "@tanstack/react-query"
import { submitRun } from "@/lib/api"
import { toast } from "sonner"

const schema = z.object({
  url: z.string().url("Must be a valid URL"),
  apiKey: z.string().min(1, "API key is required"),
})

type FormData = z.infer<typeof schema>

export function SubmitForm() {
  const queryClient = useQueryClient()
  
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const mutation = useMutation({
    mutationFn: ({ url, apiKey }: FormData) => submitRun(url, apiKey),
    onSuccess: (data) => {
      toast.success(`Run started successfully (ID: ${data.run_id.slice(0, 8)})`)
      queryClient.invalidateQueries({ queryKey: ["runs"] })
      reset()
    },
    onError: (error) => {
      let msg = "An unexpected error occurred"
      if (error instanceof Error) {
        msg = error.message
      }
      toast.error(`Submission failed: ${msg}`)
    },
  })

  const onSubmit = (data: FormData) => {
    mutation.mutate(data)
  }

  return (
    <Card className="bg-slate-900 border-slate-800 shadow-xl">
      <CardHeader className="pb-4">
        <CardTitle className="text-xl font-semibold text-slate-100 flex items-center gap-2">
          <Plus className="h-5 w-5 text-blue-500" />
          New Run
        </CardTitle>
        <CardDescription className="text-slate-400">
          Submit a new URL to the autonomous agent.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="url" className="text-slate-300">Target URL</Label>
            <Input
              id="url"
              placeholder="https://example.com/quiz"
              className="bg-slate-950 border-slate-800 text-slate-100 focus-visible:ring-blue-500"
              {...register("url")}
            />
            {errors.url && <p className="text-sm text-red-400">{errors.url.message}</p>}
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="apiKey" className="text-slate-300">API Key</Label>
            <Input
              id="apiKey"
              type="password"
              placeholder="sk-..."
              className="bg-slate-950 border-slate-800 text-slate-100 focus-visible:ring-blue-500"
              {...register("apiKey")}
            />
            {errors.apiKey && <p className="text-sm text-red-400">{errors.apiKey.message}</p>}
          </div>

          <Button 
            type="submit" 
            className="w-full bg-blue-600 hover:bg-blue-700 text-white transition-colors"
            disabled={mutation.isPending}
          >
            {mutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Initializing...
              </>
            ) : (
              "Start Run"
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
