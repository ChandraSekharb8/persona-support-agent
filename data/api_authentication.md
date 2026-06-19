# API Authentication Guide

## Overview
Our SaaS platform uses Bearer Token authentication for all secure API requests. Every API request must include a valid access token in the Authorization header.

## Required Header Format
Clients must pass the token using the following HTTP header:

Authorization: Bearer <access_token>

Example:

GET /api/v1/customers
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...

## Common Authentication Errors

### 401 Unauthorized
This error occurs when:
- The access token is missing
- The access token is expired
- The token format is incorrect
- The user account does not have API access enabled

Resolution steps:
1. Verify that the Authorization header is present.
2. Confirm that the token starts with "Bearer ".
3. Generate a new API token from the developer dashboard.
4. Check whether the API key belongs to an active workspace.
5. Retry the request after replacing the expired token.

### 403 Forbidden
This error occurs when the token is valid but the user does not have permission to access the requested resource.

Resolution steps:
1. Check the user's role permissions.
2. Confirm that the endpoint is available for the current subscription plan.
3. Contact an administrator to update API access permissions.

## Token Expiry
Access tokens may expire for security reasons. If the token has expired, generate a new token from:

Settings → Developer Tools → API Keys → Generate New Token

## Best Practices
- Never share API tokens publicly.
- Never commit API keys to GitHub.
- Rotate API keys every 90 days.
- Use environment variables to store API credentials.
- Revoke old or unused tokens immediately.

## Escalation Conditions
Escalate to human support if:
- The customer reports unauthorized account access.
- The customer cannot generate API keys.
- API access is blocked for a paid business account.
- Multiple valid tokens continue returning authentication errors.