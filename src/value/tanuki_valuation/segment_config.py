"""
TANUKI VALUATION - Segment Growth Configuration
セグメント別成長率設定

セグメント名は kpi_config.py の xbrl_members と一致させること。
実績データは annual_{year}.json の segments フィールドから自動取得。
ここでは「ウェイト」「設定成長率」「成長オプション」のみを定義する。

v7.4 更新:
  - セグメント名を XBRL Instance Document の実態に合わせて統一
  - kpi_fetcher.py が annual_{year}.json の segments と突合してkpi_dataを生成
"""

from typing import Dict, Any, Optional, List


SEGMENT_OVERRIDES: Dict[str, Dict[str, Any]] = {

    # ── NVIDIA ──
    "NVDA": {
        "enabled": True,
        "fiscal_year": "FY2026",
        "segments": {
            "Compute and Networking": {
                "weight": 0.90,
                "growth": 0.35,
                "note": "Data Center GPU/Networking for AI training & inference."
            },
            "Graphics": {
                "weight": 0.10,
                "growth": 0.10,
                "note": "GeForce GPU for PC gaming and professional visualization."
            },
        }
    },

    # ── Tesla ──
    "TSLA": {
        "enabled": True,
        "fiscal_year": "FY2025",
        "segments": {
            "Automotive": {
                "weight": 0.87,
                "growth": 0.10,
                "note": "Vehicle sales & leasing. FSD revenue included."
            },
            "Energy Generation and Storage": {
                "weight": 0.13,
                "growth": 0.30,
                "note": "Powerwall, Megapack, Solar. High-growth segment."
            },
        }
    },

    # ── Palantir ──
    "PLTR": {
        "enabled": True,
        "fiscal_year": "FY2025",
        "segments": {
            "Government": {
                "weight": 0.54,
                "growth": 0.20,
                "note": "US Gov + Allies defense/intel contracts."
            },
            "Commercial": {
                "weight": 0.46,
                "growth": 0.50,
                "note": "US Enterprise AIP platform."
            },
        }
    },

    # ── Microsoft ──
    "MSFT": {
        "enabled": True,
        "fiscal_year": "FY2025",
        "segments": {
            "Intelligent Cloud": {
                "weight": 0.38,
                "growth": 0.22,
                "note": "Azure, Server products. AI workload acceleration."
            },
            "Productivity and Business Processes": {
                "weight": 0.43,
                "growth": 0.12,
                "note": "Office 365, LinkedIn, Dynamics. Copilot upsell."
            },
            "More Personal Computing": {
                "weight": 0.19,
                "growth": 0.05,
                "note": "Windows, Xbox, Surface, Search. Mature segment."
            },
        }
    },

    # ── Amazon ──
    "AMZN": {
        "enabled": True,
        "fiscal_year": "FY2025",
        "segments": {
            "North America": {
                "weight": 0.60,
                "growth": 0.10,
                "note": "1P + 3P e-commerce, advertising, Prime."
            },
            "International": {
                "weight": 0.22,
                "growth": 0.09,
                "note": "Non-US e-commerce. Profitability improving."
            },
            "AWS": {
                "weight": 0.18,
                "growth": 0.22,
                "note": "Cloud infrastructure. Highest margin segment."
            },
        }
    },

    # ── AMD ──
    "AMD": {
        "enabled": True,
        "fiscal_year": "FY2025",
        "segments": {
            "Data Center": {
                "weight": 0.62,
                "growth": 0.35,
                "note": "EPYC CPUs + Instinct MI300X GPUs."
            },
            "Client": {
                "weight": 0.00,
                "growth": 0.08,
                "note": "Ryzen CPUs. FY2025はClient and Gamingに統合のためweight=0。"
            },
            "Gaming": {
                "weight": 0.00,
                "growth": -0.10,
                "note": "Console APUs. FY2025はClient and Gamingに統合のためweight=0。"
            },
            "Embedded": {
                "weight": 0.10,
                "growth": 0.15,
                "note": "Xilinx FPGAs. Recovery from inventory digestion."
            },
            "Client and Gaming": {
                "weight": 0.28,
                "growth": 0.05,
                "note": "FY2025 XBRL統合形式。Client(20%+8.0%)+Gaming(8%-10.0%)の合算。",
            },
            "All Other": {
                "weight": 0.00,
                "growth": 0.00,
                "note": "その他・調整項目。",
            },
        }
    },

    # ── SoFi Technologies ──
    "SOFI": {
        "enabled": True,
        "fiscal_year": "FY2025",
        "segments": {
            "Lending": {
                "weight": 0.49,
                "growth": 0.10,
                "note": "Student, personal, home loans."
            },
            "Technology Platform": {
                "weight": 0.12,
                "growth": 0.15,
                "note": "Galileo B2B fintech infrastructure."
            },
            "Financial Services": {
                "weight": 0.39,
                "growth": 0.40,
                "note": "SoFi Money, Invest, Credit Card."
            },
        }
    },

    # ── Rocket Lab ──
    "RKLB": {
        "enabled": True,
        "fiscal_year": "FY2025",
        "segments": {
            "Launch Services": {
                "weight": 0.33,
                "growth": 0.25,
                "note": "Electron launches + Neutron development."
            },
            "Space Systems": {
                "weight": 0.67,
                "growth": 0.35,
                "note": "Spacecraft components, satellites, solar panels."
            },
        }
    },

    # ── AppLovin ──
    "APP": {
        "enabled": True,
        "fiscal_year": "FY2025",
        "segments": {
            "Software Platform": {
                "weight": 0.75,
                "growth": 0.45,
                "note": "AppDiscovery, MAX, AXON 2.0."
            },
            "Apps": {
                "weight": 0.25,
                "growth": 0.02,
                "note": "1P mobile games portfolio."
            },
        }
    },

    # ── Celsius Holdings ──
    "CELH": {
        "enabled": True,
        "fiscal_year": "FY2025",
        "segments": {
            "North America": {
                "weight": 0.92,
                "growth": 0.15,
                "note": "US/Canada retail & e-commerce."
            },
            "International": {
                "weight": 0.08,
                "growth": 0.40,
                "note": "Europe, Asia expansion."
            },
        }
    },

    # ── SoundHound AI ──
    "SOUN": {
        "enabled": True,
        "fiscal_year": "FY2025",
        "segments": {
            "Voice AI": {
                "weight": 1.00,
                "growth": 0.40,
                "note": "Automotive + restaurant + IoT voice AI."
            },
        }
    },

    # ── Ondas Holdings ──
    "ONDS": {
        "enabled": True,
        "fiscal_year": "FY2025",
        "segments": {
            "Total": {
                "weight": 1.00,
                "growth": 0.30,
                "note": "Drone + railroad automation."
            },
        }
    },
}


