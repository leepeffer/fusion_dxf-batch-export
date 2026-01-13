#Author-
#Description-

# Fusion 360 API Reference: https://github.com/AutodeskFusion360/FusionAPIReference
# Python API docs: Fusion_API_Python_Reference/defs/
# HTML docs: Fusion_API_Documentation/files/

import adsk.core, adsk.fusion, adsk.cam, traceback
import os

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

        # Target the active component
        activeComp = design.activeComponent
        
        # 1. Folder Selection Dialog
        folderDlg = ui.createFolderDialog()
        folderDlg.title = 'Select Output Folder for DXF'
        
        # Show dialog
        dlgResult = folderDlg.showDialog()
        if dlgResult != adsk.core.DialogResults.DialogOK:
            return # User cancelled
            
        outputFolder = folderDlg.folder
        
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
            # Naming: Match component name exactly (sanitized for OS)
            cleanName = activeComp.name.replace(':', '_') # Replace illegal characters for versioned names
            filename = cleanName + '.dxf'
            fullPath = os.path.join(outputFolder, filename)
            
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
