# FinTech Global Payment Gateway SLA & PCI-DSS 4.0 Compliance Manual
**Document ID:** FIN-SLA-PCI-2026  
**Classification:** Confidential - Partner & Regulatory Distribution Only  
**Author:** Payments Architecture & Security Compliance Board  
**Effective Date:** 2026-01-01  
**Version:** 5.1.0  

---

## 1. Scope & System Overview
This document specifies the operational standards, transaction settlement SLAs, fraud mitigation criteria, and PCI-DSS (Payment Card Industry Data Security Standard) v4.0 architecture for the Global Checkout & Clearing Engine (GCCE). The platform processes credit cards (Visa, MasterCard, Amex), Real-Time Payments (RTP), Automated Clearing House (ACH), and SEPA instant credit transfers across 42 currencies.

---

## 2. Service Level Commitments & Latency Budgets
The payment engine commits to strict operational uptimes and synchronous authorization response latency bounds.

### 2.1 Core Availability & Processing Latencies
| Transaction Type | Availability SLA | Latency Target (p95) | Latency Ceiling (p99.9) | Peak TPS Capacity |
| :--- | :--- | :--- | :--- | :--- |
| Card Authorization (3D Secure 2.3) | 99.999% (Five 9s) | < 180 ms | < 450 ms | 15,000 TPS |
| RTP / Instant Bank Transfer | 99.99% | < 220 ms | < 600 ms | 8,000 TPS |
| Batch Settlement (ACH / SEPA) | 99.95% | N/A (Cutoff: 17:00 EST) | N/A | 50,000 Tx/batch |
| Tokenization API (`/v2/tokens`) | 99.999% | < 45 ms | < 110 ms | 25,000 TPS |

### 2.2 Financial Penalties for SLA Breaches
- Monthly Availability < 99.99% and >= 99.90%: 10% invoice credit to merchant.
- Monthly Availability < 99.90% and >= 99.50%: 25% invoice credit to merchant.
- Monthly Availability < 99.50%: 50% invoice credit plus contractual right to terminate without penalty.
- Planned maintenance windows: Maximum 2 hours per calendar quarter, scheduled exclusively on Sundays between 02:00 and 04:00 UTC with 14 business days prior written notification.

---

## 3. PCI-DSS 4.0 Architectural Controls & Cardholder Data Environment (CDE)
The Cardholder Data Environment is strictly isolated from standard corporate and merchant networks via micro-segmented firewall boundaries (Fortinet Next-Gen Firewalls).

### 3.1 Primary Account Number (PAN) Tokenization Vault
1. **Zero-Knowledge Tokenization:**
   - Raw PANs (Primary Account Numbers) are never stored in plain text or reversible symmetric encryption within application databases.
   - Incoming card telemetry hits an ephemeral stateless Ingress Proxy that passes card numbers directly to a dedicated Hardware Security Module (HSM - Thales payShield 10K).
   - The HSM generates an irreversible, cryptographically secure 16-character surrogate token: format `tok_live_4a89...` preserving Luhn checksum validity and card brand BIN identification.
2. **Sensitive Authentication Data (SAD):**
   - CVV2 / CVC3 / CID security codes are strictly processed in RAM for instant authorization and permanently overwritten via secure cryptographic zero-fill memory wiping (`memset_s`) immediately post-authorization.
   - Storage of SAD post-authorization is mathematically and programmatically prohibited under PCI-DSS Requirement 3.2.

### 3.2 Key Management & Dual Control
- Master Derivation Keys (MDK) are stored inside FIPS 140-2 Level 3 certified HSM appliances.
- Key ceremonies require split-knowledge dual-control under Shamir's Secret Sharing Scheme ($k=3$ of $n=5$ key custodians).
- Working keys are rotated automatically every 90 days. Key retirement involves cryptographic erasure and audited cryptographic attestation logs.

---

## 4. Fraud Prevention, Velocity Filters & Chargeback Mitigation
The Machine Learning Risk Scorer evaluates every transaction in real-time within an 18ms inference window.

### 4.1 Real-Time Risk Rules & Action Matrix
- **Score Range 0 - 25 (Low Risk):** Automatic frictionless pass-through authorization.
- **Score Range 26 - 75 (Moderate Risk):** Dynamic step-up authentication invoking 3D Secure 2.3 biometric or SMS OTP challenge.
- **Score Range 76 - 100 (High Risk):** Immediate hard decline (`decline_code: DO_NOT_HONOR_SUSPECTED_FRAUD`).
- **Velocity Thresholds:**
  - Max 3 attempts per IP address within 10 minutes.
  - Max 2 failed CVV attempts per billing card within 24 hours triggers an automated temporary 48-hour card freeze.
  - Billing country mismatching IP geolocation by > 2 continents triggers mandatory manual review flag unless customer has marked international travel flag.

---

## 5. Settlement Timelines & Currency Conversion
- Daily settlement cutoff: 17:00 EST. Transactions authorized prior to cutoff settle $T+1$ business days for domestic USD accounts.
- Cross-border multi-currency settlement settles $T+2$ business days.
- FX Conversion Markup: Interbank midpoint exchange rate plus fixed 0.65% spread.
- Chargeback Dispute Window: Merchants are granted 14 calendar days from retrieval request notice to submit rebuttal evidence via `/v2/disputes/{id}/evidence`.
