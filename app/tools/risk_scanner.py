from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RiskScanResult:
    flags: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    @property
    def has_high_risk(self) -> bool:
        return any(
            flag.startswith("high:") or flag.startswith("critical:")
            for flag in self.flags
        )


class RiskScanner:
    RULES = {
        "pii_phone": (["手机号", "手机号码", "身份证", "验证码"], "high:pii"),
        "credential_request": (
            ["提供密码", "发送验证码", "告诉我验证码"],
            "critical:credential",
        ),
        "unauthorized_commitment": (
            ["保证退款", "立即到账", "百分百解决", "一定赔偿"],
            "high:unauthorized_commitment",
        ),
        "prompt_injection": (
            ["忽略之前的指令", "ignore previous", "system prompt", "泄露提示词"],
            "critical:prompt_injection",
        ),
        "abuse": (["辱骂", "投诉媒体", "曝光"], "medium:complaint_escalation"),
    }

    def scan(self, text: str) -> RiskScanResult:
        normalized = text.lower()
        result = RiskScanResult()
        for rule_name, (keywords, flag) in self.RULES.items():
            for keyword in keywords:
                if keyword.lower() in normalized:
                    result.flags.append(flag)
                    result.reasons.append(f"{rule_name}:{keyword}")
                    break
        result.flags = sorted(set(result.flags))
        return result
