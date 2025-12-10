#!/usr/bin/env python3
"""
Ryanair Flight Price Checker - Command Line Interface

Usage examples:
    python main.py search DUB STN 2025-01-15
    python main.py search DUB STN 2025-01-15 --return 2025-01-20
    python main.py cheapest DUB STN 2025-01-15
    python main.py monthly DUB STN 2025-01
    python main.py airports dublin
    python main.py destinations DUB
"""

import argparse
import sys
from datetime import datetime, timedelta

from ryanair_api import (
    RyanairAPI,
    format_flight_results,
    format_cheapest_fares,
)


def search_flights(args):
    """Search for flights between two airports"""
    api = RyanairAPI()
    
    print(f"\nSearching flights from {args.origin} to {args.destination}...")
    print(f"Date: {args.date}")
    if args.return_date:
        print(f"Return: {args.return_date}")
    print(f"Passengers: {args.adults} adult(s)")
    
    try:
        results = api.get_flights(
            origin=args.origin.upper(),
            destination=args.destination.upper(),
            date_out=args.date,
            date_in=args.return_date,
            adults=args.adults,
            flex_days_out=args.flex,
        )
        print(format_flight_results(results))
    except Exception as e:
        print(f"Error searching flights: {e}")
        sys.exit(1)


def get_cheapest(args):
    """Get cheapest fares for a date range"""
    api = RyanairAPI()
    
    print(f"\nFinding cheapest fares from {args.origin} to {args.destination}...")
    print(f"Starting from: {args.date}")
    
    try:
        results = api.get_cheapest_fares(
            origin=args.origin.upper(),
            destination=args.destination.upper(),
            date_out=args.date,
            flex_days=args.days,
        )
        print(format_cheapest_fares(results))
    except Exception as e:
        print(f"Error fetching cheapest fares: {e}")
        sys.exit(1)


def get_monthly(args):
    """Get prices for a whole month"""
    api = RyanairAPI()
    
    print(f"\nFetching monthly prices from {args.origin} to {args.destination}...")
    print(f"Month: {args.month}")
    
    try:
        results = api.get_monthly_prices(
            origin=args.origin.upper(),
            destination=args.destination.upper(),
            year_month=args.month,
        )
        print(format_cheapest_fares(results))
    except Exception as e:
        print(f"Error fetching monthly prices: {e}")
        sys.exit(1)


def search_airports(args):
    """Search for airports by name or code"""
    api = RyanairAPI()
    
    print(f"\nSearching airports matching '{args.query}'...\n")
    
    try:
        airports = api.search_airports(args.query)
        
        if not airports:
            print("No airports found matching your query")
            return
        
        print(f"Found {len(airports)} airport(s):\n")
        for airport in airports[:20]:  # Limit to 20 results
            code = airport.get("iataCode", "N/A")
            name = airport.get("name", "N/A")
            city = airport.get("city", {}).get("name", "N/A")
            country = airport.get("country", {}).get("name", "N/A")
            print(f"  [{code}] {name}")
            print(f"       {city}, {country}\n")
            
    except Exception as e:
        print(f"Error searching airports: {e}")
        sys.exit(1)


def get_destinations(args):
    """Get available destinations from an airport"""
    api = RyanairAPI()
    
    print(f"\nFetching destinations from {args.origin}...\n")
    
    try:u
        destinations = api.get_destinations(args.origin.upper())
        
        if not destinations:
            print("No destinations found from this airport")
            return
        
        print(f"Available destinations from {args.origin.upper()}:\n")
        for dest in destinations:
            arrival_airport = dest.get("arrivalAirport", {})
            code = arrival_airport.get("iataCode", "N/A")
            name = arrival_airport.get("name", "N/A")
            country = arrival_airport.get("country", {}).get("name", "N/A")
            print(f"  [{code}] {name}, {country}")
            
    except Exception as e:
        print(f"Error fetching destinations: {e}")
        sys.exit(1)


