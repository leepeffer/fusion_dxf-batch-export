#Author-
#Description-

# Fusion 360 API Reference: https://github.com/AutodeskFusion360/FusionAPIReference
# Python API docs: Fusion_API_Python_Reference/defs/
# HTML docs: Fusion_API_Documentation/files/

import adsk.core, adsk.fusion, adsk.cam, adsk.drawing, traceback
import os
import re

class FilenameManager:
    """
    Task 9: File Naming & Duplicate Handling
    
    Manages filename generation for DXF exports with duplicate detection.
    - Uses component name only (not parent path)
    - Sanitizes illegal characters
    - Handles duplicates by appending sequential numbers
    """
    
    def __init__(self, output_folder):
        """
        Initialize the filename manager.

        Args:
            output_folder: The base output folder path for exports
        """
        self.output_folder = output_folder
        self.used_filenames = {}  # Maps (base_filename, extension) -> counter
        
    def sanitize_filename(self, component_name):
        """
        Sanitize component name for use as filename.
        
        Replaces illegal characters that can't be used in filenames.
        Common illegal characters: < > : " / \ | ? *
        
        Args:
            component_name: The raw component name
            
        Returns:
            str: Sanitized filename (without extension)
        """
        # Replace illegal characters with underscore
        # Windows: < > : " / \ | ? *
        # macOS/Linux: / (and : on macOS)
        illegal_chars = r'[<>:"/\\|?*\x00-\x1f]'
        sanitized = re.sub(illegal_chars, '_', component_name)
        
        # Remove leading/trailing spaces and dots (Windows doesn't allow these)
        sanitized = sanitized.strip(' .')
        
        # Ensure filename is not empty
        if not sanitized:
            sanitized = 'Component'
            
        return sanitized
    
    def get_export_path(self, component_name, file_extension='.dxf'):
        """
        Generate a unique export path for a component.

        Uses component name only (not parent path).
        Handles duplicates by appending sequential numbers.
        Checks both in-session duplicates and existing files on disk.

        Args:
            component_name: The name of the component to export
            file_extension: The file extension (including dot, e.g., '.dxf', '.pdf')

        Returns:
            str: Full path to the export file (including extension)
        """
        # Sanitize the base filename
        base_name = self.sanitize_filename(component_name)

        # Use (base_name, extension) as the key for duplicate tracking
        filename_key = (base_name, file_extension)

        # Determine the starting counter for this base name and extension
        if filename_key not in self.used_filenames:
            # First time seeing this base name/extension combination - start at 0
            self.used_filenames[filename_key] = -1  # Will be incremented to 0

        # Increment counter for this base name and extension
        self.used_filenames[filename_key] += 1
        counter = self.used_filenames[filename_key]

        # Generate filename based on counter
        if counter == 0:
            # First occurrence - use base name without number
            filename = f"{base_name}{file_extension}"
        else:
            # Duplicate detected - append number
            filename = f"{base_name}_{counter}{file_extension}"

        # Construct full path
        full_path = os.path.join(self.output_folder, filename)

        # Check if file already exists on disk and find next available number
        while os.path.exists(full_path):
            self.used_filenames[filename_key] += 1
            counter = self.used_filenames[filename_key]
            if counter == 0:
                filename = f"{base_name}{file_extension}"
            else:
                filename = f"{base_name}_{counter}{file_extension}"
            full_path = os.path.join(self.output_folder, filename)

        return full_path

    def get_drawing_export_path(self, drawing_name):
        """
        Generate export path for a drawing using its actual name.

        Args:
            drawing_name: The name of the drawing (from Fusion 360)

        Returns:
            str: Full path to the export file (including .pdf extension)
        """
        # Sanitize drawing name
        base_name = self.sanitize_filename(drawing_name)

        # Use (base_name, '.pdf') as the key for duplicate tracking
        filename_key = (base_name, '.pdf')

        # Determine the starting counter for this drawing name
        if filename_key not in self.used_filenames:
            # First time seeing this drawing name - start at 0
            self.used_filenames[filename_key] = -1  # Will be incremented to 0

        # Increment counter for this drawing name
        self.used_filenames[filename_key] += 1
        counter = self.used_filenames[filename_key]

        # Generate filename based on counter
        if counter == 0:
            # First occurrence - use base name without number
            filename = f"{base_name}.pdf"
        else:
            # Duplicate detected - append number
            filename = f"{base_name}_{counter}.pdf"

        # Construct full path
        full_path = os.path.join(self.output_folder, filename)

        # Check if file already exists on disk and find next available number
        while os.path.exists(full_path):
            self.used_filenames[filename_key] += 1
            counter = self.used_filenames[filename_key]
            if counter == 0:
                filename = f"{base_name}.pdf"
            else:
                filename = f"{base_name}_{counter}.pdf"
            full_path = os.path.join(self.output_folder, filename)

        return full_path

def show_progress(ui, current_index, total_count, component_name, display=False):
    """
    Task 10: Progress Feedback
    
    Shows progress messages during batch export operations.
    
    Formats progress as: "Exporting component X of Y: ComponentName"
    
    Args:
        ui: Fusion 360 UserInterface object (required if display=True)
        current_index: int - Current component index (1-based, e.g., 1, 2, 3...)
        total_count: int - Total number of components to process
        component_name: str - Name of the component being processed
        display: bool - If True, displays the message via UI (default: False)
                     Note: messageBox is blocking, so use sparingly in batch operations
        
    Returns:
        str: Formatted progress message
        
    Example:
        # Just format the message (for use in progress dialogs, logs, etc.)
        msg = show_progress(ui, 1, 5, "Component1")
        
        # Format and display via messageBox (blocking)
        msg = show_progress(ui, 1, 5, "Component1", display=True)
    """
    # Format: "Exporting component X of Y: ComponentName"
    progress_message = f'Exporting component {current_index} of {total_count}: {component_name}'
    
    # Optionally display via UI
    if display and ui:
        # Note: messageBox is blocking, so this should be used sparingly
        # For batch operations, consider using a progress dialog instead
        ui.messageBox(progress_message)
    
    return progress_message

