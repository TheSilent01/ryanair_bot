#!/usr/bin/env python3
"""
Ryanair Flight Price Checker - Agadir to Fez
A beautiful CLI tool to check flight prices
"""

import argparse
import requests
from datetime import datetime, timedelta
import sys
import os


# ANSI color codes
class C:
    # Colors
    BLACK = '\033[30m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    
    # Background
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    
    # Reset
    R = '\033[0m'


def supports_color():
    """Check if terminal supports colors"""
    if os.getenv('NO_COLOR'):
        return False
    if os.getenv('FORCE_COLOR'):
        return True
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()


# Disable colors if not supported
if not supports_color():
    for attr in dir(C):
        if not attr.startswith('_'):
            setattr(C, attr, '')


def print_banner():
    """Print the beautiful header banner"""
    print()
    print(f"{C.CYAN}{C.BOLD}╔════════════════════════════════════════════════════════════════╗{C.R}")
    print(f"{C.CYAN}{C.BOLD}║{C.R}                                                                {C.CYAN}{C.BOLD}║{C.R}")
    print(f"{C.CYAN}{C.BOLD}║{C.R}   {C.YELLOW}✈️ {C.WHITE}{C.BOLD} R Y A N A I R   F L I G H T   C H E C K E R{C.R}   {C.YELLOW}✈️{C.R}        {C.CYAN}{C.BOLD}║{C.R}")
    print(f"{C.CYAN}{C.BOLD}║{C.R}                                                                {C.CYAN}{C.BOLD}║{C.R}")
    print(f"{C.CYAN}{C.BOLD}╠════════════════════════════════════════════════════════════════╣{C.R}")
    print(f"{C.CYAN}{C.BOLD}║{C.R}                                                                {C.CYAN}{C.BOLD}║{C.R}")
    print(f"{C.CYAN}{C.BOLD}║{C.R}       {C.GREEN}🛫{C.R}  {C.WHITE}{C.BOLD}AGADIR{C.R} {C.DIM}(AGA){C.R}  {C.DIM}══════►{C.R}  {C.WHITE}{C.BOLD}FEZ{C.R} {C.DIM}(FEZ){C.R}  {C.GREEN}🛬{C.R}            {C.CYAN}{C.BOLD}║{C.R}")
    print(f"{C.CYAN}{C.BOLD}║{C.R}                                                                {C.CYAN}{C.BOLD}║{C.R}")
    print(f"{C.CYAN}{C.BOLD}╚════════════════════════════════════════════════════════════════╝{C.R}")
    print()


def print_loading():
    """Print loading message"""
    print(f"  {C.CYAN}⏳{C.R} {C.DIM}Fetching prices from Ryanair...{C.R}")


def print_error(message):
    """Print error message"""
    print()
    print(f"  {C.RED}╭─────────────────────────────────────────────╮{C.R}")
    print(f"  {C.RED}│{C.R}  {C.RED}❌ ERROR{C.R}                                    {C.RED}│{C.R}")
    print(f"  {C.RED}│{C.R}  {C.WHITE}{message:<40}{C.R}   {C.RED}│{C.R}")
    print(f"  {C.RED}╰─────────────────────────────────────────────╯{C.R}")
    print()


def print_no_flights(price_limit=None):
    """Print no flights message"""
    print()
    if price_limit:
        msg = f"No flights found under {price_limit:.0f} MAD"
    else:
        msg = "No flights available for this period"
    
    print(f"  {C.YELLOW}╭─────────────────────────────────────────────╮{C.R}")
    print(f"  {C.YELLOW}│{C.R}  {C.YELLOW}⚠️  {msg:<38}{C.R} {C.YELLOW}│{C.R}")
    print(f"  {C.YELLOW}╰─────────────────────────────────────────────╯{C.R}")
    print()


def price_color(price, lowest_price):
    """Get color based on price"""
    if price == lowest_price:
        return C.GREEN
    elif price <= lowest_price * 1.1:  # Within 10% of lowest
        return C.CYAN
    elif price <= lowest_price * 1.25:  # Within 25% of lowest
        return C.YELLOW
    else:
        return C.WHITE


def format_price_bar(price, lowest_price, max_price):
    """Create a visual price bar"""
    if max_price == lowest_price:
        return ""
    
    # Calculate bar length (max 20 chars)
    ratio = (price - lowest_price) / (max_price - lowest_price)
    bar_len = int(ratio * 15)
    
    if price == lowest_price:
        return f"{C.GREEN}{'█' * 1}{C.R}"
    else:
        return f"{C.DIM}{'░' * bar_len}{C.R}"


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
        print_error(f"Connection failed: {str(e)[:30]}")
        sys.exit(1)


