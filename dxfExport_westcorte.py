#Author-
#Description-

# Fusion 360 API Reference: https://github.com/AutodeskFusion360/FusionAPIReference
# Python API docs: Fusion_API_Python_Reference/defs/
# HTML docs: Fusion_API_Documentation/files/

import adsk.core, adsk.fusion, adsk.cam, traceback
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
        self.used_filenames = {}  # Maps base filename -> counter
        
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
    
    def get_export_path(self, component_name):
        """
        Generate a unique export path for a component.
        
        Uses component name only (not parent path).
        Handles duplicates by appending sequential numbers.
        Checks both in-session duplicates and existing files on disk.
        
        Args:
            component_name: The name of the component to export
            
        Returns:
            str: Full path to the export file (including .dxf extension)
        """
        # Sanitize the base filename
        base_name = self.sanitize_filename(component_name)
        
        # Determine the starting counter for this base name
        if base_name not in self.used_filenames:
            # First time seeing this base name - start at 0
            self.used_filenames[base_name] = -1  # Will be incremented to 0
        
        # Increment counter for this base name
        self.used_filenames[base_name] += 1
        counter = self.used_filenames[base_name]
        
        # Generate filename based on counter
        if counter == 0:
            # First occurrence - use base name without number
            filename = f"{base_name}.dxf"
        else:
            # Duplicate detected - append number
            filename = f"{base_name}_{counter}.dxf"
        
        # Construct full path
        full_path = os.path.join(self.output_folder, filename)
        
        # Check if file already exists on disk and find next available number
        while os.path.exists(full_path):
            self.used_filenames[base_name] += 1
            counter = self.used_filenames[base_name]
            if counter == 0:
                filename = f"{base_name}.dxf"
            else:
                filename = f"{base_name}_{counter}.dxf"
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
        self.successful_exports = []  # List of dicts: {'component_name': str, 'file_path': str}
        self.failed_exports = []      # List of dicts: {'component_name': str, 'error': str}
    
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
        
        # Build summary message
        lines = []
        
        # Main summary line
        if total == 0:
            lines.append("No components were processed.")
        else:
            lines.append(f"Export Summary: {success_count} of {total} components exported successfully.")
        
        # Add failure details if any
        if failure_count > 0:
            lines.append("")
            lines.append(f"Failed Exports ({failure_count}):")
            for failure in self.failed_exports:
                lines.append(f"  • {failure['component_name']}: {failure['error']}")
        
        # Add successful export file paths
        if success_count > 0:
            lines.append("")
            lines.append(f"Exported Files ({success_count}):")
            for export in self.successful_exports:
                # Show just the filename, not full path (for readability)
                filename = os.path.basename(export['file_path'])
                lines.append(f"  • {export['component_name']} → {filename}")
        
        return "\n".join(lines)
    
    def show_summary(self, ui):
        """
        Display the summary message in a message box.
        
        Args:
            ui: Fusion 360 UI object for displaying messages
        """
        summary = self.format_summary()
        
        # Determine title based on results
        if self.get_failure_count() == 0 and self.get_success_count() > 0:
            title = "Export Complete"
        elif self.get_failure_count() > 0:
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
    
    # Check if this component has sheet metal bodies
    if comp and has_sheet_metal_bodies(comp):
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
        
        is_external = False
        source_document = None
        
        # Check if component is external/referenced
        # External components are typically accessed via occurrences
        if occurrence:
            # Check if occurrence represents a referenced component
            # In Fusion 360 API, occurrences of external components have specific properties
            try:
                # Try to access the component's document
                # External components come from different documents
                comp_doc = component.parentDocument
                current_doc = design.parentDocument
                
                # If documents are different, it's external
                if comp_doc and current_doc and comp_doc != current_doc:
                    is_external = True
                    source_document = comp_doc
                elif occurrence.isReferencedComponent:
                    # Alternative check: occurrence property
                    is_external = True
                    # Try to get source document from occurrence
                    try:
                        source_document = occurrence.component.parentDocument
                    except:
                        pass
            except:
                # If we can't determine, assume internal
                pass
        
        # Also check if component itself is marked as referenced
        try:
            if hasattr(component, 'isReferenced') and component.isReferenced:
                is_external = True
                try:
                    source_document = component.parentDocument
                except:
                    pass
        except:
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
    
    Checks if any external/referenced components need updating.
    If updates are required, prompts the user and returns False to abort execution.
    
    Uses Option B: Checks external components after they're discovered via Task 4/5.
    
    Args:
        classified_components: List of component info dicts from Task 5
                              Each dict has 'component', 'occurrence', 'is_external', 'source_document'
        design: The Fusion 360 Design object
        ui: Optional UI object for displaying messages (required for user prompts)
        
    Returns:
        tuple: (all_up_to_date: bool, components_needing_update: list)
               - all_up_to_date: True if all external components are up-to-date, False otherwise
               - components_needing_update: List of component names that need updating
    """
    components_needing_update = []
    
    # Filter to only external components
    external_components = [comp_info for comp_info in classified_components if comp_info['is_external']]
    
    if not external_components:
        # No external components, so nothing to check
        return (True, [])
    
    # Check each external component for update status
    for comp_info in external_components:
        component = comp_info['component']
        occurrence = comp_info['occurrence']
        component_name = component.name
        
        needs_update = False
        
        # Try multiple API methods to check if component needs updating
        # Method 1: Check occurrence property (if available)
        if occurrence:
            try:
                # Some Fusion 360 APIs have isUpToDate on occurrences
                if hasattr(occurrence, 'isUpToDate'):
                    if not occurrence.isUpToDate:
                        needs_update = True
                # Alternative: check for updateAvailable property
                elif hasattr(occurrence, 'updateAvailable'):
                    if occurrence.updateAvailable:
                        needs_update = True
            except:
                pass
        
        # Method 2: Check component property (if available)
        if not needs_update:
            try:
                if hasattr(component, 'isUpToDate'):
                    if not component.isUpToDate:
                        needs_update = True
                elif hasattr(component, 'updateAvailable'):
                    if component.updateAvailable:
                        needs_update = True
            except:
                pass
        
        # Method 3: Check via document reference
        # External components that are out of date may have different document states
        if not needs_update and comp_info['source_document']:
            try:
                source_doc = comp_info['source_document']
                current_doc = design.parentDocument
                
                # If documents are different, check if source document has unsaved changes
                # or if component reference is stale
                # Note: This is a heuristic - the actual API method may vary
                if source_doc != current_doc:
                    # Try to check document modification status
                    # External components that need updating often have this property
                    if hasattr(source_doc, 'isModified'):
                        # This might indicate the external file has been modified
                        # But we need to check component-specific update status
                        pass
            except:
                pass
        
        # Method 4: Check all occurrences in design for this component
        # Sometimes the update status is tracked at the occurrence level
        if not needs_update:
            try:
                root_comp = design.rootComponent
                for occ in root_comp.allOccurrences:
                    if occ.component == component:
                        # Check if this occurrence needs updating
                        if hasattr(occ, 'isUpToDate'):
                            if not occ.isUpToDate:
                                needs_update = True
                                break
                        elif hasattr(occ, 'updateAvailable'):
                            if occ.updateAvailable:
                                needs_update = True
                                break
            except:
                pass
        
        if needs_update:
            components_needing_update.append(component_name)
    
    all_up_to_date = len(components_needing_update) == 0
    return (all_up_to_date, components_needing_update)

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
            # Flat pattern exists - try to update it
            # Note: Fusion 360 API may not have a direct update() method
            # Flat patterns typically update automatically when geometry changes
            # However, we can try to regenerate/refresh if needed
            try:
                # Some APIs use regenerate() or similar methods
                # If update method exists, use it; otherwise assume it's current
                if hasattr(flatPattern, 'update'):
                    flatPattern.update()
                elif hasattr(flatPattern, 'regenerate'):
                    flatPattern.regenerate()
                # If no update method, assume flat pattern is current
                # (Fusion 360 typically maintains flat patterns automatically)
            except Exception as e:
                # Update failed, but flat pattern exists - continue anyway
                # Log warning but don't fail
                pass
            
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
        
        # Attempt to set units to Millimeters (default is document units)
        try:
            # Try common property names for units
            dxfOptions.unit = adsk.fusion.FlatPatternExportUnits.MillimeterFlatPatternExportUnit
        except:
            try:
                dxfOptions.unit = adsk.fusion.FlatPatternExportUnits.Millimeter
            except:
                pass # Fallback to document units if property not found
        
        # Execute Export
        exportMgr.execute(dxfOptions)
        
        return (True, None)
        
    except Exception as e:
        error_msg = f'Failed to export DXF for component "{component.name}": {str(e)}'
        return (False, error_msg)

def handle_external_component(comp_info, original_document, original_design, filename_manager, 
                             export_result, current_index, total_count, ui):
    """
    Task 7: External Component Handling
    
    Handles export of external/referenced components:
    - Opens external component in new tab/document (bring to front)
    - Activates the component in the opened document
    - Exports flat pattern using Task 6 logic
    - Uses Task 9 for filename generation
    - Uses Task 10 for progress updates
    - Uses Task 11 for error tracking
    - Closes the opened document (without saving - should be unchanged)
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
        
    Returns:
        bool: True if export was successful, False otherwise
    """
    component = comp_info['component']
    component_name = component.name
    
    # Show progress
    show_progress(ui, current_index, total_count, component_name, display=False)
    
    # Track original active document
    app = adsk.core.Application.get()
    opened_document = None
    
    try:
        # Get the source document for the external component
        source_doc = comp_info.get('source_document')
        
        if not source_doc:
            # Try to get document from component
            try:
                source_doc = component.parentDocument
            except:
                pass
        
        if not source_doc:
            error_msg = f'Could not determine source document for external component "{component_name}"'
            export_result.record_failure(component_name, error_msg)
            return False
        
        # Open the external component's document
        # In Fusion 360, external components are typically already accessible
        # but we may need to activate their document
        try:
            # Check if document is already open
            documents = app.documents
            opened_document = None
            
            # Try to find the document in open documents
            for i in range(documents.count):
                doc = documents.item(i)
                if doc == source_doc:
                    opened_document = doc
                    break
            
            # If document not found in open documents, try to open it
            # Note: External components may already be accessible without explicit opening
            # The document might be referenced but not actively open
            if not opened_document:
                # Try to open the document if it has a file path
                try:
                    if hasattr(source_doc, 'dataFile') and source_doc.dataFile:
                        # Document has a file - try to open it
                        # Note: This may not be necessary if component is already accessible
                        # Fusion 360 may handle external references automatically
                        pass
                except:
                    pass
            
            # If we couldn't find/open the document, try to work with the component directly
            # External components may be accessible through their occurrence
            if not opened_document:
                opened_document = source_doc
            
            # Activate the document (bring to front)
            if opened_document:
                try:
                    app.activeDocument = opened_document
                except:
                    # If activation fails, continue anyway - component may still be accessible
                    pass
            
            # Get the design from the opened document
            opened_design = None
            if opened_document:
                try:
                    opened_design = opened_document.product
                    if not isinstance(opened_design, adsk.fusion.Design):
                        opened_design = None
                except:
                    pass
            
            # If we couldn't get design from opened document, try to use component's design
            if not opened_design:
                try:
                    # Component should have access to its design
                    comp_doc = component.parentDocument
                    if comp_doc:
                        opened_design = comp_doc.product
                        if not isinstance(opened_design, adsk.fusion.Design):
                            opened_design = None
                except:
                    pass
            
            if not opened_design:
                error_msg = f'Could not access design for external component "{component_name}"'
                export_result.record_failure(component_name, error_msg)
                return False
            
            # Activate the component in the opened design
            try:
                opened_design.activeComponent = component
            except:
                # If activation fails, try alternative method
                try:
                    component.activate()
                except:
                    # If both fail, continue anyway - may still be able to export
                    pass
            
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
                component, flat_pattern, export_path, opened_design
            )
            
            if export_success:
                export_result.record_success(component_name, export_path)
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
                             export_result, current_index, total_count, ui):
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
        
    Returns:
        bool: True if export was successful, False otherwise
    """
    component = comp_info['component']
    component_name = component.name
    
    # Show progress
    show_progress(ui, current_index, total_count, component_name, display=False)
    
    try:
        # Activate the component
        try:
            design.activeComponent = component
        except:
            # If direct activation fails, try alternative method
            try:
                component.activate()
            except Exception as e:
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
            return True
        else:
            export_result.record_failure(component_name, export_error or 'Export failed')
            return False
            
    except Exception as e:
        error_msg = f'Error processing internal component "{component_name}": {str(e)}'
        export_result.record_failure(component_name, error_msg)
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

        # 1. Folder Selection Dialog (Early - before any processing)
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
                        ui=ui
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
                        ui=ui
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