def interactive_mode():
    """Run in interactive mode"""
    api = RyanairAPI()
    
    print("\n" + "="*60)
    print("  RYANAIR FLIGHT PRICE CHECKER - Interactive Mode")
    print("="*60)
    
    # Get origin
    origin = input("\nEnter origin airport code (e.g., DUB, STN, BCN): ").strip().upper()
    if not origin:
        print("Origin is required")
        return
    
    # Get destination  
    destination = input("Enter destination airport code: ").strip().upper()
    if not destination:
        print("Destination is required")
        return
    
    # Get date
    default_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    date_input = input(f"Enter departure date (YYYY-MM-DD) [{default_date}]: ").strip()
    date_out = date_input if date_input else default_date
    
    # Ask about return
    return_input = input("Enter return date (YYYY-MM-DD) or press Enter for one-way: ").strip()
    date_in = return_input if return_input else None
    
    # Number of passengers
    adults_input = input("Number of adults [1]: ").strip()
    adults = int(adults_input) if adults_input else 1
    
    print(f"\nSearching flights from {origin} to {destination}...")
    
    try:
        results = api.get_flights(
            origin=origin,
            destination=destination,
            date_out=date_out,
            date_in=date_in,
            adults=adults,
        )
        print(format_flight_results(results))
        
        # Also show cheapest options
        print("\n" + "="*60)
        print("Looking for cheaper alternatives nearby...")
        cheap_results = api.get_cheapest_fares(origin, destination, date_out, flex_days=7)
        print(format_cheapest_fares(cheap_results))
        
    except Exception as e:
        print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Ryanair Flight Price Checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s search DUB STN 2025-01-15
  %(prog)s search DUB STN 2025-01-15 --return 2025-01-20 --adults 2
  %(prog)s cheapest DUB BCN 2025-02-01 --days 14
  %(prog)s monthly DUB STN 2025-03
  %(prog)s airports dublin
  %(prog)s destinations DUB
  %(prog)s interactive
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for flights")
    search_parser.add_argument("origin", help="Origin airport code (e.g., DUB)")
    search_parser.add_argument("destination", help="Destination airport code (e.g., STN)")
    search_parser.add_argument("date", help="Departure date (YYYY-MM-DD)")
    search_parser.add_argument("--return", dest="return_date", help="Return date (YYYY-MM-DD)")
    search_parser.add_argument("--adults", type=int, default=1, help="Number of adults (default: 1)")
    search_parser.add_argument("--flex", type=int, default=0, help="Flex days +/- (default: 0)")
    search_parser.set_defaults(func=search_flights)
    
    # Cheapest command
    cheapest_parser = subparsers.add_parser("cheapest", help="Get cheapest fares for a date range")
    cheapest_parser.add_argument("origin", help="Origin airport code")
    cheapest_parser.add_argument("destination", help="Destination airport code")
    cheapest_parser.add_argument("date", help="Start date (YYYY-MM-DD)")
    cheapest_parser.add_argument("--days", type=int, default=14, help="Number of days to search (default: 14)")
    cheapest_parser.set_defaults(func=get_cheapest)
    
    # Monthly command
    monthly_parser = subparsers.add_parser("monthly", help="Get prices for a whole month")
    monthly_parser.add_argument("origin", help="Origin airport code")
    monthly_parser.add_argument("destination", help="Destination airport code")
    monthly_parser.add_argument("month", help="Month (YYYY-MM)")
    monthly_parser.set_defaults(func=get_monthly)
    
    # Airports command
    airports_parser = subparsers.add_parser("airports", help="Search for airports")
    airports_parser.add_argument("query", help="Airport name or code to search")
    airports_parser.set_defaults(func=search_airports)
    
    # Destinations command
    dest_parser = subparsers.add_parser("destinations", help="Get destinations from an airport")
    dest_parser.add_argument("origin", help="Origin airport code")
    dest_parser.set_defaults(func=get_destinations)
    
    # Interactive command
    interactive_parser = subparsers.add_parser("interactive", help="Run in interactive mode")
    interactive_parser.set_defaults(func=lambda args: interactive_mode())
    
    args = parser.parse_args()
    
    if not args.command:
        # Default to interactive mode if no command given
        interactive_mode()
    else:
        args.func(args)


if __name__ == "__main__":
    main()