def display_flights(data, show_all: bool = True, price_limit: float = None):
    """Display flight prices with beautiful formatting"""
    
    fares = data.get('outbound', {}).get('fares', [])
    valid_fares = [f for f in fares if f and f.get('price') and not f.get('unavailable')]
    
    # Apply price limit filter if specified
    if price_limit is not None:
        valid_fares = [f for f in valid_fares if f['price']['value'] <= price_limit]
        if not valid_fares:
            print_no_flights(price_limit)
            return
        print(f"  {C.CYAN}💰{C.R} {C.DIM}Filtering: prices ≤ {C.WHITE}{price_limit:.0f} MAD{C.R}")
        print()
    
    if not valid_fares:
        print_no_flights()
        return
    
    # Sort by price to find lowest
    valid_fares.sort(key=lambda x: x['price']['value'])
    lowest = valid_fares[0]
    highest = valid_fares[-1] if len(valid_fares) > 1 else lowest
    lowest_price = lowest['price']['value']
    highest_price = highest['price']['value']
    
    # Display best price box
    lowest_day = datetime.strptime(lowest['day'], '%Y-%m-%d').strftime('%A')
    dep = lowest['departureDate'][11:16] if lowest.get('departureDate') else 'N/A'
    arr = lowest['arrivalDate'][11:16] if lowest.get('arrivalDate') else 'N/A'
    
    print(f"  {C.GREEN}╭─────────────────────────────────────────────────────────╮{C.R}")
    print(f"  {C.GREEN}│{C.R}                                                         {C.GREEN}│{C.R}")
    print(f"  {C.GREEN}│{C.R}      {C.YELLOW}🏆{C.R}  {C.WHITE}{C.BOLD}BEST PRICE FOUND!{C.R}                            {C.GREEN}│{C.R}")
    print(f"  {C.GREEN}│{C.R}                                                         {C.GREEN}│{C.R}")
    print(f"  {C.GREEN}│{C.R}      {C.GREEN}{C.BOLD}💰 {lowest_price:>7.2f} MAD{C.R}                                {C.GREEN}│{C.R}")
    print(f"  {C.GREEN}│{C.R}                                                         {C.GREEN}│{C.R}")
    print(f"  {C.GREEN}│{C.R}      {C.CYAN}📅{C.R} {C.WHITE}{lowest['day']}{C.R} {C.DIM}({lowest_day}){C.R}                       {C.GREEN}│{C.R}")
    print(f"  {C.GREEN}│{C.R}      {C.CYAN}🕐{C.R} {C.WHITE}{dep}{C.R} {C.DIM}→{C.R} {C.WHITE}{arr}{C.R} {C.DIM}(1h 20min){C.R}                       {C.GREEN}│{C.R}")
    print(f"  {C.GREEN}│{C.R}                                                         {C.GREEN}│{C.R}")
    print(f"  {C.GREEN}╰─────────────────────────────────────────────────────────╯{C.R}")
    print()
    
    if show_all and len(valid_fares) > 1:
        # Statistics
        avg_price = sum(f['price']['value'] for f in valid_fares) / len(valid_fares)
        
        print(f"  {C.DIM}┌──────────────────────────────────────────────────────────┐{C.R}")
        print(f"  {C.DIM}│{C.R}  {C.WHITE}{C.BOLD}📊 PRICE STATISTICS{C.R}                                       {C.DIM}│{C.R}")
        print(f"  {C.DIM}├──────────────────────────────────────────────────────────┤{C.R}")
        print(f"  {C.DIM}│{C.R}  {C.GREEN}▼ Lowest:{C.R}  {C.WHITE}{lowest_price:>7.2f} MAD{C.R}    {C.RED}▲ Highest:{C.R} {C.WHITE}{highest_price:>7.2f} MAD{C.R}   {C.DIM}│{C.R}")
        print(f"  {C.DIM}│{C.R}  {C.CYAN}◆ Average:{C.R} {C.WHITE}{avg_price:>7.2f} MAD{C.R}    {C.YELLOW}# Flights:{C.R} {C.WHITE}{len(valid_fares):>7}{C.R}       {C.DIM}│{C.R}")
        print(f"  {C.DIM}└──────────────────────────────────────────────────────────┘{C.R}")
        print()
        
        # All flights table
        print(f"  {C.CYAN}{C.BOLD}┌──────────────────────────────────────────────────────────┐{C.R}")
        print(f"  {C.CYAN}{C.BOLD}│{C.R}  {C.WHITE}{C.BOLD}📋 ALL AVAILABLE FLIGHTS{C.R}                                 {C.CYAN}{C.BOLD}│{C.R}")
        print(f"  {C.CYAN}{C.BOLD}├──────────────────────────────────────────────────────────┤{C.R}")
        print(f"  {C.CYAN}{C.BOLD}│{C.R}  {C.DIM}DATE         DAY        TIME          PRICE{C.R}           {C.CYAN}{C.BOLD}│{C.R}")
        print(f"  {C.CYAN}{C.BOLD}├──────────────────────────────────────────────────────────┤{C.R}")
        
        # Sort by date for display
        by_date = sorted(valid_fares, key=lambda x: x['day'])
        for fare in by_date:
            p = fare['price']['value']
            dep = fare['departureDate'][11:16] if fare.get('departureDate') else 'N/A'
            arr = fare['arrivalDate'][11:16] if fare.get('arrivalDate') else 'N/A'
            day_name = datetime.strptime(fare['day'], '%Y-%m-%d').strftime('%a')
            
            # Choose color and emoji based on price
            if p == lowest_price:
                emoji = f"{C.GREEN}★{C.R}"
                color = C.GREEN
            elif p <= lowest_price * 1.1:
                emoji = f"{C.CYAN}◆{C.R}"
                color = C.CYAN
            else:
                emoji = f"{C.DIM}○{C.R}"
                color = C.WHITE
            
            bar = format_price_bar(p, lowest_price, highest_price)
            
            print(f"  {C.CYAN}{C.BOLD}│{C.R}  {emoji} {C.WHITE}{fare['day']}{C.R}  {C.DIM}{day_name:<4}{C.R}  {C.WHITE}{dep}{C.R}{C.DIM}→{C.R}{C.WHITE}{arr}{C.R}    {color}{C.BOLD}{p:>7.2f}{C.R} {C.DIM}MAD{C.R} {bar}  {C.CYAN}{C.BOLD}│{C.R}")
        
        print(f"  {C.CYAN}{C.BOLD}└──────────────────────────────────────────────────────────┘{C.R}")
        print()
        
        # Legend
        print(f"  {C.DIM}Legend:{C.R} {C.GREEN}★{C.R} {C.DIM}Best price{C.R}  {C.CYAN}◆{C.R} {C.DIM}Great deal (<10% above lowest){C.R}  {C.DIM}○ Regular{C.R}")
    
    print()


