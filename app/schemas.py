"""Validated API and agent contracts."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TechnicalResult(BaseModel):
    score: float = Field(ge=0, le=10)
    bias: Literal["bullish", "neutral", "bearish"]
    confidence: float = Field(ge=0, le=1)
    signals: list[str] = []
    risks: list[str] = []
    summary: str = ""
    indicators: dict[str, float | None] = {}


class SentimentResult(BaseModel):
    sentiment: Literal["positive", "neutral", "negative"]
    score: float = Field(ge=0, le=10)
    confidence: float = Field(ge=0, le=1)
    important_events: list[str] = []
    summary: str = ""
    risks: list[str] = []


class RiskResult(BaseModel):
    risk_score: float = Field(ge=0, le=10)
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "EXTREME"]
    risks: list[str] = []
    suggested_stop_distance_percent: float = Field(ge=0)


class DebateResult(BaseModel):
    score: float = Field(ge=0, le=10)
    confidence: float = Field(ge=0, le=1)
    arguments: list[str] = []
    invalidations: list[str] = []


class DecisionResult(BaseModel):
    symbol: str
    recommendation: str
    score: float = Field(ge=0, le=10)
    confidence: float = Field(ge=0, le=1)
    entry_min: float
    entry_max: float
    stop_loss: float
    target_1: float
    target_2: float
    risk_reward_ratio: float
    reasoning: list[str]
    risks: list[str]
    bull_case: str = ""
    bear_case: str = ""


class BacktestRequest(BaseModel):
    symbol: str
    period: str = "5y"
    rsi_below: float = 35
    require_ema_trend: bool = True
    min_volume_ratio: float = 1.0
    require_macd_cross: bool = False
