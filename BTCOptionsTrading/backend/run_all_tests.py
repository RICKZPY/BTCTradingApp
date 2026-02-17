#!/usr/bin/env python3
"""
完整系统测试运行器
运行所有单元测试、集成测试和API测试
"""

import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.results: Dict[str, Dict] = {}
        self.start_time = None
        self.end_time = None
    
    def run_test_file(self, test_file: str, description: str) -> Tuple[bool, float, str]:
        """运行单个测试文件"""
        print(f"\n{'=' * 70}")
        print(f"Running: {description}")
        print(f"File: {test_file}")
        print(f"{'=' * 70}")
        
        start = time.time()
        
        try:
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            duration = time.time() - start
            
            # 打印输出
            if result.stdout:
                print(result.stdout)
            
            if result.stderr:
                print("STDERR:", result.stderr, file=sys.stderr)
            
            success = result.returncode == 0
            
            if success:
                print(f"\n✅ {description} PASSED ({duration:.2f}s)")
            else:
                print(f"\n❌ {description} FAILED ({duration:.2f}s)")
            
            return success, duration, result.stdout + result.stderr
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start
            print(f"\n⏱️  {description} TIMEOUT ({duration:.2f}s)")
            return False, duration, "Test timed out after 5 minutes"
        
        except Exception as e:
            duration = time.time() - start
            print(f"\n💥 {description} ERROR: {e}")
            return False, duration, str(e)
    
    def run_pytest_tests(self, description: str) -> Tuple[bool, float, str]:
        """运行pytest测试"""
        print(f"\n{'=' * 70}")
        print(f"Running: {description}")
        print(f"{'=' * 70}")
        
        start = time.time()
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            duration = time.time() - start
            
            # 打印输出
            if result.stdout:
                print(result.stdout)
            
            if result.stderr:
                print("STDERR:", result.stderr, file=sys.stderr)
            
            success = result.returncode == 0
            
            if success:
                print(f"\n✅ {description} PASSED ({duration:.2f}s)")
            else:
                print(f"\n❌ {description} FAILED ({duration:.2f}s)")
            
            return success, duration, result.stdout + result.stderr
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start
            print(f"\n⏱️  {description} TIMEOUT ({duration:.2f}s)")
            return False, duration, "Test timed out after 5 minutes"
        
        except Exception as e:
            duration = time.time() - start
            print(f"\n💥 {description} ERROR: {e}")
            return False, duration, str(e)
    
    def run_all_tests(self):
        """运行所有测试"""
        self.start_time = datetime.now()
        
        print("\n" + "=" * 70)
        print("HISTORICAL DATA INTEGRATION - COMPLETE SYSTEM TEST")
        print("=" * 70)
        print(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # 定义测试套件
        test_suites = [
            # 单元测试
            ("test_downloader.py", "Downloader Unit Tests"),
            ("test_converter.py", "Converter Unit Tests"),
            ("test_cache.py", "Cache Unit Tests"),
            ("test_validator.py", "Validator Unit Tests"),
            ("test_manager.py", "Manager Unit Tests"),
            
            # 集成测试
            ("test_backtest_integration.py", "Backtest Integration Tests"),
            ("test_historical_api.py", "API Integration Tests"),
        ]
        
        # 运行每个测试套件
        for test_file, description in test_suites:
            test_path = Path(test_file)
            
            if not test_path.exists():
                print(f"\n⚠️  Skipping {description}: File not found")
                self.results[description] = {
                    'success': False,
                    'duration': 0,
                    'output': 'File not found',
                    'skipped': True
                }
                continue
            
            success, duration, output = self.run_test_file(str(test_path), description)
            
            self.results[description] = {
                'success': success,
                'duration': duration,
                'output': output,
                'skipped': False
            }
        
        # 运行pytest测试（如果存在）
        if Path("tests").exists():
            success, duration, output = self.run_pytest_tests("Pytest Test Suite")
            self.results["Pytest Test Suite"] = {
                'success': success,
                'duration': duration,
                'output': output,
                'skipped': False
            }
        
        self.end_time = datetime.now()
        
        # 生成报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 70)
        print("TEST SUMMARY REPORT")
        print("=" * 70)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r['success'] and not r.get('skipped', False))
        failed_tests = sum(1 for r in self.results.values() if not r['success'] and not r.get('skipped', False))
        skipped_tests = sum(1 for r in self.results.values() if r.get('skipped', False))
        total_duration = sum(r['duration'] for r in self.results.values())
        
        print(f"\nStart Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End Time:   {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration:   {total_duration:.2f}s")
        
        print(f"\nTotal Test Suites: {total_tests}")
        print(f"  ✅ Passed:  {passed_tests}")
        print(f"  ❌ Failed:  {failed_tests}")
        print(f"  ⚠️  Skipped: {skipped_tests}")
        
        print("\nDetailed Results:")
        print("-" * 70)
        
        for name, result in self.results.items():
            if result.get('skipped', False):
                status = "⚠️  SKIPPED"
            elif result['success']:
                status = "✅ PASSED"
            else:
                status = "❌ FAILED"
            
            print(f"{status:12} {name:40} ({result['duration']:.2f}s)")
        
        print("\n" + "=" * 70)
        
        if failed_tests == 0 and skipped_tests == 0:
            print("🎉 ALL TESTS PASSED!")
            print("=" * 70)
            return True
        elif failed_tests == 0:
            print(f"⚠️  ALL TESTS PASSED (with {skipped_tests} skipped)")
            print("=" * 70)
            return True
        else:
            print(f"❌ {failed_tests} TEST SUITE(S) FAILED")
            print("=" * 70)
            return False
    
    def save_report(self, filename: str = "test_report.txt"):
        """保存测试报告到文件"""
        with open(filename, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("HISTORICAL DATA INTEGRATION - TEST REPORT\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"End Time:   {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration:   {sum(r['duration'] for r in self.results.values()):.2f}s\n\n")
            
            for name, result in self.results.items():
                f.write(f"\n{'=' * 70}\n")
                f.write(f"Test Suite: {name}\n")
                f.write(f"Status: {'PASSED' if result['success'] else 'FAILED'}\n")
                f.write(f"Duration: {result['duration']:.2f}s\n")
                f.write(f"{'=' * 70}\n\n")
                f.write(result['output'])
                f.write("\n\n")
        
        print(f"\n📄 Detailed report saved to: {filename}")


def main():
    """主函数"""
    runner = TestRunner()
    runner.run_all_tests()
    
    # 保存详细报告
    report_filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    runner.save_report(report_filename)
    
    # 返回退出码
    all_passed = all(r['success'] or r.get('skipped', False) for r in runner.results.values())
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
