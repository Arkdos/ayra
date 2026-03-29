import os
import json
import re
import datetime
import math
import requests
import base64
from typing import List, Dict, Any, Optional, Union
from pydantic import validate_call, Field, ValidationError

# --- 1. SPECIALIZED GEAR CLASSES ---

class FinanceGears:
    """Specialized financial calculation tools."""
    
    @staticmethod
    def get_manifest() -> List[Dict[str, Any]]:
        return [
            {
                "name": "mortgage_calculator",
                "intent": "Calculate monthly mortgage payments.",
                "parameters": {
                    "principal": {"type": "number", "description": "The total loan amount (must be > 0)."},
                    "annual_rate": {"type": "number", "description": "Annual interest rate percentage (e.g., 5.5)."},
                    "years": {"type": "integer", "description": "Loan term in years (must be 1-50)."}
                },
                "sample_output": "For a $300,000 loan at 5% for 30 years, the monthly payment is $1,610.46."
            },
            {
                "name": "compound_interest",
                "intent": "Calculate investment growth with flexible compounding and contribution periods.",
                "parameters": {
                    "principal": {"type": "number", "description": "Initial investment amount."},
                    "rate": {"type": "number", "description": "Interest rate percentage (e.g., 7.0 for 7%)."},
                    "rate_type": {"type": "string", "description": "Frequency of rate provided: 'monthly', 'quarterly', 'semi-annual', 'annual'."},
                    "time_years": {"type": "number", "description": "Number of years for investment."},
                    "compounding_frequency": {"type": "string", "description": "Compounding period: 'monthly', 'quarterly', 'semi-annual', 'annual'."}
                },
                "sample_output": "An initial $1,000 at 7% annual rate compounded monthly for 10 years results in $2,009.66."
            }
        ]

    @staticmethod
    @validate_call
    def mortgage_calculator(
        principal: float = Field(..., gt=0),
        annual_rate: float = Field(..., ge=0, le=100),
        years: int = Field(..., gt=0, le=50)
    ) -> str:
        r = (annual_rate / 100) / 12
        n = years * 12
        try:
            payment = (principal / n) if r == 0 else (principal * r * (1 + r)**n) / ((1 + r)**n - 1)
            return f"For a principal of ${principal:,.2f} at {annual_rate}% over {years} years, the monthly payment is ${payment:,.2f}."
        except:
            return "Error calculating mortgage. Check inputs."

    @staticmethod
    @validate_call
    def compound_interest(
        principal: float = Field(..., gt=0),
        rate: float = Field(..., ge=0),
        rate_type: str = Field(..., pattern="^(monthly|quarterly|semi-annual|annual)$"),
        time_years: float = Field(..., gt=0),
        compounding_frequency: str = Field(..., pattern="^(monthly|quarterly|semi-annual|annual)$")
    ) -> str:
        """
        Advanced compound interest calculator that handles cross-frequency rate adjustments.
        Formula: A = P(1 + r/n)^(nt)
        """
        # Map frequencies to periods per year
        freq_map = {'monthly': 12, 'quarterly': 4, 'semi-annual': 2, 'annual': 1}
        
        # 1. Normalize Rate to ANNUAL (Effective Annual Rate logic if simple, but here we assume simple periodic multiplication)
        # If user gives monthly 1%, annual is 12%.
        annual_nominal_rate = (rate / 100) * freq_map[rate_type]
        
        # 2. Get Compounding periods (n)
        n = freq_map[compounding_frequency]
        
        # 3. Calculate periodic rate (r/n)
        periodic_rate = annual_nominal_rate / n
        
        # 4. Final Calculation
        total_periods = n * time_years
        final_amount = principal * (1 + periodic_rate)**total_periods
        
        return (f"An initial investment of ${principal:,.2f} with a {rate}% {rate_type} growth rate "
                f"compounded {compounding_frequency} for {time_years} years results in a total value of ${final_amount:,.2f}.")


class WebGears:
    """Tools for real-time web interaction."""

    @staticmethod
    def get_manifest() -> List[Dict[str, Any]]:
        return [
            {
                "name": "get_weather",
                "intent": "Get current weather for a city.",
                "parameters": {"city": {"type": "string", "description": "City name."}},
                "sample_output": "The current weather in London is 15°C and Clear."
            }
        ]

    @staticmethod
    @validate_call
    def get_weather(city: str = Field(..., min_length=1)) -> str:
        try:
            res = requests.get(f"https://wttr.in/{city}?format=3", timeout=5)
            return f"The current weather in {city.title()} is {res.text.strip()}." if res.status_code == 200 else "Weather unavailable."
        except:
            return "Connection error while fetching weather."


