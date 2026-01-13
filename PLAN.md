# DXF Batch Export - Development Plan

## Current State
The script currently exports a single component's flat pattern to DXF format. It:
- Prompts for an output folder
- Checks/creates flat pattern for the active component
- Exports with West Corte-specific settings
- Names files after the component

## Target Workflow

### Step-by-Step Process

1. **Initial Setup**
   - Prompt user for output folder (before starting any exports)
   - Access the currently open component/design
   - **Check external components**: Verify all external/referenced components are up-to-date
     - If any external components need updating, prompt user to update them first
     - Abort script if updates are needed (user must update manually)

2. **Component Type Detection**
   - **Single Component**: 
     - Check if it has sheet metal bodies
     - If yes, proceed to flat pattern check/creation
     - If no, skip (no flat pattern possible)
   
   - **Assembly**: 
     - Traverse component hierarchy recursively
     - Find all components with sheet metal bodies (only these can have flat patterns)
     - Ignore components without sheet metal bodies

3. **Flat Pattern Management**
   For each component with sheet metal:
   - Check if flat pattern exists
   - If missing: Auto-create flat pattern (using existing largest planar face heuristic)
   - If exists: **Update the flat pattern** before exporting (ensure it's current)
   - Handle errors gracefully (skip components that can't create/update flat patterns)

4. **Component Processing Logic**
   For each component with sheet metal:
   
   - **External Component** (referenced from another file):
     - Open the component in a new tab/window (bring to front)
     - Export flat pattern as DXF
     - Close the opened component tab
     - Return to original design
     - Note: External components should not be modified, so no save needed
   
   - **Local/Internal Component** (part of current design):
     - Activate the component
     - Export flat pattern as DXF
     - Continue to next component

5. **Export Execution**
   - Use existing export settings (West Corte optimized)
   - Show progress messages: "Exporting component X of Y..."
   - Handle duplicate filenames by appending numbers (`Component.dxf`, `Component_1.dxf`, `Component_2.dxf`)
   - Continue processing even if individual components fail
   - Provide summary at completion: "X of Y components exported successfully"

## Implementation Tasks

### Task Dependency Summary

```
INDEPENDENT TASKS (can be done in any order):
├─ Task 1: Folder Selection
├─ Task 3: Component Type Detection  
├─ Task 9: File Naming & Duplicate Handling
├─ Task 10: Progress Feedback
└─ Task 11: Error Handling & Reporting

FOUNDATION CHAIN (sequential dependencies):
Task 3 → Task 4 → Task 5
                └─→ Task 6

EXECUTION TASKS (depend on all foundations):
Task 7 (External) ──┐
                    ├─→ Requires: Tasks 1, 4, 5, 6, 9, 10, 11
Task 8 (Internal) ──┘

SPECIAL CASE:
Task 2: External Update Check
  └─→ Can be independent OR depend on Task 4
```

### Task Dependency Overview

**Independent Tasks** (can be developed in parallel or any order):
- Task 1: Folder Selection
- Task 3: Component Type Detection
- Task 9: File Naming & Duplicate Handling (utility function)
- Task 10: Progress Feedback (utility function)
- Task 11: Error Handling & Reporting (utility function)

**Foundation Tasks** (must complete before dependent tasks):
- Task 1 → Required by: Tasks 7, 8
- Task 3 → Required by: Task 4
- Task 4 → Required by: Tasks 2, 5, 6, 7, 8
- Task 5 → Required by: Tasks 7, 8
- Task 6 → Required by: Tasks 7, 8
- Task 9 → Required by: Tasks 7, 8
- Task 10 → Required by: Tasks 7, 8

**Execution Tasks** (depend on multiple foundation tasks):
- Task 7: External Component Handling → Depends on: Tasks 1, 4, 5, 6, 9, 10, 11
- Task 8: Internal Component Handling → Depends on: Tasks 1, 4, 5, 6, 9, 10, 11

**Special Case**:
- Task 2: External Component Update Check → Can be independent OR depends on Task 4 (if checking during traversal)

---

### Task 1: Folder Selection (Early) ⭐ INDEPENDENT
**Status**: Independent - Can be done first
**Dependencies**: None
**Required By**: Tasks 7, 8
- Move folder selection dialog to the beginning
- Store output folder path for all exports

### Task 2: External Component Update Check ⚠️ CONDITIONAL
**Status**: Can be independent OR depend on Task 4
**Option A (Independent)**: Check all external components before any traversal
**Option B (During Traversal)**: Check external components as they're discovered in Task 4
**Dependencies**: None (if Option A) OR Task 4 (if Option B)
**Required By**: None (validation step, can abort early)
- Before starting exports, check all external/referenced components
- Use API to detect if components need updating
- If updates needed: Show message box prompting user to update external components
- Abort script execution if updates are required
- Research API methods: `Component.isUpToDate` or similar

### Task 3: Component Type Detection ⭐ INDEPENDENT
**Status**: Independent - Foundation task
**Dependencies**: None
**Required By**: Task 4
- Detect if current design is single component vs assembly
- Check `design.rootComponent` vs `design.allComponents`
- Determine if component is root-level or has children

### Task 4: Hierarchy Traversal & Sheet Metal Detection 🔗 FOUNDATION
**Status**: Depends on Task 3
**Dependencies**: Task 3
**Required By**: Tasks 2 (if Option B), 5, 6, 7, 8
- Recursively traverse component hierarchy
- **Filter**: Only process components with sheet metal bodies (`body.isSheetMetal`)
- Build list of components that need flat pattern export
- Handle both direct components and occurrences
- Skip components without sheet metal (they can't have flat patterns)

### Task 5: External Component Detection 🔗 FOUNDATION
**Status**: Depends on Task 4
**Dependencies**: Task 4 (needs list of components)
**Required By**: Tasks 7, 8
- Identify external/referenced components from the component list
- Use API to check if component is external (likely `component.isReferenced` or `occurrence.isReferencedComponent`)
- Classify each component as external vs internal
- Store reference to original document for restoration

### Task 6: Flat Pattern Check & Creation 🔗 FOUNDATION
**Status**: Depends on Task 4
**Dependencies**: Task 4 (needs list of components)
**Required By**: Tasks 7, 8
- For each component, check if flat pattern exists (`component.flatPattern`)
- If missing: Auto-create using existing logic (find largest planar face)
- If exists: **Update the flat pattern** before exporting
  - Research API: `flatPattern.update()` or similar method
  - Ensure flat pattern reflects current geometry state
- Handle errors gracefully (skip components that fail)

### Task 7: External Component Handling 🎯 EXECUTION
**Status**: Depends on multiple foundation tasks
**Dependencies**: Tasks 1 (folder), 4 (component list), 5 (external detection), 6 (flat pattern), 9 (naming), 10 (progress), 11 (error handling)
**Required By**: None (end task)
- Open external component in new tab/document (bring to front)
- Activate the component in the opened document
- Export flat pattern using Task 6 logic
- Use Task 9 for filename generation
- Use Task 10 for progress updates
- Use Task 11 for error tracking
- Close the opened document (without saving - should be unchanged)
- Restore original document context
- Track original active component/document for restoration

### Task 8: Internal Component Handling 🎯 EXECUTION
**Status**: Depends on multiple foundation tasks
**Dependencies**: Tasks 1 (folder), 4 (component list), 5 (internal detection), 6 (flat pattern), 9 (naming), 10 (progress), 11 (error handling)
**Required By**: None (end task)
- Activate component (set as active)
- Export flat pattern using Task 6 logic
- Use Task 9 for filename generation
- Use Task 10 for progress updates
- Use Task 11 for error tracking
- Continue to next component
- Track original active component to restore at end

### Task 9: File Naming & Duplicate Handling ⭐ INDEPENDENT (Utility)
**Status**: Independent - Utility function
**Dependencies**: None
**Required By**: Tasks 7, 8
- Use component name only: `SubComponent.dxf` (not `Parent_SubComponent.dxf`)
- Sanitize filename (replace illegal characters like `:` with `_`)
- Track exported filenames
- If duplicate detected: Append number (`Component_1.dxf`, `Component_2.dxf`, etc.)
- Maintain counter per base filename
- Can be implemented as standalone function

### Task 10: Progress Feedback ⭐ INDEPENDENT (Utility)
**Status**: Independent - Utility function
**Dependencies**: None
**Required By**: Tasks 7, 8
- Show progress messages during batch export
- Format: "Exporting component X of Y: ComponentName"
- Update UI during processing
- Display in message box or status area
- Can be implemented as standalone function

### Task 11: Error Handling & Reporting ⭐ INDEPENDENT (Utility)
**Status**: Independent - Utility function
**Dependencies**: None
**Required By**: Tasks 7, 8 (and used throughout)
- Continue processing on individual failures
- Collect error messages per component
- Track successful vs failed exports
- Display summary at completion:
  - "X of Y components exported successfully"
  - List any failures with component names
  - Show list of exported file paths
- Can be implemented as standalone class or functions

## Recommended Implementation Order

### Phase 1: Foundation & Utilities (Can be done in parallel)
**Goal**: Build reusable components and foundational logic

1. **Task 1**: Folder Selection (Early) - Quick win, moves existing code
2. **Task 9**: File Naming & Duplicate Handling - Utility function, testable independently
3. **Task 10**: Progress Feedback - Utility function, testable independently
4. **Task 11**: Error Handling & Reporting - Utility class/functions, testable independently
5. **Task 3**: Component Type Detection - Foundation logic

### Phase 2: Component Discovery (Sequential)
**Goal**: Find and classify all components that need exporting

6. **Task 4**: Hierarchy Traversal & Sheet Metal Detection - Depends on Task 3
7. **Task 5**: External Component Detection - Depends on Task 4
8. **Task 2**: External Component Update Check - Can integrate with Task 4 or do separately

### Phase 3: Flat Pattern Management (Sequential)
**Goal**: Ensure flat patterns exist and are current

9. **Task 6**: Flat Pattern Check & Creation - Depends on Task 4

### Phase 4: Export Execution (Sequential)
**Goal**: Implement the actual export logic

10. **Task 8**: Internal Component Handling - Depends on all previous tasks
11. **Task 7**: External Component Handling - Depends on all previous tasks

### Alternative: Incremental Development Approach

**Iteration 1**: Single Component (Current functionality + improvements)
- Task 1: Folder Selection
- Task 6: Flat Pattern Check & Creation (enhance existing)
- Task 9: File Naming
- Task 11: Error Handling

**Iteration 2**: Assembly Support (Internal components only)
- Task 3: Component Type Detection
- Task 4: Hierarchy Traversal
- Task 5: External Component Detection (identify, but skip external for now)
- Task 8: Internal Component Handling
- Task 10: Progress Feedback

**Iteration 3**: External Component Support
- Task 2: External Component Update Check
- Task 7: External Component Handling

## API Research Needed

### Key API Classes to Explore
- `Design.rootComponent` - Root component access
- `Design.allComponents` - All components in design
- `Component.allOccurrences` - All component instances
- `Occurrence.isReferencedComponent` - External component detection
- `Occurrence.component` - Get component from occurrence
- `Component.isUpToDate` or similar - Check if external component needs update
- `Application.documents` - Document/tab management
- `Application.activeDocument` - Current active document
- `Document.open()` - Opening external components
- `Document.close()` - Closing documents
- `Component.activate()` - Activating internal components
- `FlatPattern.update()` or similar - Update flat pattern before export
- `BRepBody.isSheetMetal` - Check if body is sheet metal

### API Reference
- **Fusion API Reference**: https://github.com/AutodeskFusion360/FusionAPIReference
- Python reference: `Fusion_API_Python_Reference/defs/`
- HTML documentation: `Fusion_API_Documentation/files/`

## Technical Considerations

- **Document Context Switching**: 
  - Track original document before opening external components
  - Ensure proper restoration after closing external documents
  - Handle cases where external component can't be opened

- **Component Activation**: 
  - Track original active component
  - Restore original active component after batch export
  - Handle activation failures gracefully

- **Flat Pattern Updates**:
  - Research how to update existing flat patterns
  - May need to regenerate or refresh flat pattern
  - Handle cases where update fails

- **External Component Update Detection**:
  - Need to find API method to check if external component is up-to-date
  - May need to check `Occurrence` properties
  - Handle both direct references and nested references

- **Performance**:
  - Large assemblies may take time
  - Progress feedback is important for user experience
  - Consider batching operations where possible

- **Memory Management**:
  - Opening/closing multiple external components
  - Ensure proper cleanup
  - Handle cases where documents can't be closed

- **Error Recovery**:
  - What happens if external component can't be opened?
  - What if flat pattern update fails?
  - Continue processing remaining components

## File Naming Strategy

- **Base Name**: Component name only (e.g., `SubComponent.dxf`)
- **Sanitization**: Replace illegal characters (`:` → `_`)
- **Duplicates**: Append sequential numbers (`Component.dxf`, `Component_1.dxf`, `Component_2.dxf`)
- **Tracking**: Maintain dictionary of exported filenames with counters

## Testing Scenarios

1. **Single Component**: 
   - Component with sheet metal, has flat pattern
   - Component with sheet metal, no flat pattern (needs creation)
   - Component without sheet metal (should be skipped)

2. **Simple Assembly**: 
   - Multiple top-level components, all internal
   - Mix of sheet metal and non-sheet metal components
   - Components with duplicate names

3. **Nested Assembly**: 
   - Components with sub-components
   - Deep hierarchy traversal
   - Sheet metal at various levels

4. **Mixed Assembly**: 
   - Some internal, some external components
   - External components that need updating (should prompt user)
   - External components that are up-to-date

5. **External Components**: 
   - Assembly with referenced external files
   - Opening/closing external documents
   - Restoring original document context

6. **Flat Pattern Updates**: 
   - Components with outdated flat patterns
   - Components with current flat patterns
   - Components where update fails

7. **Error Cases**: 
   - Components that can't export (invalid geometry)
   - External components that can't be opened
   - Components that can't create flat patterns
   - File system errors (permissions, disk full)

8. **Duplicate Filenames**: 
   - Multiple components with same name
   - Verify numbering works correctly
   - Verify no overwrites occur
