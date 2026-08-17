# CircuitPython Testing Guide

This directory contains unit tests for the critical systems in the CircuitPython project.

## Testing Strategy

Due to CircuitPython's limited hardware resources, we use a **hybrid testing approach**:

### 1. Host-Side Testing (Primary)
- **Where**: Run on your development machine (not on hardware)
- **How**: Mock hardware-specific CircuitPython modules
- **Benefits**: 
  - Fast execution
  - Comprehensive testing
  - No hardware resource consumption
  - Easy debugging

### 2. On-Device Testing (Optional)
- **Where**: Run on actual CircuitPython hardware
- **When**: For integration testing or hardware-specific validation
- **How**: Copy test files to device and run selectively

## Project Structure