GROWTH_OPTIONS: Dict[str, List[Dict[str, Any]]] = {

    "NVDA": [
        {
            "name": "Sovereign AI",
            "tam": 80_000_000_000,
            "penetration": 0.15,
            "fcf_margin": 0.20,
            "probability": 0.70,
            "delay_years": 3,
            "discount_rate": 0.15,
            "note": "各国政府のAIインフラ整備需要。CUDAエコシステムの競争優位。",
        },
        {
            "name": "Robotics / Isaac",
            "tam": 200_000_000_000,
            "penetration": 0.05,
            "fcf_margin": 0.20,
            "probability": 0.40,
            "delay_years": 5,
            "discount_rate": 0.15,
            "note": "Isaacプラットフォームによるロボティクス向けGPU需要。",
        },
        {
            "name": "NIM / Inference SaaS",
            "tam": 50_000_000_000,
            "penetration": 0.10,
            "fcf_margin": 0.25,
            "probability": 0.50,
            "delay_years": 4,
            "discount_rate": 0.15,
            "note": "NIMによる推論SaaS転換。AWSのようなソフトウェア収益構造の実現。",
        },
    ],

    "TSLA": [
        {
            "name": "Robotaxi / FSD Network",
            "tam": 300_000_000_000,
            "penetration": 0.05,
            "fcf_margin": 0.25,
            "probability": 0.30,
            "delay_years": 5,
            "discount_rate": 0.15,
            "note": "FSD完全自律後の配車ネットワーク収益。",
        },
        {
            "name": "Optimus Robot",
            "tam": 150_000_000_000,
            "penetration": 0.05,
            "fcf_margin": 0.15,
            "probability": 0.25,
            "delay_years": 6,
            "discount_rate": 0.15,
            "note": "汎用ヒューマノイドロボット。量産コスト確立が前提。",
        },
    ],

    "PLTR": [
        {
            "name": "AI Platform (AIP) Global",
            "tam": 100_000_000_000,
            "penetration": 0.08,
            "fcf_margin": 0.30,
            "probability": 0.60,
            "delay_years": 3,
            "discount_rate": 0.15,
            "note": "AIPの国際展開。",
        },
        {
            "name": "Defense AI / NATO",
            "tam": 50_000_000_000,
            "penetration": 0.12,
            "fcf_margin": 0.25,
            "probability": 0.55,
            "delay_years": 4,
            "discount_rate": 0.15,
            "note": "地政学的緊張によるNATO加盟国への拡大。",
        },
    ],

    "MSFT": [
        {
            "name": "Copilot Enterprise",
            "tam": 80_000_000_000,
            "penetration": 0.20,
            "fcf_margin": 0.35,
            "probability": 0.70,
            "delay_years": 3,
            "discount_rate": 0.15,
            "note": "M365 Copilotの企業向け拡大。",
        },
    ],

    "AMZN": [
        {
            "name": "Alexa+ / AI Assistant",
            "tam": 60_000_000_000,
            "penetration": 0.15,
            "fcf_margin": 0.20,
            "probability": 0.50,
            "delay_years": 4,
            "discount_rate": 0.15,
            "note": "Alexa+の有料転換と企業向け展開。",
        },
    ],

    "AMD": [
        {
            "name": "AI PC / Client AI",
            "tam": 40_000_000_000,
            "penetration": 0.20,
            "fcf_margin": 0.15,
            "probability": 0.55,
            "delay_years": 3,
            "discount_rate": 0.15,
            "note": "NPU搭載RyzenによるAI PC市場の取り込み。",
        },
    ],

    "APP": [
        {
            "name": "E-commerce Ad Network",
            "tam": 50_000_000_000,
            "penetration": 0.08,
            "fcf_margin": 0.30,
            "probability": 0.45,
            "delay_years": 3,
            "discount_rate": 0.15,
            "note": "モバイル広告からEC広告への拡張。",
        },
    ],
}