def main():
    parser = argparse.ArgumentParser(
        description=f'{C.CYAN}✈️  Ryanair Flight Price Checker{C.R} - Agadir (AGA) → Fez (FEZ)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
{C.CYAN}FLIGHT SCHEDULE:{C.R}
  {C.YELLOW}📅{C.R} Saturdays:  09:35 → 10:55 (1h 20min)
  {C.YELLOW}📅{C.R} Tuesdays:   10:05 → 11:25 (1h 20min)

{C.CYAN}EXAMPLES:{C.R}
  {C.GREEN}%(prog)s{C.R}                    {C.DIM}# All flights for next 60 days{C.R}
  {C.GREEN}%(prog)s -d 30{C.R}              {C.DIM}# Flights for next 30 days{C.R}
  {C.GREEN}%(prog)s --date 2025-12-20{C.R}  {C.DIM}# Check specific date{C.R}
  {C.GREEN}%(prog)s -l{C.R}                 {C.DIM}# Show only lowest price{C.R}
  {C.GREEN}%(prog)s -m 200{C.R}             {C.DIM}# Flights under 200 MAD{C.R}
  {C.GREEN}%(prog)s -d 30 -m 150{C.R}       {C.DIM}# Under 150 MAD in next 30 days{C.R}

{C.CYAN}PRICE LEGEND:{C.R}
  {C.GREEN}★{C.R} Lowest price    {C.CYAN}◆{C.R} Great deal    {C.DIM}○{C.R} Regular price
'''
    )
    
    parser.add_argument(
        '--days', '-d',
        type=int,
        default=60,
        metavar='N',
        help='Number of days to search (default: 60)'
    )
    
    parser.add_argument(
        '--date',
        type=str,
        metavar='DATE',
        help='Check specific date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--lowest', '-l',
        action='store_true',
        help='Show only the lowest price'
    )
    
    parser.add_argument(
        '--limit', '--max-price', '-m',
        type=float,
        metavar='PRICE',
        help='Max price filter (in MAD)'
    )
    
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )
    
    args = parser.parse_args()
    
    # Disable colors if requested
    if args.no_color:
        for attr in dir(C):
            if not attr.startswith('_'):
                setattr(C, attr, '')
    
    # Print banner
    print_banner()
    
    # Validate date format if provided
    if args.date:
        try:
            datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            print_error("Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)
    
    # Show search info
    if args.date:
        print(f"  {C.CYAN}📅{C.R} {C.DIM}Searching for:{C.R} {C.WHITE}{args.date}{C.R}")
    else:
        print(f"  {C.CYAN}📅{C.R} {C.DIM}Searching next{C.R} {C.WHITE}{args.days}{C.R} {C.DIM}days...{C.R}")
    
    print_loading()
    print()
    
    # Fetch and display flights
    data = get_flights(days=args.days, specific_date=args.date)
    display_flights(data, show_all=not args.lowest, price_limit=args.limit)


if __name__ == '__main__':
    main()
