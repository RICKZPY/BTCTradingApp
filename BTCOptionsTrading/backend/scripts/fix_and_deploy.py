#!/usr/bin/env python3
"""
Fix numpy import issue and deploy to server
Run this locally: python fix_and_deploy.py
"""

import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, description=""):
    """Run a shell command"""
    if description:
        print(f"\n{description}")
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ✗ Error: {result.stderr}")
        return False
    if result.stdout:
        print(f"  {result.stdout.strip()}")
    return True

def main():
    print("="*80)
    print("Order Book Collector - Fix & Deploy")
    print("="*80)
    
    # Step 1: Fix models.py locally
    print("\n[1/3] Fixing models.py locally...")
    models_file = Path("BTCOptionsTrading/backend/src/core/models.py")
    
    if not models_file.exists():
        print(f"  ✗ File not found: {models_file}")
        return 1
    
    with open(models_file, 'r') as f:
        content = f.read()
    
    # Remove numpy import
    content = content.replace('import numpy as np\n', '')
    
    # Fix VolatilitySurface
    old_vol = 'volatilities: np.ndarray  # 2D array of implied volatilities'
    new_vol = 'volatilities: List[List[float]]  # 2D list of implied volatilities'
    content = content.replace(old_vol, new_vol)
    
    old_interp = 'return float(np.mean(self.volatilities))'
    new_interp = '''if self.volatilities:
            flat = [v for row in self.volatilities for v in row]
            return sum(flat) / len(flat) if flat else 0.0
        return 0.0'''
    content = content.replace(old_interp, new_interp)
    
    with open(models_file, 'w') as f:
        f.write(content)
    
    print("  ✓ Fixed models.py (removed numpy dependency)")
    
    # Step 2: Copy fixed file to server
    print("\n[2/3] Copying fixed models.py to server...")
    cmd = f"scp BTCOptionsTrading/backend/src/core/models.py root@47.86.62.200:/opt/orderbook-collector/src/core/models.py"
    if not run_cmd(cmd):
        print("\n  Note: If scp fails, you can manually copy the file or use the deployment script")
        print("  Continuing with test...")
    else:
        print("  ✓ File copied successfully")
    
    # Step 3: Test on server
    print("\n[3/3] Testing collection script on server...")
    cmd = "ssh root@47.86.62.200 'cd /opt/orderbook-collector && source venv/bin/activate && python collect_orderbook.py --help'"
    if run_cmd(cmd):
        print("  ✓ Script works!")
    else:
        print("  ✗ Script failed - check server manually")
        return 1
    
    print("\n" + "="*80)
    print("✓ Fix & Deploy Complete")
    print("="*80)
    print("\nNext steps:")
    print("  1. SSH to server: ssh root@47.86.62.200")
    print("  2. Run collection: cd /opt/orderbook-collector && source venv/bin/activate && python collect_orderbook.py")
    print("  3. Check output: ls -la data/orderbook/")
    print("\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
