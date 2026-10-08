# Python version override notes

This workspace stores the notes for the PowerShell override used to force Python 3.14 in the current Windows user environment.

## Why the override exists

The machine-level PATH on this Windows machine still resolves an older Python install before the newer one, which causes `python` to resolve to an outdated interpreter even though Python 3.14 is installed.

To avoid this and keep the current session usable, a PowerShell profile override was added.

## Override location

The override is defined in the user PowerShell profile:

C:\Users\HP\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1

## Current override

The profile currently contains:

```powershell
function python {
    & "C:\Users\HP\AppData\Local\Programs\Python\Python314\python.exe" @args
}

function pip {
    & "C:\Users\HP\AppData\Local\Programs\Python\Python314\Scripts\pip.exe" @args
}
```

This means that in PowerShell, `python` and `pip` are intentionally redirected to the Python 3.14 installation instead of whichever version appears first in PATH.

## Important maintenance note

If a newer Python version is installed later, do not assume the override still points to the correct interpreter. Before updating or removing it, check:

1. the actual Python install path
2. the contents of the user PowerShell profile
3. whether the new version should replace the override or be added as a separate profile entry

## Recommended upgrade workflow

When a new Python release is installed:

1. Run `py -V` and `python -V` to confirm which version is active.
2. Check the PowerShell profile for the override functions.
3. Update the path in the override to the new installation directory if you still want the user-level alias.
4. If you no longer want the override, remove the `function python` and `function pip` blocks from the profile.
5. Close and reopen PowerShell before re-testing.

## Related commands

```powershell
python -V
python -c "import sys; print(sys.executable)"
py -V
```

If a new Python version is installed and the override is no longer needed, remove the profile functions and reopen PowerShell.
