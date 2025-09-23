#!/usr/bin/env python3

"""
osmand2qgis_point.py

This script converts OSMAnd rendering style XML definitions for point features into a QGIS style XML file.
It processes <case> elements from the OSMAnd style file that define icons and shields for map points,
encodes the corresponding SVG files as base64, and generates QGIS symbol definitions with these icons and shields.
The resulting QGIS style XML can be imported into QGIS to reproduce OSMAnd-style point symbology.

Main functionalities:
- Parses the OSMAnd rendering style XML to extract relevant <case> elements with tag, value, and icon attributes.
- Locates and base64-encodes the corresponding SVG icon and shield files.
- Constructs QGIS symbol XML elements with the encoded SVGs as marker layers.
- Handles duplicate symbols, missing shields, and missing files with informative statistics.
- Outputs a formatted QGIS style XML file with all generated symbols.

Requirements:
- lxml library for XML parsing and generation.
- Access to the OSMAnd rendering style XML and the corresponding SVG icon and shield directories.

Usage:
  python osmand2qgis_point.py
"""

from lxml import etree as ET
from os.path import join, exists
import base64
import uuid
import os

def create_qgis_symbol(value, icon_base64, shield_base64):
  """Create a QGIS symbol XML element"""
  # Create symbol element
  symbol = ET.Element("symbol")
  symbol.set("type", "marker")
  symbol.set("frame_rate", "10")
  symbol.set("tags", "OSMAnd")
  symbol.set("clip_to_extent", "1")
  symbol.set("is_animated", "0")
  symbol.set("force_rhr", "0")
  symbol.set("name", value)
  symbol.set("alpha", "1")

  # Data defined properties for symbol
  ddp_symbol = ET.SubElement(symbol, "data_defined_properties")
  option_symbol = ET.SubElement(ddp_symbol, "Option")
  option_symbol.set("type", "Map")
  name_opt = ET.SubElement(option_symbol, "Option")
  name_opt.set("type", "QString")
  name_opt.set("value", "")
  name_opt.set("name", "name")
  props_opt = ET.SubElement(option_symbol, "Option")
  props_opt.set("name", "properties")
  type_opt = ET.SubElement(option_symbol, "Option")
  type_opt.set("type", "QString")
  type_opt.set("value", "collection")
  type_opt.set("name", "type")

  # First layer - Shield (background)
  layer1 = ET.SubElement(symbol, "layer")
  layer1.set("pass", "0")
  layer1.set("enabled", "1")
  layer1.set("class", "SvgMarker")
  layer1.set("locked", "0")

  option1 = ET.SubElement(layer1, "Option")
  option1.set("type", "Map")

  # Shield layer options
  shield_options = [
    ("angle", "QString", "0"),
    ("color", "QString", "255,255,255,255,rgb:1,1,1,1"),
    ("fixedAspectRatio", "QString", "0"),
    ("horizontal_anchor_point", "QString", "1"),
    ("name", "QString", shield_base64),
    ("offset", "QString", "0,0"),
    ("offset_map_unit_scale", "QString", "3x:0,0,0,0,0,0"),
    ("offset_unit", "QString", "MM"),
    ("outline_color", "QString", "255,255,255,255,rgb:1,1,1,1"),
    ("outline_width", "QString", "0.4"),
    ("outline_width_map_unit_scale", "QString", "3x:0,0,0,0,0,0"),
    ("outline_width_unit", "QString", "MM"),
    ("scale_method", "QString", "diameter"),
    ("size", "QString", "6.8"),
    ("size_map_unit_scale", "QString", "3x:0,0,0,0,0,0"),
    ("size_unit", "QString", "MM"),
    ("vertical_anchor_point", "QString", "1")
  ]

  for name, opt_type, value in shield_options:
    opt = ET.SubElement(option1, "Option")
    opt.set("type", opt_type)
    opt.set("value", value)
    opt.set("name", name)

  # Parameters option for shield
  params_opt1 = ET.SubElement(option1, "Option")
  params_opt1.set("name", "parameters")

  # Data defined properties for shield layer
  ddp1 = ET.SubElement(layer1, "data_defined_properties")
  option_ddp1 = ET.SubElement(ddp1, "Option")
  option_ddp1.set("type", "Map")
  name_ddp1 = ET.SubElement(option_ddp1, "Option")
  name_ddp1.set("type", "QString")
  name_ddp1.set("value", "")
  name_ddp1.set("name", "name")
  props_ddp1 = ET.SubElement(option_ddp1, "Option")
  props_ddp1.set("name", "properties")
  type_ddp1 = ET.SubElement(option_ddp1, "Option")
  type_ddp1.set("type", "QString")
  type_ddp1.set("value", "collection")
  type_ddp1.set("name", "type")

  # Second layer - Icon
  layer2 = ET.SubElement(symbol, "layer")
  layer2.set("pass", "0")
  layer2.set("enabled", "1")
  layer2.set("class", "SvgMarker")
  layer2.set("locked", "0")

  option2 = ET.SubElement(layer2, "Option")
  option2.set("type", "Map")

  # Icon layer options
  icon_options = [
    ("angle", "QString", "0"),
    ("color", "QString", "255,255,255,255,rgb:1,1,1,1"),
    ("fixedAspectRatio", "QString", "0"),
    ("horizontal_anchor_point", "QString", "1"),
    ("name", "QString", icon_base64),
    ("offset", "QString", "0,0"),
    ("offset_map_unit_scale", "QString", "3x:0,0,0,0,0,0"),
    ("offset_unit", "QString", "MM"),
    ("outline_color", "QString", "255,255,255,255,rgb:1,1,1,1"),
    ("outline_width", "QString", "0.1"),
    ("outline_width_map_unit_scale", "QString", "3x:0,0,0,0,0,0"),
    ("outline_width_unit", "QString", "MM"),
    ("scale_method", "QString", "diameter"),
    ("size", "QString", "4.4"),
    ("size_map_unit_scale", "QString", "3x:0,0,0,0,0,0"),
    ("size_unit", "QString", "MM"),
    ("vertical_anchor_point", "QString", "1")
  ]

  for name, opt_type, value in icon_options:
    opt = ET.SubElement(option2, "Option")
    opt.set("type", opt_type)
    opt.set("value", value)
    opt.set("name", name)

  # Parameters option for icon
  params_opt2 = ET.SubElement(option2, "Option")
  params_opt2.set("name", "parameters")

  # Data defined properties for icon layer
  ddp2 = ET.SubElement(layer2, "data_defined_properties")
  option_ddp2 = ET.SubElement(ddp2, "Option")
  option_ddp2.set("type", "Map")
  name_ddp2 = ET.SubElement(option_ddp2, "Option")
  name_ddp2.set("type", "QString")
  name_ddp2.set("value", "")
  name_ddp2.set("name", "name")
  props_ddp2 = ET.SubElement(option_ddp2, "Option")
  props_ddp2.set("name", "properties")
  type_ddp2 = ET.SubElement(option_ddp2, "Option")
  type_ddp2.set("type", "QString")
  type_ddp2.set("value", "collection")
  type_ddp2.set("name", "type")

  return symbol

