# Security Notes - Certificate and Key Files

## 🔒 Secured Files

The following sensitive files are **excluded from Git** and should **NEVER be committed**:

### TLS/SSL Certificates and Keys
- `cert.pem` - TLS certificate
- `key.pem` - TLS private key
- `*.pem` - All PEM files (certificates/keys)
- `*.crt`, `*.cer` - Certificate files
- `server.crt`, `server.key` - Server certificates
- `client.crt`, `client.key` - Client certificates
- `ca.crt`, `ca.key` - Certificate authority files

### Application Keys
- `keys/` - Server RSA keys (private/public)
- `sensor_keys/` - Sensor private keys
- `user_keys/` - User-specific keys
- `*.key` - All key files
- `db_encryption.key` - Database encryption key

### Environment Files
- `.env` - Environment variables
- `.env.local` - Local environment variables

## ✅ What Was Done

1. ✅ Added `*.pem`, `cert.pem`, `key.pem` to `.gitignore`
2. ✅ Removed `cert.pem` and `key.pem` from git tracking
3. ✅ Committed the security fix

## 📋 For Render Deployment

### Option 1: Environment Variables (Recommended)

Convert certificates to base64 and store as environment variables:

```bash
# Convert to base64
cert_base64=$(cat cert.pem | base64)
key_base64=$(cat key.pem | base64)
```

Add to Render environment variables:
```
TLS_CERT_B64=<base64-encoded-cert>
TLS_KEY_B64=<base64-encoded-key>
```

### Option 2: Generate New Certificates on Render

Generate new certificates specifically for Render deployment.

### Option 3: Use Render's Automatic SSL

If using custom domain, Render automatically provides SSL certificates - you may not need your own `cert.pem` and `key.pem`.

## ⚠️ Important

- **Never commit** certificate or key files to Git
- **Never share** private keys publicly
- **Always use** environment variables for secrets in cloud deployments
- **Rotate keys** if they were ever committed to a public repository

## 🔍 Verify Security

Check that sensitive files are excluded:
```bash
git status
# Should NOT show: cert.pem, key.pem, keys/, sensor_keys/, *.pem
```

---

**Your certificates and keys are now secured!** 🔒

