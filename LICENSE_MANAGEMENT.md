# License Management

## Issuing licenses

1. Generate an Ed25519 key pair offline (private key never enters the app image).
2. Create a JSON license document with fields: license_id, licensee, edition, entitlements, issued_at, expires_at (optional).
3. Sign the canonical JSON (keys sorted) with the private key.
4. Attach signature as base64.
5. Deliver the file to the customer for self-hosted activation.

## Verification

- app/services/licensing.py — structure check + verify_signature_ed25519(public_key_pem).
- Embed only the public key in the deployment (LICENSE_PUBLIC_KEY_PATH).
- Expired licenses: clear messaging; do not destroy customer data.

## Editions

See COMMERCIAL_LICENSE.md: personal, professional, agency (white-label), enterprise (self-hosted).

## Online mode

Optional LICENSE_VALIDATION_URL for phone-home validation. Offline mode must work without contacting the license server.
