"""
Ryanair API Client for fetching flight prices
"""

import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import time


class RyanairAPI:
    """Client for interacting with Ryanair's public API"""
    
    BASE_URL = "https://www.ryanair.com/api"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-GB,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": "https://www.ryanair.com",
            "Referer": "https://www.ryanair.com/",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        })
    
    def get_airports(self) -> List[Dict[str, Any]]:
        """Get list of all Ryanair airports"""
        url = f"{self.BASE_URL}/views/locate/5/airports/en/active"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def search_airports(self, query: str) -> List[Dict[str, Any]]:
        """Search airports by name or code"""
        airports = self.get_airports()
        query_lower = query.lower()
        return [
            airport for airport in airports
            if query_lower in airport.get("name", "").lower() 
            or query_lower in airport.get("iataCode", "").lower()
            or query_lower in airport.get("city", {}).get("name", "").lower()
        ]
    
    def get_destinations(self, origin: str) -> List[Dict[str, Any]]:
        """Get available destinations from an origin airport"""
        url = f"{self.BASE_URL}/views/locate/searchWidget/routes/en/airport/{origin}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_flights(
        self,
        origin: str,
        destination: str,
        date_out: str,
        date_in: Optional[str] = None,
        adults: int = 1,
        teens: int = 0,
        children: int = 0,
        infants: int = 0,
        flex_days_out: int = 0,
        flex_days_in: int = 0,
    ) -> Dict[str, Any]:
        """
        Search for available flights and prices
        
        Args:
            origin: Origin airport IATA code (e.g., 'DUB')
            destination: Destination airport IATA code (e.g., 'STN')
            date_out: Outbound date in YYYY-MM-DD format
            date_in: Return date in YYYY-MM-DD format (optional for one-way)
            adults: Number of adults (16+ years)
            teens: Number of teens (12-15 years)
            children: Number of children (2-11 years)
            infants: Number of infants (under 2 years)
            flex_days_out: Flex days for outbound (+/- days)
            flex_days_in: Flex days for return (+/- days)
        
        Returns:
            Flight search results with prices
        """
        url = f"{self.BASE_URL}/booking/v4/en-gb/availability"
        
        params = {
            "ADT": adults,
            "CHD": children,
            "DateIn": date_in or "",
            "DateOut": date_out,
            "Destination": destination,
            "Disc": 0,
            "INF": infants,
            "Origin": origin,
            "TEEN": teens,
            "promoCode": "",
            "IncludeConnectingFlights": "false",
            "FlexDaysBeforeOut": flex_days_out,
            "FlexDaysOut": flex_days_out,
            "FlexDaysBeforeIn": flex_days_in,
            "FlexDaysIn": flex_days_in,
            "ToUs": "AGREED",
        }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_cheapest_fares(
        self,
        origin: str,
        destination: str,
        date_out: str,
        flex_days: int = 6,
    ) -> Dict[str, Any]:
        """
        Get cheapest fares for a date range
        
        Args:
            origin: Origin airport IATA code
            destination: Destination airport IATA code
            date_out: Start date in YYYY-MM-DD format
            flex_days: Number of days to search (+/- from date_out)
        
        Returns:
            Cheapest fares data
        """
        url = f"{self.BASE_URL}/farfnd/v4/oneWayFares/{origin}/{destination}/cheapestPerDay"
        
        params = {
            "outboundDateFrom": date_out,
            "outboundDateTo": (datetime.strptime(date_out, "%Y-%m-%d") + timedelta(days=flex_days * 2)).strftime("%Y-%m-%d"),
        }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_monthly_prices(
        self,
        origin: str,
        destination: str,
        year_month: str,
    ) -> Dict[str, Any]:
        """
        Get prices for a whole month
        
        Args:
            origin: Origin airport IATA code
            destination: Destination airport IATA code
            year_month: Month in YYYY-MM format
        
        Returns:
            Monthly price data
        """
        url = f"{self.BASE_URL}/farfnd/v4/oneWayFares/{origin}/{destination}/cheapestPerDay"
        
        # Calculate first and last day of month
        year, month = map(int, year_month.split("-"))
        first_day = f"{year_month}-01"
        
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        last_day = (next_month - timedelta(days=1)).strftime("%Y-%m-%d")
        
        params = {
            "outboundDateFrom": first_day,
            "outboundDateTo": last_day,
        }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()


def format_flight_results(results: Dict[str, Any]) -> str:
    """Format flight search results for display"""
    output = []
    
    trips = results.get("trips", [])
    currency = results.get("currency", "EUR")
    
    for trip in trips:
        origin = trip.get("origin", "")
        destination = trip.get("destination", "")
        output.append(f"\n{'='*60}")
        output.append(f"Route: {origin} → {destination}")
        output.append(f"{'='*60}")
        
        dates = trip.get("dates", [])
        for date_info in dates:
            date_out = date_info.get("dateOut", "")
            flights = date_info.get("flights", [])
            
            if flights:
                output.append(f"\nDate: {date_out[:10]}")
                output.append("-" * 40)
                
                for flight in flights:
                    flight_number = flight.get("flightNumber", "N/A")
                    time_utc = flight.get("time", ["", ""])
                    departure = time_utc[0][11:16] if len(time_utc) > 0 and time_utc[0] else "N/A"
                    arrival = time_utc[1][11:16] if len(time_utc) > 1 and time_utc[1] else "N/A"
                    
                    regular_fare = flight.get("regularFare", {})
                    fares = regular_fare.get("fares", [])
                    
                    if fares:
                        for fare in fares:
                            fare_type = fare.get("type", "")
                            amount = fare.get("amount", 0)
                            output.append(
                                f"  Flight {flight_number}: {departure} - {arrival} | "
                                f"{fare_type}: {amount:.2f} {currency}"
                            )
                    else:
                        # Check for business fares
                        business_fare = flight.get("businessFare", {})
                        if business_fare:
                            amount = business_fare.get("amount", 0)
                            output.append(
                                f"  Flight {flight_number}: {departure} - {arrival} | "
                                f"Business: {amount:.2f} {currency}"
                            )
                        else:
                            output.append(
                                f"  Flight {flight_number}: {departure} - {arrival} | "
                                f"No fares available"
                            )
    
    return "\n".join(output) if output else "No flights found"


def format_cheapest_fares(results: Dict[str, Any]) -> str:
    """Format cheapest fares results for display"""
    output = []
    
    if not results:
        return "No fares found for the specified route and dates"
    
    # Handle different API response formats
    outbound = results.get("outbound") or {}
    fares = outbound.get("fares", [])
    
    # Alternative format: direct fares array
    if not fares and isinstance(results, list):
        fares = results
    
    if not fares:
        return "No fares found for the specified route and dates"
    
    output.append(f"\n{'='*60}")
    output.append("Cheapest Fares by Date")
    output.append(f"{'='*60}\n")
    
    # Sort fares by price
    valid_fares = []
    for f in fares:
        if not f:
            continue
        price = f.get("price") or {}
        if price.get("value"):
            valid_fares.append(f)
    
    sorted_fares = sorted(valid_fares, key=lambda x: (x.get("price") or {}).get("value", float("inf")))
    
    for fare in sorted_fares:
        day = fare.get("day", "")
        price = fare.get("price") or {}
        amount = price.get("value", 0)
        currency = price.get("currencyCode", "EUR")
        
        if amount:
            output.append(f"  {day}: {amount:.2f} {currency}")
    
    return "\n".join(output) if output else "No fares available"