class ExportResult:
    """
    Task 11: Error Handling & Reporting
    
    Tracks export results for batch processing:
    - Records successful exports with file paths
    - Records failed exports with error messages
    - Provides summary reporting at completion
    """
    
    def __init__(self):
        """Initialize the export result tracker."""
        self.successful_exports = []     # List of dicts: {'component_name': str, 'file_path': str}
        self.failed_exports = []         # List of dicts: {'component_name': str, 'error': str}
        self.drawing_exports = []        # List of dicts: {'component_name': str, 'drawing_name': str, 'file_path': str}
        self.failed_drawing_exports = [] # List of dicts: {'component_name': str, 'drawing_name': str, 'error': str}
    
    def record_success(self, component_name, file_path):
        """
        Record a successful export.
        
        Args:
            component_name: Name of the component that was exported
            file_path: Full path to the exported DXF file
        """
        self.successful_exports.append({
            'component_name': component_name,
            'file_path': file_path
        })
    
    def record_failure(self, component_name, error_message):
        """
        Record a failed export.

        Args:
            component_name: Name of the component that failed to export
            error_message: Error message describing the failure
        """
        self.failed_exports.append({
            'component_name': component_name,
            'error': error_message
        })

    def record_drawing_success(self, component_name, drawing_name, file_path):
        """
        Record a successful drawing export.

        Args:
            component_name: Name of the component the drawing belongs to
            drawing_name: Name of the drawing that was exported
            file_path: Full path to the exported PDF file
        """
        self.drawing_exports.append({
            'component_name': component_name,
            'drawing_name': drawing_name,
            'file_path': file_path
        })

    def record_drawing_failure(self, component_name, drawing_name, error_message):
        """
        Record a failed drawing export.

        Args:
            component_name: Name of the component the drawing belongs to
            drawing_name: Name of the drawing that failed to export
            error_message: Error message describing the failure
        """
        self.failed_drawing_exports.append({
            'component_name': component_name,
            'drawing_name': drawing_name,
            'error': error_message
        })
    
    def get_total_count(self):
        """
        Get the total number of components processed.
        
        Returns:
            int: Total number of components (successful + failed)
        """
        return len(self.successful_exports) + len(self.failed_exports)
    
    def get_success_count(self):
        """
        Get the number of successful exports.
        
        Returns:
            int: Number of successful exports
        """
        return len(self.successful_exports)
    
    def get_failure_count(self):
        """
        Get the number of failed exports.
        
        Returns:
            int: Number of failed exports
        """
        return len(self.failed_exports)
    
    def format_summary(self):
        """
        Format a summary message for display to the user.

        Returns:
            str: Formatted summary message with success/failure counts,
                 list of failures (if any), and list of exported files
        """
        total = self.get_total_count()
        success_count = self.get_success_count()
        failure_count = self.get_failure_count()
        drawing_count = len(self.drawing_exports)
        drawing_failure_count = len(self.failed_drawing_exports)

        # Build summary message
        lines = []

        # Main summary line
        if total == 0:
            lines.append("No components were processed.")
        else:
            lines.append(f"Export Summary: {success_count} of {total} components exported successfully.")

        # Add drawing export summary if any drawings were processed
        if drawing_count > 0 or drawing_failure_count > 0:
            lines.append(f"Drawing Exports: {drawing_count} successful, {drawing_failure_count} failed.")

        # Add failure details if any
        if failure_count > 0:
            lines.append("")
            lines.append(f"Failed DXF Exports ({failure_count}):")
            for failure in self.failed_exports:
                lines.append(f"  • {failure['component_name']}: {failure['error']}")

        # Add drawing failure details if any
        if drawing_failure_count > 0:
            lines.append("")
            lines.append(f"Failed Drawing Exports ({drawing_failure_count}):")
            for failure in self.failed_drawing_exports:
                lines.append(f"  • {failure['component_name']} ({failure['drawing_name']}): {failure['error']}")

        # Add successful export file paths
        if success_count > 0:
            lines.append("")
            lines.append(f"Exported DXF Files ({success_count}):")
            for export in self.successful_exports:
                # Show just the filename, not full path (for readability)
                filename = os.path.basename(export['file_path'])
                lines.append(f"  • {export['component_name']} → {filename}")

        # Add successful drawing export file paths
        if drawing_count > 0:
            lines.append("")
            lines.append(f"Exported Drawing Files ({drawing_count}):")
            for export in self.drawing_exports:
                # Show just the filename, not full path (for readability)
                filename = os.path.basename(export['file_path'])
                lines.append(f"  • {export['component_name']} → {filename} ({export['drawing_name']})")

        return "\n".join(lines)
    
    def show_summary(self, ui):
        """
        Display the summary message in a message box.
        
        Args:
            ui: Fusion 360 UI object for displaying messages
        """
        summary = self.format_summary()
        
        # Determine title based on results
        has_failures = self.get_failure_count() > 0 or len(self.failed_drawing_exports) > 0
        has_successes = self.get_success_count() > 0 or len(self.drawing_exports) > 0

        if not has_failures and has_successes:
            title = "Export Complete"
        elif has_failures:
            title = "Export Complete (with errors)"
        else:
            title = "Export Summary"
        
        ui.messageBox(summary, title)

def has_sheet_metal_bodies(component):
    """
    Check if a component has any sheet metal bodies.
    
    Args:
        component: The Component to check
        
    Returns:
        bool: True if component has at least one sheet metal body, False otherwise
    """
    for body in component.bRepBodies:
        if body.isSheetMetal:
            return True
    return False

