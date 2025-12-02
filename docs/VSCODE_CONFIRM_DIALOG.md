# VSCode Extension: Implementing confirmDialog RPC Method

This document describes how to add the `confirmDialog` RPC method to your VSCode extension to enable user confirmation before applying edits.

## Overview

When `ide_integration.require_user_confirm` is enabled in `config/feature.yaml`, the `edit_file` tool will:
1. Show the diff preview in VSCode
2. Display a confirmation dialog asking the user to approve/reject the changes
3. Only apply the changes if the user clicks "Yes"

## Implementation

### 1. Add RPC Handler in Extension

In your VSCode extension's RPC handler, add the `confirmDialog` method:

```typescript
// extension.ts or rpc-handler.ts

async function handleRpcRequest(method: string, params: any): Promise<any> {
    switch (method) {
        // ... existing methods (getActiveFile, showDiff, etc.) ...

        case 'confirmDialog':
            return await handleConfirmDialog(params);

        default:
            return { success: false, error: `Unknown method: ${method}` };
    }
}

async function handleConfirmDialog(params: { message: string, title?: string }): Promise<any> {
    const { message, title = 'Confirm' } = params;

    // Show modal dialog with Yes/No buttons
    const choice = await vscode.window.showInformationMessage(
        message,
        { modal: true },  // Make it modal (blocks until user responds)
        'Yes',
        'No'
    );

    return {
        success: true,
        confirmed: choice === 'Yes'
    };
}
```

### 2. Request Format

**Request:**
```json
{
    "jsonrpc": "2.0",
    "id": 123,
    "method": "confirmDialog",
    "params": {
        "message": "Apply changes to file.py (lines 10-15)?",
        "title": "Confirm Edit"
    }
}
```

**Response (User clicked "Yes"):**
```json
{
    "jsonrpc": "2.0",
    "id": 123,
    "result": {
        "success": true,
        "confirmed": true
    }
}
```

**Response (User clicked "No"):**
```json
{
    "jsonrpc": "2.0",
    "id": 123,
    "result": {
        "success": true,
        "confirmed": false
    }
}
```

### 3. Enable the Feature

Update `config/feature.yaml`:

```yaml
ide_integration:
  require_user_confirm:
    enabled: true  # Change from false to true
```

## User Experience Flow

### Before (without confirmation):
1. Agent decides to edit file
2. User confirms the tool call
3. ✅ Diff shown in VSCode
4. ✅ Changes applied immediately (no chance to cancel)

### After (with confirmation):
1. Agent decides to edit file
2. User confirms the tool call
3. ✅ Diff shown in VSCode
4. ✅ **Confirmation dialog appears: "Apply changes to file.py (lines 10-15)?"**
5. ✅ User clicks "Yes" → Changes applied
6. ✅ User clicks "No" → Changes cancelled, file unchanged

## Alternative: Custom Confirmation UI

Instead of a simple Yes/No dialog, you can create a richer UI:

```typescript
async function handleConfirmDialog(params: { message: string, title?: string }): Promise<any> {
    const { message, title = 'Confirm' } = params;

    // Show quick pick with more options
    const choice = await vscode.window.showQuickPick(
        [
            { label: '✅ Apply Changes', value: 'yes' },
            { label: '❌ Cancel', value: 'no' },
            { label: '👁️ Review Diff Again', value: 'review' }
        ],
        {
            placeHolder: message,
            title: title
        }
    );

    if (choice?.value === 'review') {
        // Show diff again, then ask again
        // ... (implementation depends on your extension)
    }

    return {
        success: true,
        confirmed: choice?.value === 'yes'
    };
}
```

## Testing Without Extension Modification

If you cannot modify the VSCode extension, you can still test the feature:

1. The `confirm_dialog` function has a safe fallback
2. If RPC fails, it returns `False` (rejects the edit)
3. The edit will be cancelled with error: "Edit cancelled by user in VSCode diff preview"

## Error Handling

The Python client handles errors gracefully:

- **RPC timeout (60s)**: If user doesn't respond within 60 seconds, edit is cancelled
- **RPC failure**: If extension doesn't support `confirmDialog`, edit is cancelled (safe default)
- **Mock mode (non-VSCode)**: Always returns `True` (for testing)

## Implementation Checklist

- [ ] Add `confirmDialog` case to RPC handler
- [ ] Implement `handleConfirmDialog` function
- [ ] Test with `enabled: true` in `config/feature.yaml`
- [ ] Verify dialog appears after diff preview
- [ ] Test both "Yes" and "No" responses
- [ ] Test timeout behavior (wait 60+ seconds)
- [ ] Document for users

## See Also

- `backend/tools/vscode_tools/vscode.py` - Python client implementation
- `backend/tools/filesystem_tools/edit_file.py` - Integration in edit_file tool
- `config/feature.yaml` - Feature flag configuration
