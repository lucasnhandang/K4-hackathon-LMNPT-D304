"""Enum nghiệp vụ."""

from enum import Enum


class Decision(str, Enum):
    TRA_LOI = "TRA_LOI"
    HOI_LAI = "HOI_LAI"
    CHUYEN_MOD = "CHUYEN_MOD"
