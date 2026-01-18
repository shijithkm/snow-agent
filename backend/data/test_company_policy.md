# Company IT Security Policy

## Password Requirements

All employees must follow these password requirements:

- Minimum 12 characters long
- Must contain uppercase and lowercase letters
- Must contain at least one number
- Must contain at least one special character
- Passwords must be changed every 90 days
- Cannot reuse last 5 passwords

## VPN Access

To access company resources remotely:

1. Install Cisco AnyConnect VPN client
2. Use your employee credentials
3. Enable two-factor authentication
4. VPN must be active for all remote work

## Okta Access Control

### Rate Limiting

Okta implements the following rate limits:

- Authentication requests: 100 per minute per user
- API calls: 1000 requests per minute per organization
- Password reset attempts: 5 per hour per user

### Access Control Lists (ACL)

Okta ACLs control who can access applications:

- Rules are evaluated top-to-bottom
- First matching rule applies
- Default deny if no rules match
- Supports IP whitelisting and geolocation restrictions

## Incident Response

When security incidents occur:

1. Contact security@company.com immediately
2. Do not attempt to investigate on your own
3. Preserve all evidence
4. Document everything you observed
5. Follow up with Security team within 24 hours

## Data Classification

- **Public**: Can be shared externally
- **Internal**: Company employees only
- **Confidential**: Authorized personnel only
- **Restricted**: C-level and specific roles only

Always mark documents with appropriate classification.
