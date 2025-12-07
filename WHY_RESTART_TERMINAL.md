# Why Restart Terminal/IDE After Setting Environment Variables?

## What Happens When You Set Environment Variables

When you set an environment variable **permanently** (using `[System.Environment]::SetEnvironmentVariable` or Windows GUI), it's saved to Windows registry, but:

- **Existing terminals/IDEs** don't automatically see the new variable
- They only read environment variables when they **start up**
- So you need to **close and reopen** them to pick up the new variable

## What "Restart Terminal/IDE" Means

### Terminal (PowerShell/CMD):
1. **Close** your current PowerShell/CMD window
2. **Open a new** PowerShell/CMD window
3. The new window will have the updated environment variables

### IDE (VS Code, PyCharm, etc.):
1. **Close** your IDE completely
2. **Reopen** your IDE
3. The IDE will read the updated environment variables when it starts

## Why This Matters

If you set `DB_ENCRYPTION_KEY` permanently but don't restart:
- Your **current** terminal/IDE won't see it
- But **new** terminals/IDEs will see it
- Apache (when restarted) will see it (if set in app.wsgi)

## For Your Current Situation

Since you're using **Apache**, you don't need to restart your terminal/IDE because:

✅ **We already added the key to `app.wsgi`** - Apache will use it directly
✅ **Just restart Apache** - that's all you need!

The "restart terminal/IDE" instruction was for if you were running Flask **directly** (like `python app.py`), but since you're using Apache, you're all set!

## Quick Check

To verify if your terminal sees the variable (after restarting terminal):

```powershell
echo $env:DB_ENCRYPTION_KEY
```

If it shows your key, the variable is set. If it's empty, you need to restart the terminal.

But again - **for Apache, you don't need this** because we set it in `app.wsgi`!