def find_shield_value(case_element):
  """Find shield value from case element or its parents"""
  # First check if the case itself has a shield attribute
  if 'shield' in case_element.attrib:
    return case_element.attrib['shield']

  # Walk up the parent tree to find shield attribute
  parent = case_element.getparent()
  while parent is not None:
    if parent.tag == 'switch' and 'shield' in parent.attrib:
      return parent.attrib['shield']
    elif parent.tag == 'apply' and 'shield' in parent.attrib:
      return parent.attrib['shield']
    parent = parent.getparent()

  return None

def main():
  osmand_xml = join("OsmAnd-resources", "rendering_styles", "default.render.xml")
  icons_dir = join("OsmAnd-resources", "rendering_styles", "style-icons", "poi-icons-svg")
  shields_dir = join("OsmAnd-resources", "icons", "svg", "shields")

  tree = ET.parse(osmand_xml)
  root = tree.getroot()
  # Search for all case elements with tag, value, and icon attributes anywhere in the XML
  cases = root.findall(".//case[@tag][@value][@icon]")
  print(f"Found {len(cases)} <case> entries with tag, value, and icon attributes.")

  # Create root QGIS style element
  qgis_style = ET.Element("qgis_style")
  qgis_style.set("version", "2")

  # Create symbols container
  symbols_container = ET.SubElement(qgis_style, "symbols")

  # Create empty containers for other QGIS style elements
  ET.SubElement(qgis_style, "colorramps")
  ET.SubElement(qgis_style, "textformats")
  ET.SubElement(qgis_style, "labelsettings")
  ET.SubElement(qgis_style, "legendpatchshapes")
  ET.SubElement(qgis_style, "symbols3d")

  processed_count = 0
  skipped_no_shield = 0
  skipped_no_files = 0
  skipped_duplicates = 0

  for c in cases:
    attrs = dict(c.attrib)
    icon_name = attrs.get("icon", "").strip()
    tag = attrs.get("tag", "").strip()
    value = attrs.get("value", "").strip()

    if not tag or not value or not icon_name:
      continue

    # Create tag:value name for the symbol
    symbol_name = f"{tag}:{value}"

    # Skip duplicates based on tag:value combination
    existing_symbols = symbols_container.findall(f".//symbol[@name='{symbol_name}']")
    if existing_symbols:
      skipped_duplicates += 1
      continue

    # Find shield value (check case element and parent elements)
    shield = find_shield_value(c)
    if not shield:
      skipped_no_shield += 1
      continue

    icon_path = join(icons_dir, f"mx_{icon_name}.svg")
    if not exists(icon_path):
      skipped_no_files += 1
      continue
    with open(icon_path, "rb") as f:
      encoded = base64.b64encode(f.read()).decode("utf-8")
      icon_base64 = f"base64:{encoded}"

    shield_path = join(shields_dir, f"h_{shield}.svg") if shield else None
    if not shield_path or not exists(shield_path):
      skipped_no_files += 1
      continue
    with open(shield_path, "rb") as f:
      encoded = base64.b64encode(f.read()).decode("utf-8")
      shield_base64 = f"base64:{encoded}"

    # Create symbol and add to symbols container
    symbol = create_qgis_symbol(symbol_name, icon_base64, shield_base64)
    symbols_container.append(symbol)
    processed_count += 1

  print(f"Converted {processed_count} symbols.")
  print(f"Skipped {skipped_duplicates} duplicates.")
  print(f"Skipped {skipped_no_shield} without shield.")
  print(f"Skipped {skipped_no_files} due to missing files.")

  # Write XML output
  output_path = join("examples", "points.xml")
  
  # Create output directory if it doesn't exist
  os.makedirs(os.path.dirname(output_path), exist_ok=True)

  # Format the XML with proper indentation
  ET.indent(qgis_style, space="  ")

  # Create tree and write to file
  tree = ET.ElementTree(qgis_style)
  tree.write(output_path, encoding="utf-8", xml_declaration=True)

  # Add DOCTYPE declaration manually
  with open(output_path, "r", encoding="utf-8") as f:
    content = f.read()

  # Replace XML declaration with DOCTYPE
  content = content.replace('<?xml version=\'1.0\' encoding=\'utf-8\'?>',
                           '<?xml version=\'1.0\' encoding=\'utf-8\'?>\n<!DOCTYPE qgis_style>')

  with open(output_path, "w", encoding="utf-8") as f:
    f.write(content)

  print(f"Wrote QGIS style XML to {output_path}")


if __name__ == "__main__":
  main()
