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
        
        # For now, continue with existing single-component logic
        # This will be used by Task 4 (Hierarchy Traversal) later
        
        # Target the active component
        activeComp = design.activeComponent
        
        # 2. Check/Create Flat Pattern
        flatPattern = activeComp.flatPattern
        
        if not flatPattern:
            # Try to create it manually
            # Heuristic: Find the first sheet metal body and a large planar face
            targetBody = None
            for body in activeComp.bRepBodies:
                if body.isSheetMetal:
                    targetBody = body
                    break
            
            if not targetBody:
                ui.messageBox('The active component does not contain any Sheet Metal bodies.')
                return
                
            # Find largest planar face to use as base face
            bestFace = None
            maxArea = 0.0
            
            for face in targetBody.faces:
                # Check if geometry is a plane
                if face.geometry.objectType == adsk.core.Plane.classType():
                    if face.area > maxArea:
                        maxArea = face.area
                        bestFace = face
            
            if not bestFace:
                ui.messageBox('Could not automatically determine a base face for the Flat Pattern.')
                return
            
            # Create the Flat Pattern
            try:
                flatPattern = activeComp.createFlatPattern(bestFace)
            except:
                # If creation fails, notify user
                ui.messageBox('Failed to create Flat Pattern. Please ensure the model is valid sheet metal.')
                return

        # 3. Export to DXF
        if flatPattern:
            # Task 9: Use FilenameManager for naming and duplicate handling
            fullPath = filename_manager.get_export_path(activeComp.name)
            
            exportMgr = design.exportManager
            
            # Create DXF Export Options
            # Note: createDXFFlatPatternExportOptions is the correct method for FlatPattern
            dxfOptions = exportMgr.createDXFFlatPatternExportOptions(fullPath, flatPattern)
            
            # Explicitly set options
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
            
            ui.messageBox(f'Export Successful!\nSubject: {activeComp.name}\nPath: {fullPath}')
            
        else:
            ui.messageBox('Unexpected error: Flat Pattern valid but not found.')

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
