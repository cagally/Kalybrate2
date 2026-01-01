# Authentication Setup Guide: SAML and OAuth

## Overview

Metabase supports two robust authentication methods: SAML (Security Assertion Markup Language) and OAuth. This guide will walk you through setting up and configuring these authentication systems.

## Prerequisites

- Metabase Enterprise or Pro edition
- Administrative access to your Metabase instance
- Credentials for your identity provider (IdP)

## SAML Authentication Setup

### Step 1: Configure Identity Provider

1. Obtain the following details from your SAML Identity Provider:
   - IdP SSO URL
   - IdP Entity ID
   - Public X.509 certificate

2. Prepare Metabase Service Provider (SP) Details:
   - SP Entity ID: `https://your-metabase-domain.com/saml`
   - ACS (Assertion Consumer Service) URL: `https://your-metabase-domain.com/saml/callback`

### Step 2: Metabase SAML Configuration

Navigate to **Admin** > **Authentication** > **SAML**:

1. **Enable SAML Authentication**: Toggle the switch
2. **IdP URL**: Paste your Identity Provider's SSO URL
3. **IdP Certificate**: Upload the X.509 certificate
4. **Attribute Mapping**:
   - First Name: `first_name`
   - Last Name: `last_name`
   - Email: `email`

### SAML Troubleshooting

**Common Issues:**

- **Certificate Errors**
  - Ensure certificate is valid and not expired
  - Check certificate is in correct format (Base64 encoded)

- **Login Failures**
  - Verify IdP and SP entity IDs match exactly
  - Check clock synchronization between systems

## OAuth Authentication Setup

### Step 1: Register Application

1. Create an OAuth application with your provider (Google, Azure AD, etc.)
2. Obtain:
   - Client ID
   - Client Secret
   - Authorization endpoints

### Step 2: Metabase OAuth Configuration

Navigate to **Admin** > **Authentication** > **OAuth**:

1. Select OAuth Provider (Google, Azure, etc.)
2. Enter **Client ID** and **Client Secret**
3. Configure **Authorized Redirect URIs**:
   - `https://your-metabase-domain.com/oauth/callback`

### OAuth Troubleshooting

**Common Challenges:**

- **Authorization Errors**
  - Confirm redirect URI matches exactly
  - Check client credentials
  - Verify OAuth scopes include required permissions

- **Email Mapping**
  - Ensure OAuth provider returns email address
  - Check email domain restrictions

## Security Recommendations

- Use HTTPS for all authentication endpoints
- Implement Multi-Factor Authentication (MFA)
- Regularly rotate credentials
- Limit authentication attempts

## Advanced Configuration

### Group Synchronization

Both SAML and OAuth support automatic group assignment based on user attributes.

**Configuration:**
- Map external groups to Metabase groups
- Control access based on group membership

## Debugging Authentication

1. Enable verbose logging in Metabase
2. Check system logs
3. Use browser developer tools to inspect authentication flow

## Support

If you encounter persistent issues:
- Review configuration
- Check Metabase support documentation
- Contact Metabase support with detailed logs

---

**Note:** Authentication configurations vary by organization. Always test in a staging environment first.