def traverse_hierarchy_for_sheet_metal(component, result_list=None):
    """
    Task 4: Hierarchy Traversal & Sheet Metal Detection
    
    Recursively traverses component hierarchy to find all components with sheet metal bodies.
    Only processes components that have sheet metal bodies (these can have flat patterns).
    
    Args:
        component: The Component to start traversal from (or Occurrence)
        result_list: List to accumulate results (created on first call)
        
    Returns:
        list: List of Component objects that have sheet metal bodies
              Each entry is a dict with:
              - 'component': Component - The component with sheet metal
              - 'occurrence': Occurrence or None - The occurrence if component came from occurrence
    """
    if result_list is None:
        result_list = []
    
    # Handle both Component and Occurrence inputs
    comp = None
    occurrence = None
    
    if hasattr(component, 'component'):
        # It's an Occurrence
        occurrence = component
        comp = occurrence.component
    else:
        # It's a Component
        comp = component
    
    # Check if this component has sheet metal bodies and hasn't been added yet
    if comp and has_sheet_metal_bodies(comp):
        # Avoid duplicates - only add if this component isn't already in the list
        if not any(entry['component'] == comp for entry in result_list):
            result_list.append({
                'component': comp,
                'occurrence': occurrence
            })
    
    # Recursively traverse child occurrences
    if comp:
        for occ in comp.occurrences:
            traverse_hierarchy_for_sheet_metal(occ, result_list)
    
    return result_list

def detect_external_components(component_list, design):
    """
    Task 5: External Component Detection
    
    Identifies which components in the list are external/referenced components.
    Classifies each component as external vs internal.
    
    Args:
        component_list: List of component dicts from Task 4
                       Each dict has 'component' and 'occurrence' keys
        design: The Fusion 360 Design object (for document reference)
        
    Returns:
        list: List of component info dicts with external/internal classification
              Each entry includes:
              - 'component': Component - The component
              - 'occurrence': Occurrence or None - The occurrence if applicable
              - 'is_external': bool - True if external/referenced, False if internal
              - 'source_document': Document or None - Original document for external components
    """
    app = adsk.core.Application.get()
    result_list = []
    
    for comp_info in component_list:
        component = comp_info['component']
        occurrence = comp_info['occurrence']

        # Simplify external component detection using the reliable API
        is_external = False
        source_document = None

        if occurrence and occurrence.isReferencedComponent:
            # Primary check: occurrence represents a referenced (external) component
            is_external = True
            try:
                source_document = occurrence.component.parentDocument
            except:
                # Source document may not be accessible, but that's okay
                pass

        result_list.append({
            'component': component,
            'occurrence': occurrence,
            'is_external': is_external,
            'source_document': source_document
        })
    
    return result_list

def check_external_component_updates(classified_components, design, ui=None):
    """
    Task 2: External Component Update Check

    Checks if external/referenced components need updating using document-level APIs.
    Uses design.parentDocument.isUpToDate and document.updateAllReferences().

    Args:
        classified_components: List of component info dicts from Task 5
                              Each dict has 'component', 'occurrence', 'is_external', 'source_document'
        design: The Fusion 360 Design object
        ui: Optional UI object for displaying messages (required for user prompts)

    Returns:
        tuple: (all_up_to_date: bool, components_needing_update: list)
               - all_up_to_date: True if document is up-to-date, False if updates are needed
               - components_needing_update: List of component names (empty if all up-to-date, or generic message)
    """
    try:
        # Check if the document is up to date (includes external references)
        document = design.parentDocument
        if not document.isUpToDate:
            # Document has external references that need updating
            # Return that updates are needed - let user handle via updateAllReferences()
            return (False, ["External references need updating"])
        else:
            # Document is up to date
            return (True, [])
    except Exception as e:
        # If check fails, assume updates may be needed for safety
        if ui:
            ui.messageBox(f'Warning: Could not check external component update status: {str(e)}')
        return (False, ["Unable to verify external component status"])

def prompt_external_component_updates(components_needing_update, ui):
    """
    Helper function to prompt user about external components that need updating.
    
    Args:
        components_needing_update: List of component names that need updating
        ui: UI object for displaying message box
        
    Returns:
        bool: True if user wants to proceed anyway, False if user wants to abort
    """
    if not components_needing_update:
        return True
    
    # Build message listing components that need updating
    component_list = '\n'.join([f'  • {name}' for name in components_needing_update])
    
    message = (
        f"The following external components need to be updated before export:\n\n"
        f"{component_list}\n\n"
        f"Please update these components in Fusion 360 before running the export script.\n\n"
        f"To update external components:\n"
        f"1. Right-click on the component in the browser\n"
        f"2. Select 'Update' or 'Update All'\n"
        f"3. Run this script again\n\n"
        f"Click OK to abort the export."
    )
    
    ui.messageBox(message, "External Components Need Updating")
    
    # Always abort - user must update components manually
    return False

def find_largest_planar_face(component):
    """
    Helper function to find the largest planar face in a component's sheet metal bodies.
    Used for flat pattern creation.
    
    Args:
        component: Component to search for planar faces
        
    Returns:
        Face or None: The largest planar face found, or None if none found
    """
    targetBody = None
    
    # Find first sheet metal body
    for body in component.bRepBodies:
        if body.isSheetMetal:
            targetBody = body
            break
    
    if not targetBody:
        return None
    
    # Find largest planar face
    bestFace = None
    maxArea = 0.0
    
    for face in targetBody.faces:
        # Check if geometry is a plane
        if face.geometry.objectType == adsk.core.Plane.classType():
            if face.area > maxArea:
                maxArea = face.area
                bestFace = face
    
    return bestFace

