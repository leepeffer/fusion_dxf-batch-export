# Fusion 360 DXF Batch Export

A Fusion 360 add-in script for exporting sheet metal flat patterns to DXF files with settings optimized for West Corte.

## Description

This script automates the export of sheet metal flat patterns from Fusion 360 to DXF format. It handles flat pattern creation, file naming, and applies specific export settings required by West Corte.

## Features

- **Automatic Flat Pattern Creation**: Automatically creates flat patterns if they don't exist
- **Smart Base Face Detection**: Finds the largest planar face to use as the base for flat pattern creation
- **Custom Export Settings**: 
  - Center lines (bend lines) enabled
  - Extent lines (bounding box) disabled
  - Splines preserved (not converted to polylines)
  - Units set to millimeters
- **Component-Based Naming**: Exports DXF files using the active component name
- **Folder Selection Dialog**: User-friendly folder selection for output location

## Requirements

- Fusion 360 (desktop application)
- Windows or macOS
- Active Fusion 360 design with sheet metal components

## Installation

1. Clone or download this repository
2. Open Fusion 360
3. Go to **Tools** → **Add-Ins** → **Scripts and Add-Ins**
4. Click the **+** button to add a new script
5. Navigate to the downloaded folder and select `dxfExport_westcorte.py`
6. The script will appear in your scripts list

## Usage

1. Open a Fusion 360 design containing sheet metal components
2. Ensure the component you want to export is active (selected in the browser)
3. Run the script from **Tools** → **Add-Ins** → **Scripts and Add-Ins** → **dxfExport_westcorte**
4. Select the output folder when prompted
5. The script will:
   - Check for an existing flat pattern, or create one automatically
   - Export the flat pattern to DXF format
   - Save the file with the component name (sanitized for the file system)
6. A success message will display with the export path

## Export Settings

The script applies the following DXF export options:

- **Center Lines**: Enabled (bend lines are exported)
- **Extent Lines**: Disabled (bounding box lines are not exported)
- **Spline Conversion**: Disabled (splines remain as splines)
- **Units**: Millimeters

## File Naming

The exported DXF file will be named after the active component. Illegal characters (such as `:`) are replaced with underscores (`_`) to ensure compatibility with the file system.

## Troubleshooting

- **"No active Fusion 360 design found"**: Make sure you have a design file open
- **"The active component does not contain any Sheet Metal bodies"**: Ensure your component contains sheet metal bodies
- **"Could not automatically determine a base face"**: The script couldn't find a suitable planar face. Try creating the flat pattern manually first
- **"Failed to create Flat Pattern"**: The sheet metal model may have validation issues. Check your model for errors

## Files

- `dxfExport_westcorte.py` - Main script file
- `dxfExport_westcorte.manifest` - Add-in manifest file
- `ScriptIcon.svg` - Script icon

## API Reference

When developing or modifying this script, refer to the official Fusion 360 API documentation:
- **Fusion API Reference Repository**: https://github.com/AutodeskFusion360/FusionAPIReference
- Contains HTML documentation, C++ headers, and Python object definitions
- Python reference: `Fusion_API_Python_Reference/defs/`
- HTML documentation: `Fusion_API_Documentation/files/`

## Development Plan

See [PLAN.md](./PLAN.md) for the development roadmap and next steps for batch export functionality.

## License

This project is provided as-is for use with Fusion 360.
