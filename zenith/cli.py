import argparse
import sys
from zenith.api import status

def main():
    parser = argparse.ArgumentParser(description="Zenith CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    subparsers.add_parser("status", help="Show status")
    subparsers.add_parser("cache", help="Manage cache")
    subparsers.add_parser("profile", help="Profile an application")
    subparsers.add_parser("analyze", help="Analyze imports")
    
    args = parser.parse_args()
    
    if args.command == "status":
        s = status()
        print(f"[Zenith Status]")
        for k, v in s.items():
            print(f"{k}: {v}")
    elif args.command == "cache":
        print("Cache management")
    elif args.command == "profile":
        print("Profiling")
    elif args.command == "analyze":
        print("Analyzing")
    else:
        parser.print_help()
        
if __name__ == "__main__":
    main()