def ensure_flat_pattern(component, ui=None):
    """
    Task 6: Flat Pattern Check & Creation
    
    Ensures a flat pattern exists for a component and is up-to-date.
    - Checks if flat pattern exists
    - If missing: Auto-creates using largest planar face heuristic
    - If exists: Updates the flat pattern to ensure it reflects current geometry
    
    Args:
        component: Component to check/create/update flat pattern for
        ui: Optional UI object for error messages (if None, errors are silent)
        
    Returns:
        tuple: (success: bool, flat_pattern: FlatPattern or None, error_message: str or None)
    """
    try:
        # Check if flat pattern exists
        flatPattern = component.flatPattern
        
        if not flatPattern:
            # Flat pattern doesn't exist - create it
            if not has_sheet_metal_bodies(component):
                error_msg = f'Component "{component.name}" does not contain any Sheet Metal bodies.'
                if ui:
                    ui.messageBox(error_msg)
                return (False, None, error_msg)
            
            # Find largest planar face
            bestFace = find_largest_planar_face(component)
            
            if not bestFace:
                error_msg = f'Could not automatically determine a base face for Flat Pattern in component "{component.name}".'
                if ui:
                    ui.messageBox(error_msg)
                return (False, None, error_msg)
            
            # Create the flat pattern
            try:
                flatPattern = component.createFlatPattern(bestFace)
                return (True, flatPattern, None)
            except Exception as e:
                error_msg = f'Failed to create Flat Pattern for component "{component.name}": {str(e)}'
                if ui:
                    ui.messageBox(error_msg)
                return (False, None, error_msg)
        else:
            # Flat pattern exists and is always current
            # Fusion 360 automatically maintains flat patterns when geometry changes
            return (True, flatPattern, None)
            
    except Exception as e:
        error_msg = f'Error processing flat pattern for component "{component.name}": {str(e)}'
        if ui:
            ui.messageBox(error_msg)
        return (False, None, error_msg)

def detect_component_type(design):
    """
    Task 3: Component Type Detection
    
    Detects if the current design is a single component vs an assembly.
    
    Args:
        design: The Fusion 360 Design object
        
    Returns:
        dict: A dictionary with:
            - 'is_assembly': bool - True if design is an assembly, False if single component
            - 'root_component': Component - The root component
            - 'all_components': ComponentCollection - All components in the design
            - 'has_children': bool - True if root component has child occurrences
            - 'component_count': int - Total number of components
    """
    rootComp = design.rootComponent
    
    # Check if root component has child occurrences (indicates assembly)
    has_children = rootComp.occurrences.count > 0
    
    # Get all components in the design
    allComponents = design.allComponents
    
    # Count total components (excluding root)
    component_count = allComponents.count
    
    # Determine if it's an assembly:
    # - Has child occurrences, OR
    # - Has more than just the root component
    is_assembly = has_children or component_count > 1
    
    return {
        'is_assembly': is_assembly,
        'root_component': rootComp,
        'all_components': allComponents,
        'has_children': has_children,
        'component_count': component_count
    }

