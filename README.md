# Fusion 360 DXF Batch Export

A Fusion 360 add-in script for batch exporting sheet metal flat patterns to DXF files with settings optimized for West Corte.

## Description

This script automates the batch export of sheet metal flat patterns from Fusion 360 to DXF format. It can process entire assemblies, handling both internal components and external referenced components. The script automatically creates flat patterns when needed, manages file naming with duplicate detection, and applies West Corte-specific export settings.

## Features

- **Batch Processing**: Processes entire assemblies, automatically finding and exporting all sheet metal components
- **External Component Support**: Handles both internal components and external referenced components from other Fusion 360 files
- **Automatic Flat Pattern Management**: Creates flat patterns when missing and ensures they are up-to-date
- **Smart Base Face Detection**: Finds the largest planar face to use as the base for flat pattern creation
- **Intelligent File Naming**: Uses component names with automatic duplicate detection and numbering (e.g., `Component.dxf`, `Component_1.dxf`)
- **Progress Feedback**: Shows real-time progress during batch exports with component counts
- **Error Recovery**: Continues processing even if individual components fail, providing comprehensive error reporting
- **Custom Export Settings**:
  - Center lines (bend lines) enabled
  - Extent lines (bounding box) disabled
  - Splines preserved (not converted to polylines)
  - Units set to millimeters
- **External Component Update Detection**: Checks and prompts users to update external components before export

## Requirements

- Fusion 360 (desktop application)
- Windows or macOS
- Active Fusion 360 design with sheet metal components (single component or assembly)
- External referenced components (if used) should be accessible and up-to-date

## Installation

### Option 1: Using GitHub/GitLab Installer (Recommended)

1. Install the "Install scripts or addins from GitHub or GitLab" addon from the [Autodesk App Store](https://apps.autodesk.com/FUSION/en/Detail/Index?id=789800822168335025&appLang=en&os=Mac&autostart=true)
2. Launch the addon in Fusion 360
3. Enter this repository URL: `https://github.com/leepeffer/fusion_dxf-batch-export`
4. Click OK - the script will be automatically installed

### Option 2: Manual Installation

1. Clone or download this repository
2. Open Fusion 360
3. Go to **Tools** → **Add-Ins** → **Scripts and Add-Ins**
4. Click the **+** button to add a new script
5. Navigate to the downloaded folder and select `dxfExport_westcorte.py`
6. The script will appear in your scripts list

## Usage

1. Open a Fusion 360 design containing sheet metal components (single component or assembly)
2. Run the script from **Tools** → **Add-Ins** → **Scripts and Add-Ins** → **dxfExport_westcorte**
3. Select the output folder when prompted (this happens first)
4. The script will automatically:
   - Check for external referenced components and prompt to update them if needed
   - Traverse the component hierarchy to find all sheet metal components
   - Process each component individually:
     - Create flat patterns if they don't exist
     - Export to DXF format with West Corte settings
     - Generate unique filenames with duplicate handling
   - Show progress feedback: "Exporting component X of Y: ComponentName"
   - Continue processing even if individual components fail
5. A summary will display showing successful exports, failures, and file paths

## Export Settings

The script applies the following DXF export options:

- **Center Lines**: Enabled (bend lines are exported)
- **Extent Lines**: Disabled (bounding box lines are not exported)
- **Spline Conversion**: Disabled (splines remain as splines)
- **Units**: Millimeters

## External Component Handling

The script automatically detects and handles external referenced components:

- **External Components**: Components referenced from other Fusion 360 files
- **Update Check**: Before processing, the script checks if external components need updating
- **User Prompt**: If updates are required, users are prompted to update external components manually
- **Document Management**: External components are opened in new tabs, processed, then closed
- **Context Restoration**: Original document focus is maintained throughout the process

## File Naming

Each exported DXF file is named after its component. The script handles:
- **Component Names**: Uses the component name (not full path)
- **Illegal Characters**: Replaces characters like `:` with `_` for file system compatibility
- **Duplicates**: Automatically appends numbers for duplicate names (`Component.dxf`, `Component_1.dxf`)
- **Session Tracking**: Prevents overwrites within the same export session

## Troubleshooting

- **"No active Fusion 360 design found"**: Make sure you have a design file open
- **"No components with sheet metal bodies found to export"**: The design doesn't contain any sheet metal components, or they're not properly configured
- **"External components need updating"**: Some referenced components from other files need to be updated. Update them manually and run the script again
- **"Could not automatically determine a base face"**: The script couldn't find a suitable planar face for flat pattern creation. Try creating the flat pattern manually first
- **"Failed to create Flat Pattern"**: The sheet metal model may have validation issues. Check your model for errors
- **"Failed to activate component"**: Component activation failed. This may be due to design complexity or component state
- **"External component document could not be opened"**: Referenced component file may be missing, corrupted, or inaccessible
- **Individual component export failures**: The script continues processing other components. Check the summary for specific error details

## Files

- `dxfExport_westcorte.py` - Main script file containing:
  - `FilenameManager` class - Handles file naming with duplicate detection
  - `ExportResult` class - Tracks export results and provides summary feedback
  - Batch processing functions for component traversal and export
  - External component handling and document management
- `dxfExport_westcorte.manifest` - Add-in manifest file
- `ScriptIcon.svg` - Script icon
- `PLAN.md` - Development plan and implementation status

## API Reference

When developing or modifying this script, refer to the official Fusion 360 API documentation:
- **Fusion API Reference Repository**: https://github.com/AutodeskFusion360/FusionAPIReference
- Contains HTML documentation, C++ headers, and Python object definitions
- Python reference: `Fusion_API_Python_Reference/defs/`
- HTML documentation: `Fusion_API_Documentation/files/`

## Development Status

The batch export system is fully implemented. See [PLAN.md](./PLAN.md) for implementation details, API compliance status, and testing scenarios.

## License

This project is provided as-is for use with Fusion 360.