class TextGears:
    """Tools for text manipulation and analysis."""

    @staticmethod
    def get_manifest() -> List[Dict[str, Any]]:
        return [
            {
                "name": "extract_keywords",
                "intent": "Find recurring words in a text.",
                "parameters": {"text": {"type": "string", "description": "Text to analyze."}},
                "sample_output": "I identified the following keywords: AI, Logic, Data."
            }
        ]

    @staticmethod
    @validate_call
    def extract_keywords(text: str = Field(..., min_length=10)) -> str:
        words = re.findall(r'\w{5,}', text.lower())
        found = list(set([w for w in words if words.count(w) > 1]))[:10]
        return f"I identified {len(found)} keywords: {', '.join([w.capitalize() for w in found])}." if found else "No keywords found."

class UtilityGears:
    """General utility tools including unit conversion."""

    @staticmethod
    def get_manifest() -> List[Dict[str, Any]]:
        return [
            {
                "name": "convert_units",
                "intent": "Convert numerical values between different units (length, weight, temperature, volume).",
                "parameters": {
                    "value": {"type": "number", "description": "The quantity to convert."},
                    "category": {"type": "string", "description": "Category: 'length', 'weight', 'temp', 'volume'."},
                    "from_unit": {"type": "string", "description": "Source unit (e.g., 'km', 'kg', 'c', 'liters')."},
                    "to_unit": {"type": "string", "description": "Target unit (e.g., 'mi', 'lb', 'f', 'gallons')."}
                },
                "sample_output": "The conversion of 100 kilometers to miles is 62.14."
            }
        ]

    @staticmethod
    @validate_call
    def convert_units(
        value: float = Field(...),
        category: str = Field(..., pattern="^(length|weight|temp|volume)$"),
        from_unit: str = Field(...),
        to_unit: str = Field(...)
    ) -> str:
        """Universal unit converter for common measurements."""
        f, t = from_unit.lower(), to_unit.lower()
        
        if category == 'temp':
            if f == 'c' and t == 'f': res = (value * 9/5) + 32
            elif f == 'f' and t == 'c': res = (value - 32) * 5/9
            elif f == 'c' and t == 'k': res = value + 273.15
            elif f == 'k' and t == 'c': res = value - 273.15
            else: return f"Temperature conversion from {f} to {t} not supported."
            return f"{value}°{f.upper()} is {round(res, 2)}°{t.upper()}."

        units = {
            'length': {'m': 1, 'km': 1000, 'cm': 0.01, 'mm': 0.001, 'mi': 1609.34, 'ft': 0.3048, 'in': 0.0254, 'yd': 0.9144},
            'weight': {'kg': 1, 'g': 0.001, 'mg': 0.000001, 'lb': 0.453592, 'oz': 0.0283495},
            'volume': {'l': 1, 'ml': 0.001, 'gal': 3.78541, 'qt': 0.946353, 'pt': 0.473176, 'cup': 0.236588}
        }
        
        cat_units = units.get(category)
        if f not in cat_units or t not in cat_units:
            return f"Unit '{f}' or '{t}' not recognized in category '{category}'."
        
        base_val = value * cat_units[f]
        res = base_val / cat_units[t]
        
        return f"Converting {value} {f} to {t} results in {round(res, 4)} {t}."


# --- 2. THE TORQUE ORCHESTRATOR ---

class Torque:
    """
    Torque: The Central Transmission for Ayra Gears.
    Aggregates all specialized tool classes into a single manifest for the AI.
    """

    _gears = [FinanceGears, WebGears, TextGears, UtilityGears]

    @classmethod
    def get_tool_manifest(cls) -> List[Dict[str, Any]]:
        """Consolidates manifests from all registered Gears."""
        full_manifest = []
        for gear in cls._gears:
            full_manifest.extend(gear.get_manifest())
        return full_manifest

    @classmethod
    def execute(cls, tool_name: str, **kwargs) -> str:
        """Dynamically routes a tool call to the correct Gear class."""
        for gear in cls._gears:
            if hasattr(gear, tool_name):
                method = getattr(gear, tool_name)
                try:
                    return method(**kwargs)
                except ValidationError as e:
                    err = e.errors()[0]
                    return f"Validation Error: The field '{err['loc'][0]}' {err['msg']}."
                except Exception as e:
                    return f"Execution Error: {str(e)}"
        return f"Tool '{tool_name}' not found."

# --- Verification ---
if __name__ == "__main__":
    print(Torque.execute("compound_interest", principal=1000, rate=1, rate_type="monthly", time_years=10, compounding_frequency="monthly"))
    print(Torque.execute("convert_units", value=100, category="length", from_unit="mi", to_unit="km"))
