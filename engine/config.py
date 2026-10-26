"""All weights and thresholds in one place (LLD §10.3–10.6).

`export()` is written into every offline snapshot so the browser router uses
exactly the same numbers as the server.
"""

from dataclasses import asdict, dataclass, field

# Zone and grid
CRS_UTM = "EPSG:32645"
CRS_WGS = "EPSG:4326"
CELL_M = 30

# Replay window: hour 0 = 2024-09-27 00:00 IST, last hour = 2024-10-07 23:00 IST
REPLAY_START = "2024-09-27T00:00:00+05:30"
REPLAY_HOURS = 11 * 24


@dataclass(frozen=True)
class RiskConfig:
    hand_scale_m: float = 10.0
    depr_scale_m: float = 1.5
    w_hand: float = 0.6
    w_depr: float = 0.4
    rain_24h_scale_mm: float = 200.0
    w1: float = 0.6  # terrain
    w2: float = 1.5  # rain/river amplification
    w3: float = 0.9  # observed water (video, breach)
    w4: float = 0.8  # reports
    text_only_factor: float = 0.5
    report_radius_m: float = 100.0
    report_half_life_h: float = 6.0
    level_weight: dict = field(
        default_factory=lambda: {"ankle": 0.4, "knee": 0.7, "waist": 0.9, "above": 1.0}
    )
    duplicate_radius_m: float = 50.0
    duplicate_window_min: float = 30.0


@dataclass(frozen=True)
class BreachConfig:
    head_loss_m_per_km: float = 0.3
    max_cells_per_hour: int = 4000
    flooded_risk: float = 0.9


@dataclass(frozen=True)
class RoutingConfig:
    alpha: float = 10.0
    edge_sample_m: float = 20.0
    block_walk: float = 0.7
    block_vehicle: float = 0.4
    block_offline: float = 0.5
    mobility_max_m: float = 1500.0
    fallback_high_ground_m: float = 1000.0
    top_k: int = 3
    walk_speed_mps: float = 1.0  # slow, wet-ground walking
    stale_snapshot_h: float = 2.0
    shelter_weights: dict = field(
        default_factory=lambda: {"safety": 0.4, "levels": 0.2, "type": 0.2, "official": 0.2}
    )
    rank_offset: float = 0.5


@dataclass(frozen=True)
class SitingConfig:
    demand_risk: float = 0.5
    demand_lookahead_h: int = 12
    cluster_m: float = 150.0
    candidate_max_risk: float = 0.3
    candidate_lookahead_h: int = 24
    candidate_min_levels: int = 2
    candidate_min_area_m2: float = 500.0
    default_k: int = 3
    default_max_walk_m: float = 2000.0


@dataclass(frozen=True)
class VisionConfig:
    max_side_px: int = 1024
    min_mask_conf: float = 0.5
    video_fps: float = 1.0
    video_max_frames: int = 60
    road_water_frac: float = 0.6
    road_consecutive_frames: int = 3
    edge_match_m: float = 30.0
    stranded_water_m: float = 3.0


@dataclass(frozen=True)
class AgentConfig:
    max_tool_calls: int = 4
    timeout_s: float = 15.0
    retries: int = 1
    max_sentences: int = 3
    emergency_numbers: tuple = ("112", "1070")  # 1070: state disaster helpline; verify for Bihar


RISK = RiskConfig()
BREACH = BreachConfig()
ROUTING = RoutingConfig()
SITING = SitingConfig()
VISION = VisionConfig()
AGENT = AgentConfig()


def export() -> dict:
    """Thresholds the browser router needs, embedded into each snapshot."""
    return {"routing": asdict(ROUTING), "risk_levels": RISK.level_weight}
