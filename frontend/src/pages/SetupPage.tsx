import { SetupWizard } from '@/components/setup/SetupWizard'

export function SetupPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-slate-100">面试准备</h1>
      <p className="text-sm text-slate-400">按步骤配置职位方向与细分角色，完成后进入面试主界面。</p>
      <SetupWizard />
    </div>
  )
}
