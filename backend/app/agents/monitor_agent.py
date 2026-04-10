from __future__ import annotations


class MonitorAgent:
    def summarize_behavior(self, behavior_detail: dict) -> str:
        sample_count = int(behavior_detail.get("sample_count", 0))
        if sample_count == 0:
            return "未采集到有效行为数据，建议在安静、光线稳定环境下重新练习。"
        return "候选人整体状态稳定，建议继续提升眼神交流与头部姿态一致性。"
