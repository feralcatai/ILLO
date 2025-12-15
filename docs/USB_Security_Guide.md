# 🔒 ILLO USB Security & Storage Guide

**Understanding filesystem security, data persistence, and safe USB operation**

---

## ⚠️ Critical Security Information

When ILLO is connected via USB, your computer has **direct read/write access** to the device's filesystem. This creates important security and data integrity considerations for production deployments.

---

## 🔐 USB Connection Modes

### Read-Only Mode (Production/Testing)

**When Active:**
- ILLO is connected via USB
- Computer has mounted the CIRCUITPY drive
- Filesystem is **read-only** from ILLO's perspective
- All data persistence features are automatically disabled

**Security Benefits:**
- ✅ Configuration cannot be accidentally modified during operation
- ✅ AI memory cannot be corrupted by simultaneous access
- ✅ System remains stable even if computer writes conflicting data
- ✅ Perfect for demonstrations, testing, and public displays

**Visual Indicator:**