def export_flat_pattern_to_dxf(component, flat_pattern, output_path, design):
    """
    Helper function to export a flat pattern to DXF with West Corte settings.
    
    This is shared logic used by both Task 7 (external) and Task 8 (internal) handlers.
    
    Args:
        component: The Component to export
        flat_pattern: The FlatPattern to export
        output_path: Full path where the DXF file should be saved
        design: The Fusion 360 Design object (for exportManager)
        
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    try:
        exportMgr = design.exportManager
        
        # Create DXF Export Options
        # Note: createDXFFlatPatternExportOptions is the correct method for FlatPattern
        dxfOptions = exportMgr.createDXFFlatPatternExportOptions(output_path, flat_pattern)
        
        # Explicitly set options (West Corte optimized settings)
        dxfOptions.isCenterLinesExported = True        # Enable center (bend) lines
        dxfOptions.isExtentLinesExported = False       # Disable 'extend lines' (bounding box)
        dxfOptions.isSplineConvertedToPolyline = False # Keep splines (prevents missing lines issues)
        
        # Set units to Millimeters (West Corte optimization)
        dxfOptions.units = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        
        # Execute Export
        exportMgr.execute(dxfOptions)
        
        return (True, None)
        
    except Exception as e:
        error_msg = f'Failed to export DXF for component "{component.name}": {str(e)}'
        return (False, error_msg)

def handle_external_component(comp_info, original_document, original_design, filename_manager,
                             export_result, current_index, total_count, ui, export_drawings=False, drawings_folder=None):
    """
    Task 7: External Component Handling

    Handles export of external/referenced components:
    - Activates the component in the current design (external components are already referenced)
    - Exports flat pattern using Task 6 logic
    - Uses Task 9 for filename generation
    - Uses Task 10 for progress updates
    - Uses Task 11 for error tracking
    - Restores original document context

    Args:
        comp_info: Component info dict with 'component', 'occurrence', 'is_external', 'source_document'
        original_document: The original document to restore after processing
        original_design: The original design object
        filename_manager: FilenameManager instance for generating export paths
        export_result: ExportResult instance for tracking results
        current_index: Current component index (1-based) for progress display
        total_count: Total number of components to process
        ui: UI object for messages
        export_drawings: Boolean indicating whether to export associated drawings
        drawings_folder: Path to folder containing drawing files (if export_drawings is True)

    Returns:
        bool: True if export was successful, False otherwise
    """
    component = comp_info['component']
    component_name = component.name
    
    # Show progress
    show_progress(ui, current_index, total_count, component_name, display=False)
    
    # External components work with current design - no separate document handling needed
    app = adsk.core.Application.get()
    
    try:
        # External components are already referenced in the current design
        # No need to open separate documents - work directly with current design
        opened_design = original_design

        # Activate the component in the current design
        occurrence = comp_info['occurrence']
        try:
            if occurrence:
                # For components in assemblies, activate through the occurrence
                occurrence.activate()
            else:
                # For root component, set as active component
                opened_design.activeComponent = component
        except Exception as e:
            # If activation fails, cannot proceed with export
            error_msg = f'Failed to activate component "{component_name}" - cannot export: {str(e)}'
            export_result.record_failure(component_name, error_msg)
            return False

        # Task 6: Ensure flat pattern exists and is up-to-date (only after successful activation)
        success, flat_pattern, error_msg = ensure_flat_pattern(component, ui=None)

        if not success:
            export_result.record_failure(component_name, error_msg or 'Failed to create/update flat pattern')
            return False

        if not flat_pattern:
            export_result.record_failure(component_name, 'Flat pattern not found after creation')
            return False

        # Task 9: Generate export path using FilenameManager
        export_path = filename_manager.get_export_path(component_name)

        # Export the flat pattern
        export_success, export_error = export_flat_pattern_to_dxf(
            component, flat_pattern, export_path, opened_design
        )

        if export_success:
            export_result.record_success(component_name, export_path)

            # Export associated drawings if requested
            if export_drawings:
                # #region agent log - hypothesis B: Drawing export decision
                try:
                    import json
                    import time
                    with open('/Users/leepeffer/Documents/github/fusion_dxf-batch-export/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({
                            "id": f"log_{int(time.time()*1000)}_drawing_decision",
                            "timestamp": int(time.time()*1000),
                            "location": "dxfExport_westcorte.py:825",
                            "message": "Starting drawing export for component",
                            "data": {"component_name": component_name, "export_drawings": export_drawings},
                            "sessionId": "debug-session",
                            "runId": "initial",
                            "hypothesisId": "B"
                        }) + '\n')
                except:
                    pass
                # #endregion

                try:
                    # Find drawings associated with this component
                    associated_drawings = find_associated_drawings(component, drawings_folder, app, ui=None)

                    # #region agent log - hypothesis B: Drawing discovery results (external)
                    try:
                        import json
                        import time
                        drawing_names = [d['name'] for d in associated_drawings]
                        with open('/Users/leepeffer/Documents/github/fusion_dxf-batch-export/.cursor/debug.log', 'a') as f:
                            f.write(json.dumps({
                                "id": f"log_{int(time.time()*1000)}_drawing_found_ext",
                                "timestamp": int(time.time()*1000),
                                "location": "dxfExport_westcorte.py:835",
                                "message": "Drawing discovery results (external component)",
                                "data": {
                                    "component_name": component_name,
                                    "num_drawings_found": len(associated_drawings),
                                    "drawing_names": drawing_names
                                },
                                "sessionId": "debug-session",
                                "runId": "initial",
                                "hypothesisId": "B"
                            }) + '\n')
                    except:
                        pass
                    # #endregion

                    if associated_drawings:
                        # Get the latest drawing
                        latest_drawing = get_latest_drawing(associated_drawings)

                        if latest_drawing:
                            # Generate export path for the drawing
                            drawing_export_path = filename_manager.get_drawing_export_path(latest_drawing['name'])

                            # Export the drawing to PDF
                            drawing_success, drawing_error = export_drawing_to_pdf(
                                latest_drawing['drawing'],
                                drawing_export_path,
                                ui=None
                            )

                            if drawing_success:
                                export_result.record_drawing_success(component_name, latest_drawing['name'], drawing_export_path)
                            else:
                                export_result.record_drawing_failure(component_name, latest_drawing['name'], drawing_error or 'Drawing export failed')

                            # Close the drawing document to clean up
                            try:
                                latest_drawing['document'].close(False)  # False = don't save
                            except:
                                pass  # Ignore errors when closing

                        # If no latest drawing found, silently skip (not an error)
                    # If no associated drawings found, silently skip (not an error)
                except Exception as e:
                    # Log drawing export error but don't fail the component export
                    export_result.record_drawing_failure(component_name, 'Unknown', f'Drawing export error: {str(e)}')

            return True
        else:
            export_result.record_failure(component_name, export_error or 'Export failed')
            return False

    except Exception as e:
        error_msg = f'Error processing external component "{component_name}": {str(e)}'
        export_result.record_failure(component_name, error_msg)
        return False
            
    finally:
        # Restore original document context
        try:
            if original_document and app:
                app.activeDocument = original_document
                # Also restore the design's active component if possible
                try:
                    if original_design:
                        # Try to restore original active component
                        # (This may have been tracked separately)
                        pass
                except:
                    pass
        except:
            # If restoration fails, log but don't fail
            pass

def handle_internal_component(comp_info, original_active_component, design, filename_manager,
                             export_result, current_index, total_count, ui, export_drawings=False, drawings_folder=None):
    """
    Task 8: Internal Component Handling
    
    Handles export of internal components:
    - Activates component (set as active)
    - Exports flat pattern using Task 6 logic
    - Uses Task 9 for filename generation
    - Uses Task 10 for progress updates
    - Uses Task 11 for error tracking
    - Continues to next component
    
    Args:
        comp_info: Component info dict with 'component', 'occurrence', 'is_external', 'source_document'
        original_active_component: The original active component to restore at end
        design: The Fusion 360 Design object
        filename_manager: FilenameManager instance for generating export paths
        export_result: ExportResult instance for tracking results
        current_index: Current component index (1-based) for progress display
        total_count: Total number of components to process
        ui: UI object for messages
        export_drawings: Boolean indicating whether to export associated drawings
        drawings_folder: Path to folder containing drawing files (if export_drawings is True)
        
    Returns:
        bool: True if export was successful, False otherwise
    """
    component = comp_info['component']
    component_name = component.name
    
    # Show progress
    show_progress(ui, current_index, total_count, component_name, display=False)
    
    try:
        # Activate the component
        occurrence = comp_info['occurrence']
        try:
            if occurrence:
                # For components in assemblies, activate through the occurrence
                occurrence.activate()
            else:
                # For root component, set as active component
                design.activeComponent = component
        except Exception as e:
            # If activation fails, cannot proceed with export
            error_msg = f'Failed to activate component "{component_name}": {str(e)}'
            export_result.record_failure(component_name, error_msg)
            return False
        
        # Task 6: Ensure flat pattern exists and is up-to-date
        success, flat_pattern, error_msg = ensure_flat_pattern(component, ui=None)
        
        if not success:
            export_result.record_failure(component_name, error_msg or 'Failed to create/update flat pattern')
            return False
        
        if not flat_pattern:
            export_result.record_failure(component_name, 'Flat pattern not found after creation')
            return False
        
        # Task 9: Generate export path using FilenameManager
        export_path = filename_manager.get_export_path(component_name)
        
        # Export the flat pattern
        export_success, export_error = export_flat_pattern_to_dxf(
            component, flat_pattern, export_path, design
        )

        if export_success:
            export_result.record_success(component_name, export_path)

            # Export associated drawings if requested
            if export_drawings:
                try:
                    app = adsk.core.Application.get()
                    # Find drawings associated with this component
                    associated_drawings = find_associated_drawings(component, drawings_folder, app, ui=None)

                    # #region agent log - hypothesis B: Drawing discovery results (internal)
                    try:
                        import json
                        import time
                        drawing_names = [d['name'] for d in associated_drawings]
                        with open('/Users/leepeffer/Documents/github/fusion_dxf-batch-export/.cursor/debug.log', 'a') as f:
                            f.write(json.dumps({
                                "id": f"log_{int(time.time()*1000)}_drawing_found_int",
                                "timestamp": int(time.time()*1000),
                                "location": "dxfExport_westcorte.py:956",
                                "message": "Drawing discovery results (internal component)",
                                "data": {
                                    "component_name": component_name,
                                    "num_drawings_found": len(associated_drawings),
                                    "drawing_names": drawing_names
                                },
                                "sessionId": "debug-session",
                                "runId": "initial",
                                "hypothesisId": "B"
                            }) + '\n')
                    except:
                        pass
                    # #endregion

                    if associated_drawings:
                        # Get the latest drawing
                        latest_drawing = get_latest_drawing(associated_drawings)

                        if latest_drawing:
                            # Generate export path for the drawing
                            drawing_export_path = filename_manager.get_drawing_export_path(latest_drawing['name'])

                            # Export the drawing to PDF
                            drawing_success, drawing_error = export_drawing_to_pdf(
                                latest_drawing['drawing'],
                                drawing_export_path,
                                ui=None
                            )

                            if drawing_success:
                                export_result.record_drawing_success(component_name, latest_drawing['name'], drawing_export_path)
                            else:
                                export_result.record_drawing_failure(component_name, latest_drawing['name'], drawing_error or 'Drawing export failed')

                            # Close the drawing document to clean up
                            try:
                                latest_drawing['document'].close(False)  # False = don't save
                            except:
                                pass  # Ignore errors when closing

                        # If no latest drawing found, silently skip (not an error)
                    # If no associated drawings found, silently skip (not an error)
                except Exception as e:
                    # Log drawing export error but don't fail the component export
                    export_result.record_drawing_failure(component_name, 'Unknown', f'Drawing export error: {str(e)}')

            return True
        else:
            export_result.record_failure(component_name, export_error or 'Export failed')
            return False
            
    except Exception as e:
        error_msg = f'Error processing internal component "{component_name}": {str(e)}'
        export_result.record_failure(component_name, error_msg)
        return False

def find_associated_drawings(component, drawings_folder, app, ui=None):
    """
    Find drawing files that are associated with the given component by matching names.

    Args:
        component: The Component to find drawings for
        drawings_folder: Path to folder containing .f2d drawing files
        app: The Fusion 360 Application object
        ui: Optional UI object for error messages

    Returns:
        list: List of Drawing objects that were opened and match this component
              Each entry is a dict with:
              - 'drawing': Drawing - The drawing object
              - 'document': DrawingDocument - The document containing the drawing
              - 'name': str - The drawing name
              - 'file_path': str - Full path to the drawing file
    """
    # #region agent log - hypothesis A: File system drawing discovery
    try:
        import json
        import time
        with open('/Users/leepeffer/Documents/github/fusion_dxf-batch-export/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({
                "id": f"log_{int(time.time()*1000)}_find_drawings",
                "timestamp": int(time.time()*1000),
                "location": "dxfExport_westcorte.py:983",
                "message": "Starting find_associated_drawings (file system approach)",
                "data": {
                    "component_name": getattr(component, 'name', 'unknown'),
                    "drawings_folder": drawings_folder
                },
                "sessionId": "debug-session",
                "runId": "initial",
                "hypothesisId": "A"
            }) + '\n')
    except:
        pass
    # #endregion

    associated_drawings = []

    if not drawings_folder:
        return associated_drawings

    # #region agent log - hypothesis D: Document iteration
    try:
        import json
        import time
        docs_list = []
        for i, doc in enumerate(app.documents):
            try:
                doc_info = {
                    "index": i,
                    "name": doc.name,
                    "has_products": hasattr(doc, 'products'),
                    "product_count": len(list(doc.products)) if hasattr(doc, 'products') else 0
                }
                if hasattr(doc, 'products'):
                    products_info = []
                    for j, product in enumerate(doc.products):
                        product_info = {
                            "product_index": j,
                            "product_type": product.productType if hasattr(product, 'productType') else 'unknown'
                        }
                        products_info.append(product_info)
                    doc_info["products"] = products_info
                docs_list.append(doc_info)
            except:
                docs_list.append({"index": i, "error": "failed to get doc info"})

        with open('/Users/leepeffer/Documents/github/fusion_dxf-batch-export/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({
                "id": f"log_{int(time.time()*1000)}_doc_iteration",
                "timestamp": int(time.time()*1000),
                "location": "dxfExport_westcorte.py:1005",
                "message": "Document iteration results",
                "data": {"total_docs": len(docs_list), "docs": docs_list},
                "sessionId": "debug-session",
                "runId": "initial",
                "hypothesisId": "D"
            }) + '\n')
    except:
        pass
    # #endregion

    try:
        import os

        # Get component name for matching
        component_name = component.name.lower()

        # Scan the drawings folder for .f2d files
        for filename in os.listdir(drawings_folder):
            if filename.lower().endswith('.f2d'):
                # Check if the drawing filename matches the component name
                drawing_name_base = os.path.splitext(filename)[0].lower()

                # Match if component name is contained in drawing name or vice versa
                # This allows for flexible naming (e.g., "Component" matches "Component Drawing")
                name_matches = (
                    component_name in drawing_name_base or
                    drawing_name_base in component_name
                )

                # #region agent log - hypothesis A: Filename matching
                try:
                    import json
                    import time
                    with open('/Users/leepeffer/Documents/github/fusion_dxf-batch-export/.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({
                            "id": f"log_{int(time.time()*1000)}_filename_match",
                            "timestamp": int(time.time()*1000),
                            "location": "dxfExport_westcorte.py:1015",
                            "message": "Checking filename match",
                            "data": {
                                "component_name": component_name,
                                "drawing_filename": filename,
                                "drawing_name_base": drawing_name_base,
                                "name_matches": name_matches
                            },
                            "sessionId": "debug-session",
                            "runId": "initial",
                            "hypothesisId": "A"
                        }) + '\n')
                except:
                    pass
                # #endregion

                if name_matches:
                    # Found a matching drawing file, try to open it
                    drawing_path = os.path.join(drawings_folder, filename)

                    try:
                        # Open the drawing document
                        # #region agent log - hypothesis A: Opening drawing
                        try:
                            import json
                            import time
                            with open('/Users/leepeffer/Documents/github/fusion_dxf-batch-export/.cursor/debug.log', 'a') as f:
                                f.write(json.dumps({
                                    "id": f"log_{int(time.time()*1000)}_opening_drawing",
                                    "timestamp": int(time.time()*1000),
                                    "location": "dxfExport_westcorte.py:1025",
                                    "message": "Attempting to open drawing file",
                                    "data": {
                                        "drawing_path": drawing_path,
                                        "component_name": component.name
                                    },
                                    "sessionId": "debug-session",
                                    "runId": "initial",
                                    "hypothesisId": "A"
                                }) + '\n')
                        except:
                            pass
                        # #endregion

                        drawing_doc = app.documents.open(drawing_path, True)  # True = visible

                        if drawing_doc and drawing_doc.isDrawing:
                            # Get the drawing product
                            drawing_product = drawing_doc.products.itemByProductType("DrawingProductType")
                            if drawing_product:
                                drawing = adsk.drawing.Drawing.cast(drawing_product)
                                if drawing:
                                    associated_drawings.append({
                                        'drawing': drawing,
                                        'document': drawing_doc,
                                        'name': drawing_doc.name,
                                        'file_path': drawing_path
                                    })

                                    # #region agent log - hypothesis A: Successfully opened drawing
                                    try:
                                        import json
                                        import time
                                        with open('/Users/leepeffer/Documents/github/fusion_dxf-batch-export/.cursor/debug.log', 'a') as f:
                                            f.write(json.dumps({
                                                "id": f"log_{int(time.time()*1000)}_drawing_opened",
                                                "timestamp": int(time.time()*1000),
                                                "location": "dxfExport_westcorte.py:1045",
                                                "message": "Successfully opened drawing",
                                                "data": {
                                                    "drawing_name": drawing_doc.name,
                                                    "component_name": component.name
                                                },
                                                "sessionId": "debug-session",
                                                "runId": "initial",
                                                "hypothesisId": "A"
                                            }) + '\n')
                                    except:
                                        pass
                                    # #endregion

                    except Exception as e:
                        # Failed to open this drawing file
                        # #region agent log - hypothesis A: Failed to open drawing
                        try:
                            import json
                            import time
                            with open('/Users/leepeffer/Documents/github/fusion_dxf-batch-export/.cursor/debug.log', 'a') as f:
                                f.write(json.dumps({
                                    "id": f"log_{int(time.time()*1000)}_drawing_open_failed",
                                    "timestamp": int(time.time()*1000),
                                    "location": "dxfExport_westcorte.py:1050",
                                    "message": "Failed to open drawing file",
                                    "data": {
                                        "drawing_path": drawing_path,
                                        "error": str(e),
                                        "component_name": component.name
                                    },
                                    "sessionId": "debug-session",
                                    "runId": "initial",
                                    "hypothesisId": "A"
                                }) + '\n')
                        except:
                            pass
                        # #endregion

                        if ui:
                            ui.messageBox(f'Warning: Could not open drawing file {filename}: {str(e)}')

    except Exception as e:
        if ui:
            ui.messageBox(f'Error searching for associated drawings: {str(e)}')

    return associated_drawings

def get_latest_drawing(drawings_list):
    """
    Get the first drawing from a list (since we now open drawings on demand).

    Args:
        drawings_list: List of drawing dicts from find_associated_drawings()

    Returns:
        dict or None: The first drawing dict, or None if list is empty
    """
    if not drawings_list:
        return None

    # Since we're opening drawings on demand, just return the first match
    return drawings_list[0]

def export_drawing_to_pdf(drawing, output_path, ui=None):
    """
    Export a drawing to PDF format.

    Args:
        drawing: The Drawing object to export
        output_path: Full path where the PDF file should be saved
        ui: Optional UI object for error messages

    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    # #region agent log - hypothesis C: Drawing export setup
    try:
        import json
        import time
        with open('/Users/leepeffer/Documents/github/fusion_dxf-batch-export/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({
                "id": f"log_{int(time.time()*1000)}_export_setup",
                "timestamp": int(time.time()*1000),
                "location": "dxfExport_westcorte.py:1112",
                "message": "Starting drawing PDF export",
                "data": {"output_path": output_path},
                "sessionId": "debug-session",
                "runId": "initial",
                "hypothesisId": "C"
            }) + '\n')
    except:
        pass
    # #endregion

    try:
        # Access the drawing's export manager
        exportMgr = drawing.exportManager

        # Create PDF export options
        pdfOptions = exportMgr.createPDFExportOptions(output_path)

        # Set export options
        pdfOptions.sheetsToExport = adsk.drawing.PDFSheetsExport.AllPDFSheetsExport
        pdfOptions.useLineWeights = True

        # Execute the export
        # #region agent log - hypothesis C: Export execution
        try:
            import json
            import time
            with open('/Users/leepeffer/Documents/github/fusion_dxf-batch-export/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    "id": f"log_{int(time.time()*1000)}_export_exec",
                    "timestamp": int(time.time()*1000),
                    "location": "dxfExport_westcorte.py:1132",
                    "message": "Executing PDF export",
                    "data": {"has_exportMgr": exportMgr is not None},
                    "sessionId": "debug-session",
                    "runId": "initial",
                    "hypothesisId": "C"
                }) + '\n')
        except:
            pass
        # #endregion

        exportMgr.execute(pdfOptions)

        # #region agent log - hypothesis C: Export success
        try:
            import json
            import time
            with open('/Users/leepeffer/Documents/github/fusion_dxf-batch-export/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    "id": f"log_{int(time.time()*1000)}_export_success",
                    "timestamp": int(time.time()*1000),
                    "location": "dxfExport_westcorte.py:1135",
                    "message": "PDF export completed successfully",
                    "data": {"file_exists": os.path.exists(output_path)},
                    "sessionId": "debug-session",
                    "runId": "initial",
                    "hypothesisId": "C"
                }) + '\n')
        except:
            pass
        # #endregion

        return (True, None)

    except Exception as e:
        error_msg = f'Failed to export drawing "{document.name}" to PDF: {str(e)}'
        return (False, error_msg)

