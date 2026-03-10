# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Continuous Process Resource Waste
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate continuous resource occupation
  - **Scoped PBT Approach**: Scope the property to non-trading hours (e.g., 6:00-4:59) to ensure reproducibility
  - Test that service maintains persistent process and connections during non-trading hours
  - Verify process exists when it should not (isBugCondition: hasWhileTrueLoop AND hasTimeCheckingLogic AND maintainsPersistentConnection)
  - Monitor resource occupation (CPU, memory, WebSocket connections) over time
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (process exists and consumes resources when it shouldn't)
  - Document counterexamples found (e.g., "Process runs continuously for 1 hour consuming 50MB RAM during non-trading hours")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Trading Logic and Configuration Compatibility
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for trading execution scenarios
  - Test sentiment analysis logic produces same results (analyze_sentiment method)
  - Test strategy selection logic remains unchanged (execute_sentiment_strategy method)
  - Test trading execution produces same orders and history format
  - Test error handling and logging format remain unchanged
  - Test configuration compatibility (mainnet/testnet mixed mode)
  - Test data file formats remain unchanged (sentiment_trading_history.json, current_positions.json)
  - Write property-based tests capturing observed behavior patterns
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

- [x] 3. Refactor sentiment_trading_service.py to cron-compatible execution model

  - [x] 3.1 Remove continuous execution loop from run() method
    - Remove `while True:` loop from run() method
    - Remove time checking logic (`if current_time.hour == CHECK_TIME.hour`)
    - Remove `await asyncio.sleep(60)` polling delay
    - Remove `last_check_date` duplicate execution check (cron guarantees no duplicates)
    - _Bug_Condition: isBugCondition(deployment) where hasWhileTrueLoop AND hasTimeCheckingLogic_
    - _Expected_Behavior: Service executes once and exits cleanly_
    - _Preservation: All trading logic methods remain unchanged_
    - _Requirements: 1.1, 1.3, 2.1, 2.3_

  - [x] 3.2 Create execute_once() method for single execution
    - Create new execute_once() async method as main entry point
    - Establish connection at start: `await self.trader.authenticate()`
    - Execute trading logic: `await self.daily_check()`
    - Close connection at end: implement proper cleanup/close logic
    - Use try-finally to ensure connections always closed
    - Add execution completion logging
    - _Bug_Condition: Service should establish temporary connections only when needed_
    - _Expected_Behavior: Connections established, trading executed, connections closed_
    - _Preservation: daily_check() method remains completely unchanged_
    - _Requirements: 2.2, 2.4_

  - [x] 3.3 Add connection lifecycle management
    - Implement connection cleanup in DeribitConnector if not exists
    - Ensure WebSocket connections properly closed after execution
    - Add error handling for connection failures
    - Verify no resource leaks after execution
    - _Bug_Condition: Persistent connections waste resources_
    - _Expected_Behavior: All connections released after execution_
    - _Preservation: Connection authentication logic unchanged_
    - _Requirements: 1.2, 2.2, 2.4_

  - [x] 3.4 Update main() function to use single execution
    - Change `await service.run()` to `await service.execute_once()`
    - Add execution start/completion log messages
    - Ensure script exits cleanly after execution
    - _Bug_Condition: main() should not run indefinitely_
    - _Expected_Behavior: Script executes and exits_
    - _Preservation: Service initialization logic unchanged_
    - _Requirements: 2.1, 2.3, 2.5_

  - [x] 3.5 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Cron-Based Execution Model
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - Verify process does NOT exist during non-trading hours
    - Verify resources are NOT occupied when service is not running
    - Verify connections are established only during execution
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.6 Verify preservation tests still pass
    - **Property 2: Preservation** - Trading Logic and Configuration Compatibility
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - Verify sentiment analysis produces same results
    - Verify strategy selection logic unchanged
    - Verify trading execution produces same outputs
    - Verify error handling and logging unchanged
    - Verify configuration compatibility preserved
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)

- [x] 4. Create cron setup automation script

  - [x] 4.1 Create setup_cron.sh script
    - Detect Python interpreter path automatically
    - Detect script absolute path
    - Generate cron expression: `0 5 * * *` (daily at 5:00 AM)
    - Configure log redirection to file
    - Provide install command to add cron job
    - Provide uninstall command to remove cron job
    - Add validation to check if cron job already exists
    - _Expected_Behavior: Easy deployment via automated script_
    - _Requirements: 2.5_

  - [x] 4.2 Test cron setup script
    - Run install command and verify cron job added
    - Verify cron job syntax is correct
    - Run uninstall command and verify cron job removed
    - Test idempotency (running install twice should not duplicate)
    - _Expected_Behavior: Reliable cron job management_
    - _Requirements: 2.5_

- [x] 5. Update documentation for cron-based deployment

  - [x] 5.1 Update SENTIMENT_TRADING_QUICKSTART.md
    - Replace continuous service instructions with cron setup instructions
    - Document how to use setup_cron.sh script
    - Explain cron job scheduling and log file locations
    - Add troubleshooting section for cron-related issues
    - _Preservation: Keep all trading logic documentation unchanged_
    - _Requirements: 2.5_

  - [x] 5.2 Add cron monitoring guidance
    - Document how to verify cron job is running
    - Document how to check execution logs
    - Document how to manually trigger execution for testing
    - Add resource usage comparison (before/after optimization)
    - _Expected_Behavior: Clear operational guidance_
    - _Requirements: 2.4, 2.5_

- [x] 6. Checkpoint - Ensure all tests pass
  - Run all property-based tests (bug condition and preservation)
  - Verify manual execution works correctly
  - Verify cron job triggers and executes successfully
  - Verify process exits cleanly after execution
  - Verify no resource leaks or persistent connections
  - Verify all trading logic produces expected results
  - Ask the user if questions arise
