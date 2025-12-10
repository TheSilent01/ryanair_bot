#!/usr/bin/env python3
"""
Ryanair Flight Price Checker - Agadir to Fez
Check flight prices from the command line
"""

import argparse
import requests
from datetime import datetime, timedelta
import sys


def get_flights(days: int = 60, specific_date: str = None):
    """Fetch flight prices from Ryanair API"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    })
    
    if specific_date:
        start_date = specific_date
        end_date = specific_date
    else:
        start_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    
    url = 'https://www.ryanair.com/api/farfnd/v4/oneWayFares/AGA/FEZ/cheapestPerDay'
    params = {'outboundDateFrom': start_date, 'outboundDateTo': end_date}
    
    try:
        response = session.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ Error fetching flights: {e}")
        sys.exit(1)


def display_flights(data, show_all: bool = True, price_limit: float = None):
    """Display flight prices"""
    print()
    print('✈️  RYANAIR FLIGHT PRICES')
    print('🛫 Agadir (AGA) → Fez (FEZ)')
    print('=' * 55)
    
    fares = data.get('outbound', {}).get('fares', [])
    valid_fares = [f for f in fares if f and f.get('price') and not f.get('unavailable')]
    
    # Apply price limit filter if specified
    if price_limit is not None:
        valid_fares = [f for f in valid_fares if f['price']['value'] <= price_limit]
        if valid_fares:
            print(f'💰 Showing flights ≤ {price_limit:.0f} MAD')
        else:
            print(f'\n❌ No flights found under {price_limit:.0f} MAD\n')
            return
    
    if not valid_fares:
        print('\n❌ No flights available for this period\n')
        return
    
    # Sort by price to find lowest
    valid_fares.sort(key=lambda x: x['price']['value'])
    lowest = valid_fares[0]
    
    print()
    print(f"🏆 LOWEST PRICE: {lowest['price']['value']:.2f} MAD")
    lowest_day = datetime.strptime(lowest['day'], '%Y-%m-%d').strftime('%A')
    print(f"📅 Date: {lowest['day']} ({lowest_day})")
    dep = lowest['departureDate'][11:16] if lowest['departureDate'] else 'N/A'
    arr = lowest['arrivalDate'][11:16] if lowest['arrivalDate'] else 'N/A'
    print(f"🕐 Time: {dep} → {arr}")
    print()
    
    if show_all and len(valid_fares) > 1:
        print('=' * 55)
        print('📊 ALL AVAILABLE FLIGHTS (sorted by date):')
        print('=' * 55)
        print()
        print(f"{'Date':<12} {'Day':<10} {'Time':<13} {'Price':>12}")
        print('-' * 55)
        
        # Sort by date for display
        by_date = sorted(valid_fares, key=lambda x: x['day'])
        for fare in by_date:
            p = fare['price']
            dep = fare['departureDate'][11:16] if fare['departureDate'] else 'N/A'
            arr = fare['arrivalDate'][11:16] if fare['arrivalDate'] else 'N/A'
            day_name = datetime.strptime(fare['day'], '%Y-%m-%d').strftime('%A')
            emoji = '🟢' if p['value'] == lowest['price']['value'] else '  '
            print(f"{emoji}{fare['day']}  {day_name:<10} {dep}→{arr}    {p['value']:>8.2f} MAD")
        
        print()
        print(f"Total available flights: {len(valid_fares)}")
    
    print()


def main():
    parser = argparse.ArgumentParser(
        description='🛫 Ryanair Flight Price Checker - Agadir (AGA) → Fez (FEZ)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
FLIGHT SCHEDULE:
  📅 Saturdays:  09:35 → 10:55 (1h 20min)
  📅 Tuesdays:   10:05 → 11:25 (1h 20min)

EXAMPLES:
  %(prog)s                    # Show all flights for next 60 days
  %(prog)s --days 30          # Show flights for next 30 days
  %(prog)s --date 2025-12-20  # Check specific date
  %(prog)s --lowest           # Show only lowest price
  %(prog)s --limit 200        # Show flights under 200 MAD
  %(prog)s -d 30 --limit 150  # Flights under 150 MAD in next 30 days

PRICE LEGEND:
  🟢 Lowest price available
  💰 Price limit filter active
'''
    )
    
    parser.add_argument(
        '--days', '-d',
        type=int,
        default=60,
        help='Number of days to search (default: 60)'
    )
    
    parser.add_argument(
        '--date',
        type=str,
        help='Check specific date (YYYY-MM-DD format)'
    )
    
    parser.add_argument(
        '--lowest', '-l',
        action='store_true',
        help='Show only the lowest price'
    )
    
    parser.add_argument(
        '--limit', '--max-price', '-m',
        type=float,
        help='Show only flights at or below this price (in MAD)'
    )
    
    args = parser.parse_args()
    
    # Validate date format if provided
    if args.date:
        try:
            datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            print("❌ Invalid date format. Use YYYY-MM-DD (e.g., 2025-12-20)")
            sys.exit(1)
    
    # Fetch and display flights
    data = get_flights(days=args.days, specific_date=args.date)
    display_flights(data, show_all=not args.lowest, price_limit=args.limit)


if __name__ == '__main__':
    main()