def get_segment_growth(ticker: str) -> Optional[Dict[str, Any]]:
    config = SEGMENT_OVERRIDES.get(ticker)
    if not config or not config.get("enabled", False):
        return None
    segments = config.get("segments", {})
    if not segments:
        return None
    weighted_growth = sum(
        seg.get("weight", 0) * seg.get("growth", 0)
        for seg in segments.values()
    )
    total_weight = sum(seg.get("weight", 0) for seg in segments.values())
    if not (0.95 <= total_weight <= 1.05):
        print(f"[WARN] {ticker} segment weights sum to {total_weight:.2f}, expected ~1.0")
    return {
        "enabled": True,
        "weighted_growth": weighted_growth,
        "fiscal_year": config.get("fiscal_year"),
        "segments": segments,
        "source": "segment_config"
    }


def get_growth_options(ticker: str) -> List[Dict[str, Any]]:
    options = GROWTH_OPTIONS.get(ticker, [])
    if not options:
        return []
    enriched = []
    for opt in options:
        expected_fcf = opt["tam"] * opt["penetration"] * opt["fcf_margin"] * opt["probability"]
        pv = expected_fcf / (1 + opt["discount_rate"]) ** opt["delay_years"]
        enriched.append({**opt, "expected_fcf": expected_fcf, "pv": pv})
    return enriched


def calculate_growth_option_total_pv(ticker: str) -> Dict[str, Any]:
    options = get_growth_options(ticker)
    total_pv = sum(opt["pv"] for opt in options)
    return {"total_pv": total_pv, "options": options, "count": len(options)}


def calculate_scenario_growth(ticker: str, scenario: str = "base") -> Dict[str, Any]:
    segment_data = get_segment_growth(ticker)
    if not segment_data:
        return {"rate": None, "scenario": scenario, "source": "not_configured"}
    base_rate = segment_data["weighted_growth"]
    adjustments = {"bull": 1.2, "base": 1.0, "bear": 0.7}
    adjusted_rate = max(0.0, min(0.50, base_rate * adjustments.get(scenario, 1.0)))
    return {
        "rate": adjusted_rate,
        "base_rate": base_rate,
        "scenario": scenario,
        "adjustment": adjustments.get(scenario, 1.0),
        "source": "segment_config"
    }


if __name__ == "__main__":
    print("=== Segment Growth ===")
    for ticker in ["NVDA", "TSLA", "PLTR", "MSFT", "AMZN", "AMD", "SOFI", "RKLB", "APP", "CELH", "SOUN", "ONDS"]:
        result = get_segment_growth(ticker)
        if result:
            print(f"{ticker}: {result['weighted_growth']:.1%}  ({result['fiscal_year']})")
        else:
            print(f"{ticker}: not configured")
