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
                "intent": "Calculate investment growth with compound interest.",
                "parameters": {
                    "principal": {"type": "number", "description": "The initial amount invested."},
                    "rate": {"type": "number", "description": "The annual interest rate percentage."},
                    "time": {"type": "number", "description": "Number of years invested."},
                    "n": {"type": "integer", "description": "Times compounded per year (default 12)."}
                },
                "sample_output": "The total value after 10 years will be $2,009.66."
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
        time: float = Field(..., gt=0),
        n: int = Field(12, gt=0)
    ) -> str:
        amount = principal * (1 + (rate/100)/n)**(n*time)
        return f"Starting with ${principal:,.2f} at {rate}% compounded {n}x yearly, the value after {time} years is ${amount:,.2f}."


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


# --- 2. THE TORQUE ORCHESTRATOR ---

class Torque:
    """
    Torque: The Central Transmission for Ayra Gears.
    Aggregates all specialized tool classes into a single manifest for the AI.
    """

    # Register gear classes here
    _gears = [FinanceGears, WebGears, TextGears]

    @classmethod
    def get_tool_manifest(cls) -> List[Dict[str, Any]]:
        """Consolidates manifests from all registered Gears."""
        full_manifest = []
        for gear in cls._gears:
            full_manifest.extend(gear.get_manifest())
        return full_manifest

    @classmethod
    def execute(cls, tool_name: str, **kwargs) -> str:
        """
        Dynamically routes a tool call to the correct Gear class.
        Includes a safety wrapper for validation errors.
        """
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
        
        return f"Tool '{tool_name}' not found in any registered Gear."

# --- Quick Verification ---
if __name__ == "__main__":
    # Simulate an AI searching for all tools
    print(f"🤖 Torque Discovery: {len(Torque.get_tool_manifest())} tools active.")
    
    # Test execution via the Torque central hub
    print("\n⚡ Executing Mortgage Tool via Torque:")
    result = Torque.execute("mortgage_calculator", principal=350000, annual_rate=6.2, years=30)
    print(result)

    print("\n⚡ Executing Weather Tool via Torque:")
    result = Torque.execute("get_weather", city="Vancouver")
    print(result)

    print("\n❌ Testing Validation via Torque:")
    result = Torque.execute("mortgage_calculator", principal=-500, annual_rate=5, years=30)
    print(result)
