"""
TANUKI VALUATION - Config Migration Script
既存の segment_config.py / maturity_config.py の設定値を
JSON形式に書き出す（一度だけ実行）

使用方法:
    cd On-a-journey-git
    python migrate_config_to_json.py

出力先: config/ ディレクトリ（リポジトリルート直下）
"""

import json
import os
from datetime import datetime

# ── 出力先 ──
REPO_ROOT  = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(REPO_ROOT, "config")
os.makedirs(CONFIG_DIR, exist_ok=True)

TODAY = datetime.now().strftime("%Y-%m-%d")


def write_json(filename: str, data: dict) -> None:
    path = os.path.join(CONFIG_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ {path}")


# ============================================================
# 1. segment_config.json
# ============================================================
segment_config = {
    "_meta": {
        "description": "セグメント別成長率・ウェイト設定",
        "encoding": "UTF-8",
        "updated_at": TODAY,
        "schema_version": "1.0"
    },
    "_schema": {
        "enabled":       "true=有効 / false=無効（FCF CAGRにフォールバック）",
        "fiscal_year":   "設定対象の会計年度ラベル（表示用）",
        "segments":      "セグメント名: {weight: ウェイト合計1.0, growth: 成長率, note: メモ}",
        "weight_rule":   "全セグメントのweight合計が0.95〜1.05の範囲に収まること",
        "growth_null":   "growth=nullの場合はFCF CAGRにフォールバック"
    },
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
            }
        }
    },
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
            }
        }
    },
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
            }
        }
    },
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
            }
        }
    },
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
            }
        }
    },
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
                "note": "FY2025 XBRL統合形式。Client(20%+8.0%)+Gaming(8%-10.0%)の合算。"
            },
            "All Other": {
                "weight": 0.00,
                "growth": 0.00,
                "note": "その他・調整項目。"
            }
        }
    },
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
            }
        }
    },
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
            }
        }
    },
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
            }
        }
    },
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
            }
        }
    },
    "SOUN": {
        "enabled": True,
        "fiscal_year": "FY2025",
        "segments": {
            "Voice AI": {
                "weight": 1.00,
                "growth": 0.40,
                "note": "Automotive + restaurant + IoT voice AI."
            }
        }
    },
    "ONDS": {
        "enabled": True,
        "fiscal_year": "FY2025",
        "segments": {
            "Total": {
                "weight": 1.00,
                "growth": 0.30,
                "note": "Drone + railroad automation."
            }
        }
    }
}

# ============================================================
# 2. growth_options_config.json
# ============================================================
growth_options_config = {
    "_meta": {
        "description": "成長オプション（仮説セグメント）設定",
        "encoding": "UTF-8",
        "updated_at": TODAY,
        "schema_version": "1.0"
    },
    "_schema": {
        "options":       "成長オプションのリスト",
        "name":          "オプション名（表示用）",
        "tam":           "Total Addressable Market（円/ドル）",
        "penetration":   "市場侵入率（0.0〜1.0）",
        "fcf_margin":    "FCFマージン（0.0〜1.0）",
        "probability":   "実現確率（0.0〜1.0）",
        "delay_years":   "収益化までの年数",
        "discount_rate": "割引率（0.0〜1.0）",
        "note":          "メモ・根拠",
        "formula":       "PV = TAM × penetration × fcf_margin × probability / (1+discount_rate)^delay_years"
    },
    "NVDA": {
        "options": [
            {
                "name": "Sovereign AI",
                "tam": 80000000000,
                "penetration": 0.15,
                "fcf_margin": 0.20,
                "probability": 0.70,
                "delay_years": 3,
                "discount_rate": 0.15,
                "note": "各国政府のAIインフラ整備需要。CUDAエコシステムの競争優位。"
            },
            {
                "name": "Robotics / Isaac",
                "tam": 200000000000,
                "penetration": 0.05,
                "fcf_margin": 0.20,
                "probability": 0.40,
                "delay_years": 5,
                "discount_rate": 0.15,
                "note": "Isaacプラットフォームによるロボティクス向けGPU需要。"
            },
            {
                "name": "NIM / Inference SaaS",
                "tam": 50000000000,
                "penetration": 0.10,
                "fcf_margin": 0.25,
                "probability": 0.50,
                "delay_years": 4,
                "discount_rate": 0.15,
                "note": "NIMによる推論SaaS転換。AWSのようなソフトウェア収益構造の実現。"
            }
        ]
    },
    "TSLA": {
        "options": [
            {
                "name": "Robotaxi / FSD Network",
                "tam": 300000000000,
                "penetration": 0.05,
                "fcf_margin": 0.25,
                "probability": 0.30,
                "delay_years": 5,
                "discount_rate": 0.15,
                "note": "FSD完全自律後の配車ネットワーク収益。"
            },
            {
                "name": "Optimus Robot",
                "tam": 150000000000,
                "penetration": 0.05,
                "fcf_margin": 0.15,
                "probability": 0.25,
                "delay_years": 6,
                "discount_rate": 0.15,
                "note": "汎用ヒューマノイドロボット。量産コスト確立が前提。"
            }
        ]
    },
    "PLTR": {
        "options": [
            {
                "name": "AI Platform (AIP) Global",
                "tam": 100000000000,
                "penetration": 0.08,
                "fcf_margin": 0.30,
                "probability": 0.60,
                "delay_years": 3,
                "discount_rate": 0.15,
                "note": "AIPの国際展開。"
            },
            {
                "name": "Defense AI / NATO",
                "tam": 50000000000,
                "penetration": 0.12,
                "fcf_margin": 0.25,
                "probability": 0.55,
                "delay_years": 4,
                "discount_rate": 0.15,
                "note": "地政学的緊張によるNATO加盟国への拡大。"
            }
        ]
    },
    "MSFT": {
        "options": [
            {
                "name": "Copilot Enterprise",
                "tam": 80000000000,
                "penetration": 0.20,
                "fcf_margin": 0.35,
                "probability": 0.35,
                "delay_years": 3,
                "discount_rate": 0.15,
                "note": "M365 Copilotの企業向け拡大。"
            }
        ]
    },
    "AMZN": {
        "options": [
            {
                "name": "Alexa+ / AI Assistant",
                "tam": 60000000000,
                "penetration": 0.15,
                "fcf_margin": 0.20,
                "probability": 0.50,
                "delay_years": 4,
                "discount_rate": 0.15,
                "note": "Alexa+の有料転換と企業向け展開。"
            }
        ]
    },
    "AMD": {
        "options": [
            {
                "name": "AI PC / Client AI",
                "tam": 40000000000,
                "penetration": 0.20,
                "fcf_margin": 0.15,
                "probability": 0.55,
                "delay_years": 3,
                "discount_rate": 0.15,
                "note": "NPU搭載RyzenによるAI PC市場の取り込み。"
            }
        ]
    },
    "APP": {
        "options": [
            {
                "name": "E-commerce Ad Network",
                "tam": 50000000000,
                "penetration": 0.08,
                "fcf_margin": 0.30,
                "probability": 0.45,
                "delay_years": 3,
                "discount_rate": 0.15,
                "note": "モバイル広告からEC広告への拡張。"
            }
        ]
    }
}

