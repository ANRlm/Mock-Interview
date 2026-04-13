import { useEffect, useMemo, useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { getLLMProfiles, updateLLMRuntime } from '@/services/api'
import { useSettingsStore } from '@/stores/settingsStore'
import type { LLMProfilesResponse, LLMProfileName } from '@/types/api'

interface RuntimeState {
  loading: boolean
  saving: boolean
  error: string | null
  data: LLMProfilesResponse | null
}

export function LlmRuntimePanel() {
  const {
    llmProfile,
    llmModel,
    llmDisableThinking,
    llmRoutingStrategy,
    setLlmProfile,
    setLlmModel,
    setLlmDisableThinking,
    setLlmRoutingStrategy,
  } = useSettingsStore()
  const [state, setState] = useState<RuntimeState>({
    loading: true,
    saving: false,
    error: null,
    data: null,
  })

  useEffect(() => {
    let disposed = false

    async function fetchData() {
      try {
        setState((prev) => ({ ...prev, loading: true, error: null }))
        const data = await getLLMProfiles()
        if (disposed) return
        setState({ loading: false, saving: false, error: null, data })
        setLlmProfile(data.active_profile)
        setLlmModel(data.active_model ?? data.active_runtime.model)
        setLlmDisableThinking(data.active_runtime.disable_thinking)
        setLlmRoutingStrategy(data.routing_strategy)
      } catch (error) {
        if (disposed) return
        const message = error instanceof Error ? error.message : '读取 LLM 配置失败'
        setState({ loading: false, saving: false, error: message, data: null })
      }
    }

    fetchData()

    return () => {
      disposed = true
    }
  }, [setLlmDisableThinking, setLlmModel, setLlmProfile, setLlmRoutingStrategy])

  const profileMap = useMemo(() => {
    const map = new Map<LLMProfileName, { enabled: boolean; defaultModel: string; label: string }>()
    for (const item of state.data?.profiles ?? []) {
      map.set(item.name, {
        enabled: item.enabled,
        defaultModel: item.default_model,
        label: item.label,
      })
    }
    return map
  }, [state.data])

  const selectedProfile = profileMap.get(llmProfile)

  const applyConfig = async () => {
    setState((prev) => ({ ...prev, saving: true, error: null }))
    try {
      const updated = await updateLLMRuntime({
        profile: llmProfile,
        model: llmModel.trim() || null,
        disable_thinking: llmDisableThinking,
        routing_strategy: llmRoutingStrategy,
      })
      setState({ loading: false, saving: false, error: null, data: updated })
      setLlmProfile(updated.active_profile)
      setLlmModel(updated.active_model ?? updated.active_runtime.model)
      setLlmDisableThinking(updated.active_runtime.disable_thinking)
      setLlmRoutingStrategy(updated.routing_strategy)
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '更新 LLM 配置失败'
      setState((prev) => ({ ...prev, saving: false, error: message }))
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">LLM 运行配置</CardTitle>
        <CardDescription>支持本地/云端两档切换，可实时生效到后续轮次。</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {state.loading ? <p className="text-xs text-slate-400">正在读取配置...</p> : null}
        {state.error ? <p className="text-xs text-rose-300">{state.error}</p> : null}

        <div className="grid gap-2 md:grid-cols-2">
          {(['local', 'cloud'] as const).map((profile) => {
            const info = profileMap.get(profile)
            const enabled = info?.enabled ?? false
            const active = llmProfile === profile

            return (
              <button
                key={profile}
                type="button"
                disabled={!enabled || state.saving}
                className={`rounded-lg border px-3 py-2 text-left text-sm transition-colors ${
                  active ? 'border-blue-500 bg-blue-500/10' : 'border-slate-800 bg-slate-950/40 hover:border-slate-700'
                } ${!enabled ? 'cursor-not-allowed opacity-45' : ''}`}
                onClick={() => {
                  setLlmProfile(profile)
                  if (!llmModel.trim() && info?.defaultModel) {
                    setLlmModel(info.defaultModel)
                  }
                }}
              >
                <p className="font-medium text-slate-100">{info?.label ?? profile}</p>
                <p className="mt-1 text-xs text-slate-400">{enabled ? `默认模型: ${info?.defaultModel || '-'}` : '当前未启用'}</p>
              </button>
            )
          })}
        </div>

        <div className="space-y-2">
          <p className="text-xs text-slate-400">任务路由策略</p>
          <div className="grid gap-2 md:grid-cols-3">
            {(state.data?.routing_strategies ?? []).map((item) => (
              <button
                key={item.name}
                type="button"
                disabled={state.saving}
                onClick={() => setLlmRoutingStrategy(item.name)}
                className={`rounded-lg border px-3 py-2 text-left text-xs transition-colors ${
                  llmRoutingStrategy === item.name
                    ? 'border-cyan-400 bg-cyan-400/10'
                    : 'border-slate-800 bg-slate-950/40 hover:border-slate-700'
                }`}
              >
                <p className="font-medium text-slate-100">{item.label}</p>
                <p className="mt-1 text-slate-400">{item.description}</p>
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-xs text-slate-400">模型名称（可选覆盖）</p>
          <Input
            value={llmModel}
            onChange={(event) => setLlmModel(event.target.value)}
            placeholder={selectedProfile?.defaultModel ?? '例如: qwen3.5:2b'}
            disabled={state.saving}
          />
        </div>

        <label className="flex items-center gap-2 text-xs text-slate-300">
          <input
            type="checkbox"
            checked={llmDisableThinking}
            onChange={(event) => setLlmDisableThinking(event.target.checked)}
            disabled={state.saving}
          />
          关闭 thinking（推荐低延迟）
        </label>

        <div className="flex items-center gap-2">
          <Button type="button" size="sm" onClick={applyConfig} disabled={state.loading || state.saving || !selectedProfile?.enabled}>
            {state.saving ? '应用中...' : '应用配置'}
          </Button>
          {state.data?.active_runtime ? (
            <Badge variant="secondary">当前: {state.data.active_runtime.label} / {state.data.active_runtime.model}</Badge>
          ) : null}
        </div>

        {state.data?.task_routes ? (
          <div className="space-y-2 rounded-md border border-slate-800 bg-slate-950/50 p-3">
            <p className="text-xs uppercase tracking-widest text-slate-400">任务级路由预览</p>
            <div className="grid gap-2 text-xs text-slate-300">
              {Object.entries(state.data.task_routes).map(([task, route]) => (
                <p key={task}>
                  {task}: {route.profile} / {route.model || '-'} / thinking {route.disable_thinking ? 'off' : 'on'}
                </p>
              ))}
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
