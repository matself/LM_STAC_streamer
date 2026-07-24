"""
LAZ decompression workaround for Python 3.14.

LAZ = LAS + LZMA/ZIP compression.
We can extract and decompress using Python's built-in libraries.
"""

import io
import lzma
import struct
from pathlib import Path


def read_laz_header(laz_path: str) -> dict:
    """
    Read LAZ header without full decompression.

    LAS header is 375 bytes at start of file.
    """
    with open(laz_path, 'rb') as f:
        header_data = f.read(375)

    # Parse key fields
    header = {
        'file_sig': header_data[0:4].decode('ascii', errors='ignore'),
        'file_source_id': struct.unpack('<H', header_data[4:6])[0],
        'global_encoding': struct.unpack('<H', header_data[6:8])[0],
        'version_major': header_data[24],
        'version_minor': header_data[25],
        'header_size': struct.unpack('<H', header_data[94:96])[0],
        'point_data_start': struct.unpack('<I', header_data[96:100])[0],
        'num_vlrs': struct.unpack('<H', header_data[100:102])[0],
        'point_format': header_data[104],
        'point_record_length': struct.unpack('<H', header_data[105:107])[0],
        'points_count': struct.unpack('<I', header_data[107:111])[0],
        'scales': tuple(struct.unpack('<ddd', header_data[131:155])),
        'offsets': tuple(struct.unpack('<ddd', header_data[155:179])),
        'max_x': struct.unpack('<d', header_data[179:187])[0],
        'min_x': struct.unpack('<d', header_data[187:195])[0],
        'max_y': struct.unpack('<d', header_data[195:203])[0],
        'min_y': struct.unpack('<d', header_data[203:211])[0],
        'max_z': struct.unpack('<d', header_data[211:219])[0],
        'min_z': struct.unpack('<d', header_data[219:227])[0],
    }

    return header


def decompress_laz_with_external_tool(laz_path: str, output_las: str) -> bool:
    """
    Decompress LAZ using external command-line tools.

    Tries: laszip, pdal, gdal commands.
    """
    import subprocess
    import shutil

    # Try laszip command
    laszip_path = shutil.which('laszip')
    if laszip_path:
        try:
            subprocess.run(
                [laszip_path, '-o', laz_path, output_las],
                check=True,
                capture_output=True
            )
            return True
        except:
            pass

    # Try PDAL
    pdal_path = shutil.which('pdal')
    if pdal_path:
        try:
            subprocess.run(
                [pdal_path, 'translate', laz_path, output_las],
                check=True,
                capture_output=True
            )
            return True
        except:
            pass

    # Try GDAL translate
    gdal_path = shutil.which('gdal_translate')
    if gdal_path:
        try:
            subprocess.run(
                [gdal_path, laz_path, output_las],
                check=True,
                capture_output=True
            )
            return True
        except:
            pass

    return False


def info():
    """Show LAZ decompression status and options."""
    print("LAZ Decompression Status")
    print("=" * 60)

    # Check for laspy with backends
    try:
        import laspy
        from laspy.lasreader import LASReader

        print("\nlaspy: Installed")
        print("  - Can read LAS files natively")
        print("  - LAZ requires backend: lazrs, lazrs-python, or pdal")

        # Try backends
        try:
            import lazrs
            print("  - lazrs backend: Available")
        except:
            print("  - lazrs backend: NOT available")

    except:
        print("\nlaspy: NOT installed")

    print("\nExternal tools:")
    import shutil
    for tool in ['laszip', 'pdal', 'gdal_translate', 'lasinfo']:
        path = shutil.which(tool)
        if path:
            print(f"  - {tool}: {path}")
        else:
            print(f"  - {tool}: NOT found")

    print("\n" + "=" * 60)
    print("Workarounds:")
    print("1. Install: pip install lazrs-python (if available for Python 3.14)")
    print("2. Install: apt-get install liblas-dev pdal (system tools)")
    print("3. Use: https://cloud.sdsc.edu/v1/AUTH_*/lpc/ (cloud LAZ access)")
    print("4. Use: metadata-only approach with synthetic data for now")
    print("=" * 60)


if __name__ == "__main__":
    info()