# ============================================================
# 3. maturity_config.json
# ============================================================
maturity_config = {
    "_meta": {
        "description": "DCF成熟プロファイル設定（two_stage / three_stage）",
        "encoding": "UTF-8",
        "updated_at": TODAY,
        "schema_version": "1.0"
    },
    "_schema": {
        "type":           "two_stage（2段階）| three_stage（3段階）",
        "phase1.years":   "高成長期の年数",
        "phase1.growth":  "高成長期の成長率。null = segment_configの加重平均成長率を流用",
        "phase2.years":   "移行期の年数（three_stageのみ有効）",
        "phase2.growth":  "移行期の成長率（three_stageのみ有効）",
        "terminal_growth":"永続成長率（通常0.03）",
        "_default":       "銘柄未設定時のフォールバック（two_stage）"
    },
    "_default": {
        "type": "two_stage",
        "terminal_growth": 0.03
    },
    "NVDA": {
        "type": "three_stage",
        "phase1": {"years": 5, "growth": None},
        "phase2": {"years": 5, "growth": 0.15},
        "terminal_growth": 0.03
    },
    "TSLA": {
        "type": "three_stage",
        "phase1": {"years": 4, "growth": None},
        "phase2": {"years": 4, "growth": 0.08},
        "terminal_growth": 0.03
    },
    "PLTR": {
        "type": "three_stage",
        "phase1": {"years": 5, "growth": None},
        "phase2": {"years": 5, "growth": 0.15},
        "terminal_growth": 0.03
    },
    "MSFT": {
        "type": "three_stage",
        "phase1": {"years": 5, "growth": None},
        "phase2": {"years": 5, "growth": 0.08},
        "terminal_growth": 0.03
    },
    "AMZN": {
        "type": "three_stage",
        "phase1": {"years": 5, "growth": None},
        "phase2": {"years": 5, "growth": 0.10},
        "terminal_growth": 0.03
    },
    "AMD": {
        "type": "three_stage",
        "phase1": {"years": 4, "growth": None},
        "phase2": {"years": 4, "growth": 0.10},
        "terminal_growth": 0.03
    },
    "APP": {
        "type": "three_stage",
        "phase1": {"years": 4, "growth": None},
        "phase2": {"years": 4, "growth": 0.12},
        "terminal_growth": 0.03
    },
    "CELH": {
        "type": "three_stage",
        "phase1": {"years": 3, "growth": None},
        "phase2": {"years": 5, "growth": 0.10},
        "terminal_growth": 0.03
    }
}

# ============================================================
# 書き出し実行
# ============================================================
print("=== TANUKI VALUATION Config Migration ===\n")
print(f"出力先: {CONFIG_DIR}\n")

write_json("segment_config.json",      segment_config)
write_json("growth_options_config.json", growth_options_config)
write_json("maturity_config.json",     maturity_config)

# バリデーション
print("\n=== バリデーション ===")
for ticker, data in segment_config.items():
    if ticker.startswith("_"): continue
    total_w = sum(s["weight"] for s in data["segments"].values())
    status = "✅" if 0.95 <= total_w <= 1.05 else "❌ ウェイト合計が1.0から外れています"
    print(f"  segment {ticker}: ウェイト合計={total_w:.2f} {status}")

print("\n完了。次のステップ: Python側の移行（segment_config.py / maturity_config.py）")