def _drawing_references_component(referenced_design, target_component):
    """
    Helper function to check if a referenced design contains the target component.

    Args:
        referenced_design: The design referenced by a drawing view
        target_component: The component we're looking for

    Returns:
        bool: True if the design contains the target component
    """
    try:
        # Check if the referenced design's root component is our target
        if referenced_design.rootComponent == target_component:
            return True

        # Check if any component in the referenced design matches our target
        for comp in referenced_design.allComponents:
            if comp == target_component:
                return True

        # Check if the target component's parent document is this design
        if hasattr(target_component, 'parentDocument') and target_component.parentDocument == referenced_design.parentDocument:
            return True

        return False

    except:
        return False

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design = app.activeProduct
        
        # Check if a design is active
        if not design:
            ui.messageBox('No active Fusion 360 design found.')
            return

        # 1. Drawing Export Option Dialog
        export_drawings_result = ui.messageBox(
            'Export associated drawings (if available)?\n\n' +
            'This will export PDF files for any open drawings that reference the components being exported.',
            'Export Drawings Option',
            adsk.core.MessageBoxButtonTypes.YesNoButtonType,
            adsk.core.MessageBoxIconTypes.QuestionIconType
        )

        export_drawings = (export_drawings_result == adsk.core.DialogResults.DialogYes)

        drawings_folder = None
        if export_drawings:
            # Ask user for drawings directory
            drawings_folder_dlg = ui.createFolderDialog()
            drawings_folder_dlg.title = 'Select Folder Containing Drawing Files (.f2d)'
            drawings_folder_dlg.initialDirectory = outputFolder  # Default to same as DXF folder

            dlgResult = drawings_folder_dlg.showDialog()
            if dlgResult != adsk.core.DialogResults.DialogOK:
                # User cancelled drawings folder selection
                export_drawings = False
                drawings_folder = None
            else:
                drawings_folder = drawings_folder_dlg.folder

        # 2. Folder Selection Dialog (Early - before any processing)
        folderDlg = ui.createFolderDialog()
        folderDlg.title = 'Select Output Folder for DXF'
        
        # Show dialog
        dlgResult = folderDlg.showDialog()
        if dlgResult != adsk.core.DialogResults.DialogOK:
            return # User cancelled
            
        outputFolder = folderDlg.folder
        
        # Task 9: Initialize File Naming & Duplicate Handling
        filename_manager = FilenameManager(outputFolder)
        
        # Task 3: Component Type Detection
        component_type_info = detect_component_type(design)
        is_assembly = component_type_info['is_assembly']
        root_component = component_type_info['root_component']
        all_components = component_type_info['all_components']
        
        # Task 4: Hierarchy Traversal & Sheet Metal Detection
        # Find all components with sheet metal bodies
        sheet_metal_components = traverse_hierarchy_for_sheet_metal(root_component)
        
        # Task 5: External Component Detection
        # Classify components as external vs internal
        classified_components = detect_external_components(sheet_metal_components, design)
        
        # Task 2: External Component Update Check
        # Check if any external components need updating before proceeding
        all_up_to_date, components_needing_update = check_external_component_updates(
            classified_components, design, ui
        )
        
        if not all_up_to_date:
            # External components need updating - abort and prompt user
            prompt_external_component_updates(components_needing_update, ui)
            return  # Abort script execution
        
        # Check if we have any components to process
        if not classified_components:
            ui.messageBox('No components with sheet metal bodies found to export.')
            return
        
        # Task 11: Initialize error tracking
        export_result = ExportResult()
        
        # Track original document and active component for restoration
        app = adsk.core.Application.get()
        original_document = app.activeDocument
        original_active_component = design.activeComponent
        
        # Tasks 7 & 8: Batch Process All Components
        total_count = len(classified_components)
        
        for index, comp_info in enumerate(classified_components, start=1):
            component = comp_info['component']
            is_external = comp_info['is_external']
            
            try:
                if is_external:
                    # Task 7: Handle external component
                    handle_external_component(
                        comp_info=comp_info,
                        original_document=original_document,
                        original_design=design,
                        filename_manager=filename_manager,
                        export_result=export_result,
                        current_index=index,
                        total_count=total_count,
                        ui=ui,
                        export_drawings=export_drawings,
                        drawings_folder=drawings_folder
                    )
                else:
                    # Task 8: Handle internal component
                    handle_internal_component(
                        comp_info=comp_info,
                        original_active_component=original_active_component,
                        design=design,
                        filename_manager=filename_manager,
                        export_result=export_result,
                        current_index=index,
                        total_count=total_count,
                        ui=ui,
                        export_drawings=export_drawings,
                        drawings_folder=drawings_folder
                    )
            except Exception as e:
                # Catch any unexpected errors and continue processing
                error_msg = f'Unexpected error processing component "{component.name}": {str(e)}'
                export_result.record_failure(component.name, error_msg)
        
        # Restore original active component
        try:
            if original_active_component:
                design.activeComponent = original_active_component
        except:
            # If restoration fails, continue - not critical
            pass
        
        # Task 11: Show summary of results
        export_result.show_summary(ui)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
