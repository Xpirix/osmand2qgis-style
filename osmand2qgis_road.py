#!/usr/bin/env python3
"""
OsmAnd to QGIS Style Converter for Roads

This script converts road styling from OsmAnd's default.render.xml to QGIS XML style format.
It parses the routeInfo_roadClass elements and creates QGIS line symbols with stroke and main layers.
"""

from lxml import etree
import re

def hex_to_rgb(hex_color):
    """Convert hex color to RGB values."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r},{g},{b},255,rgb:{r/255:.10f},{g/255:.10f},{b/255:.10f},1"
    return "0,0,0,255,rgb:0,0,0,1"

def resolve_color_variable(color_var, color_definitions):
    """Resolve color variable to hex value."""
    if color_var.startswith('$'):
        var_name = color_var[1:]
        if var_name in color_definitions:
            return color_definitions[var_name]
    elif color_var.startswith('#'):
        return color_var
    return "#000000"  # default black

def extract_color_definitions(root):
    """Extract color definitions from rendering attributes."""
    color_defs = {}
    
    # Find all renderingAttribute elements
    for attr in root.xpath('.//renderingAttribute'):
        attr_name = attr.get('name')
        if attr_name and 'Color' in attr_name:
            # Look for the default case (last case without conditions or with minimal conditions)
            cases = attr.xpath('.//case[@attrColorValue]')
            if cases:
                # Get the case with the simplest condition (fewer attributes) or the last one
                best_case = None
                min_attrs = float('inf')
                
                for case in cases:
                    # Count attributes (conditions)
                    attr_count = len([k for k in case.attrib.keys() if k not in ['attrColorValue']])
                    color_value = case.get('attrColorValue')
                    
                    if color_value and color_value.startswith('#') and attr_count < min_attrs:
                        min_attrs = attr_count
                        best_case = case
                
                if best_case is not None:
                    color_defs[attr_name] = best_case.get('attrColorValue')
    
    # Add fallback colors for variables that resolve to other variables
    manual_colors = {
        'tertiaryRoadRouteDetailsColor': '#ffdb93',  # Found manually in XML
        'footwayColor': '#fa8c16',
        'roadRoadColor': '#cdcdcd',  # Found manually 
        'bridlewayColor': '#c76817',
        'pathColor': '#fa8c16',
        'cyclewayColor': '#178fe5'  # Found manually
    }
    
    # Update with manual colors where needed
    for key, value in manual_colors.items():
        if key not in color_defs or not color_defs[key].startswith('#'):
            color_defs[key] = value
            
    return color_defs

def extract_stroke_width_for_zoom(case_elem, zoom_level=16):
    """Extract stroke width for a specific zoom level from case element."""
    # Look for strokeWidth patterns for the given zoom level
    stroke_width_attrs = [
        f'maxzoom="{zoom_level}" strokeWidth=',
        f'minzoom="{zoom_level}" strokeWidth=',
        'strokeWidth='
    ]
    
    # Try to find strokeWidth in nested apply elements
    for apply_elem in case_elem.xpath('.//apply'):
        for case_child in apply_elem.xpath('.//case'):
            case_str = etree.tostring(case_child, encoding='unicode')
            for attr_pattern in stroke_width_attrs:
                if attr_pattern in case_str:
                    # Extract the stroke width value
                    pattern = f'{attr_pattern}"([^"]*)"'
                    match = re.search(pattern, case_str)
                    if match:
                        width_str = match.group(1)
                        # Parse width like "4:4" or "4.5:4.5"
                        if ':' in width_str:
                            return float(width_str.split(':')[0])
                        else:
                            return float(width_str)
    
    # Default fallback widths based on road type if not found
    return 2.0

def extract_road_info(root, color_definitions):
    """Extract road information from the line rendering section."""
    roads = []
    
    # Find the line section with highway rendering
    line_section = root.xpath('.//line')[0]
    
    # Look for switch elements containing highway cases in high zoom levels
    # Find switches with minzoom="14" which contain the main road rendering
    high_zoom_switches = line_section.xpath('.//switch[@minzoom="14"]')
    
    processed_highways = set()  # To avoid duplicates
    
    for switch in high_zoom_switches:
        # Find all highway cases in this switch
        highway_cases = switch.xpath('.//case[@tag="highway"][@value][@color]')
        
        for case in highway_cases:
            tag = case.get('tag')
            value = case.get('value')
            color_attr = case.get('color')
            
            if tag == 'highway' and value and color_attr and value not in processed_highways:
                processed_highways.add(value)
                
                # Resolve color variable
                resolved_color = resolve_color_variable(color_attr, color_definitions)
                
                # Create symbol name
                symbol_name = f"Road {value.replace('_', ' ').title()}"
                
                # Extract stroke width (try to get it from zoom 16)
                stroke_width = extract_stroke_width_for_zoom(case, 16)
                
                roads.append({
                    'tag': tag,
                    'value': value,
                    'color': resolved_color,
                    'symbol_name': symbol_name,
                    'stroke_width': stroke_width
                })
                
                print(f"Found highway: {value}, color: {resolved_color}, width: {stroke_width}")
    
    # Add some additional road types that might be in other sections
    additional_roads = [
        {'value': 'service', 'color_var': '$serviceRoadColor', 'width': 1.5},
        {'value': 'pedestrian', 'color_var': '$pedestrianRoadColor', 'width': 1.2},
        {'value': 'footway', 'color_var': '$footwayColor', 'width': 1.0},
        {'value': 'cycleway', 'color_var': '$cyclewayColor', 'width': 1.0},
        {'value': 'path', 'color_var': '$pathColor', 'width': 1.0},
        {'value': 'bridleway', 'color_var': '$bridlewayColor', 'width': 1.0},
        {'value': 'steps', 'color_var': '$footwayColor', 'width': 1.0},
        {'value': 'living_street', 'color_var': '$residentialRoadColor', 'width': 1.8},
        {'value': 'road', 'color_var': '$roadRoadColor', 'width': 1.5}
    ]
    
    for road_info in additional_roads:
        if road_info['value'] not in processed_highways:
            resolved_color = resolve_color_variable(road_info['color_var'], color_definitions)
            symbol_name = f"Road {road_info['value'].replace('_', ' ').title()}"
            
            roads.append({
                'tag': 'highway',
                'value': road_info['value'],
                'color': resolved_color,
                'symbol_name': symbol_name,
                'stroke_width': road_info['width']
            })
            
            print(f"Added additional highway: {road_info['value']}, color: {resolved_color}, width: {road_info['width']}")
    
    return roads

def create_qgis_symbol(road_info, main_width_ratio=0.8):
    """Create a QGIS line symbol XML element."""
    stroke_width = road_info.get('stroke_width', 1.5)  # Use extracted width
    
    symbol = etree.Element('symbol')
    symbol.set('type', 'line')
    symbol.set('frame_rate', '10')
    symbol.set('tags', 'OSMAnd')
    symbol.set('clip_to_extent', '1')
    symbol.set('is_animated', '0')
    symbol.set('force_rhr', '0')
    symbol.set('name', road_info['symbol_name'])
    symbol.set('alpha', '1')
    
    # Data defined properties
    data_props = etree.SubElement(symbol, 'data_defined_properties')
    option = etree.SubElement(data_props, 'Option')
    option.set('type', 'Map')
    
    name_option = etree.SubElement(option, 'Option')
    name_option.set('type', 'QString')
    name_option.set('value', '')
    name_option.set('name', 'name')
    
    props_option = etree.SubElement(option, 'Option')
    props_option.set('name', 'properties')
    
    type_option = etree.SubElement(option, 'Option')
    type_option.set('type', 'QString')
    type_option.set('value', 'collection')
    type_option.set('name', 'type')
    
    # Stroke layer (first layer, pass 0)
    stroke_layer = etree.SubElement(symbol, 'layer')
    stroke_layer.set('pass', '0')
    stroke_layer.set('enabled', '1')
    stroke_layer.set('class', 'SimpleLine')
    stroke_layer.set('locked', '0')
    
    stroke_option = etree.SubElement(stroke_layer, 'Option')
    stroke_option.set('type', 'Map')
    
    # Stroke layer properties
    stroke_props = {
        'align_dash_pattern': '0',
        'capstyle': 'square',
        'customdash': '5;2',
        'customdash_map_unit_scale': '3x:0,0,0,0,0,0',
        'customdash_unit': 'MM',
        'dash_pattern_offset': '0',
        'dash_pattern_offset_map_unit_scale': '3x:0,0,0,0,0,0',
        'dash_pattern_offset_unit': 'MM',
        'draw_inside_polygon': '0',
        'joinstyle': 'bevel',
        'line_color': hex_to_rgb('#565656'),  # Dark gray for stroke
        'line_style': 'solid',
        'line_width': str(stroke_width),
        'line_width_unit': 'MM',
        'offset': '0',
        'offset_map_unit_scale': '3x:0,0,0,0,0,0',
        'offset_unit': 'MM',
        'ring_filter': '0',
        'trim_distance_end': '0',
        'trim_distance_end_map_unit_scale': '3x:0,0,0,0,0,0',
        'trim_distance_end_unit': 'MM',
        'trim_distance_start': '0',
        'trim_distance_start_map_unit_scale': '3x:0,0,0,0,0,0',
        'trim_distance_start_unit': 'MM',
        'tweak_dash_pattern_on_corners': '0',
        'use_custom_dash': '0',
        'width_map_unit_scale': '3x:0,0,0,0,0,0'
    }
    
    for prop_name, prop_value in stroke_props.items():
        prop_elem = etree.SubElement(stroke_option, 'Option')
        prop_elem.set('type', 'QString')
        prop_elem.set('value', prop_value)
        prop_elem.set('name', prop_name)
    
    # Stroke layer data defined properties
    stroke_data_props = etree.SubElement(stroke_layer, 'data_defined_properties')
    stroke_option_elem = etree.SubElement(stroke_data_props, 'Option')
    stroke_option_elem.set('type', 'Map')
    
    stroke_name_option = etree.SubElement(stroke_option_elem, 'Option')
    stroke_name_option.set('type', 'QString')
    stroke_name_option.set('value', '')
    stroke_name_option.set('name', 'name')
    
    stroke_props_option = etree.SubElement(stroke_option_elem, 'Option')
    stroke_props_option.set('name', 'properties')
    
    stroke_type_option = etree.SubElement(stroke_option_elem, 'Option')
    stroke_type_option.set('type', 'QString')
    stroke_type_option.set('value', 'collection')
    stroke_type_option.set('name', 'type')
    
    # Main layer (second layer, pass 1)
    main_layer = etree.SubElement(symbol, 'layer')
    main_layer.set('pass', '1')
    main_layer.set('enabled', '1')
    main_layer.set('class', 'SimpleLine')
    main_layer.set('locked', '0')
    
    main_option = etree.SubElement(main_layer, 'Option')
    main_option.set('type', 'Map')
    
    # Main layer properties
    main_width = stroke_width * main_width_ratio
    main_props = {
        'align_dash_pattern': '0',
        'capstyle': 'round',
        'customdash': '5;2',
        'customdash_map_unit_scale': '3x:0,0,0,0,0,0',
        'customdash_unit': 'MM',
        'dash_pattern_offset': '0',
        'dash_pattern_offset_map_unit_scale': '3x:0,0,0,0,0,0',
        'dash_pattern_offset_unit': 'MM',
        'draw_inside_polygon': '0',
        'joinstyle': 'round',
        'line_color': hex_to_rgb(road_info['color']),
        'line_style': 'solid',
        'line_width': f"{main_width:.5f}",
        'line_width_unit': 'MM',
        'offset': '0',
        'offset_map_unit_scale': '3x:0,0,0,0,0,0',
        'offset_unit': 'MM',
        'ring_filter': '0',
        'trim_distance_end': '0',
        'trim_distance_end_map_unit_scale': '3x:0,0,0,0,0,0',
        'trim_distance_end_unit': 'MM',
        'trim_distance_start': '0',
        'trim_distance_start_map_unit_scale': '3x:0,0,0,0,0,0',
        'trim_distance_start_unit': 'MM',
        'tweak_dash_pattern_on_corners': '0',
        'use_custom_dash': '0',
        'width_map_unit_scale': '3x:0,0,0,0,0,0'
    }
    
    for prop_name, prop_value in main_props.items():
        prop_elem = etree.SubElement(main_option, 'Option')
        prop_elem.set('type', 'QString')
        prop_elem.set('value', prop_value)
        prop_elem.set('name', prop_name)
    
    # Main layer data defined properties
    main_data_props = etree.SubElement(main_layer, 'data_defined_properties')
    main_option_elem = etree.SubElement(main_data_props, 'Option')
    main_option_elem.set('type', 'Map')
    
    main_name_option = etree.SubElement(main_option_elem, 'Option')
    main_name_option.set('type', 'QString')
    main_name_option.set('value', '')
    main_name_option.set('name', 'name')
    
    main_props_option = etree.SubElement(main_option_elem, 'Option')
    main_props_option.set('name', 'properties')
    
    main_type_option = etree.SubElement(main_option_elem, 'Option')
    main_type_option.set('type', 'QString')
    main_type_option.set('value', 'collection')
    main_type_option.set('name', 'type')
    
    return symbol

def generate_qgis_style(osmand_xml_path, output_path):
    """Generate QGIS style XML from OsmAnd rendering XML."""
    
    # Parse OsmAnd XML
    tree = etree.parse(osmand_xml_path)
    root = tree.getroot()
    
    # Extract color definitions
    color_definitions = extract_color_definitions(root)
    print(f"Found {len(color_definitions)} color definitions")
    
    # Extract road information
    roads = extract_road_info(root, color_definitions)
    print(f"Found {len(roads)} road types")
    
    # Create QGIS style XML
    qgis_style = etree.Element('qgis_style')
    qgis_style.set('version', '2')
    
    # Add DOCTYPE
    doctype = '<!DOCTYPE qgis_style>'
    
    symbols = etree.SubElement(qgis_style, 'symbols')
    
    # Generate symbols for each road type
    for road in roads:
        print(f"Creating symbol for: {road['symbol_name']} ({road['color']}) width: {road['stroke_width']}")
        
        symbol = create_qgis_symbol(road)
        symbols.append(symbol)
    
    # Add empty sections
    colorramps = etree.SubElement(qgis_style, 'colorramps')
    textformats = etree.SubElement(qgis_style, 'textformats')
    labelsettings = etree.SubElement(qgis_style, 'labelsettings')
    legendpatchshapes = etree.SubElement(qgis_style, 'legendpatchshapes')
    symbols3d = etree.SubElement(qgis_style, 'symbols3d')
    
    # Write to file
    with open(output_path, 'wb') as f:
        f.write(doctype.encode() + b'\n')
        f.write(etree.tostring(qgis_style, pretty_print=True, xml_declaration=False, encoding='utf-8'))
    
    print(f"Generated QGIS style with {len(roads)} road symbols: {output_path}")

def main():
    osmand_xml = "OsmAnd-resources/rendering_styles/default.render.xml"
    output_xml = "styles/roads.xml"
    
    generate_qgis_style(osmand_xml, output_xml)

if __name__ == "__main__":
    main()