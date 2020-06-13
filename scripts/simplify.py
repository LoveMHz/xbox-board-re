#!/usr/bin/env python3

import sys
import getopt
import uuid
from xml.dom import minidom

default_svg_attrs = {
	'xmlns:svg': 'http://www.w3.org/2000/svg',
	'xmlns:xlink': 'http://www.w3.org/1999/xlink'
}

element_group_format_rules = {
	'image': {
		'default_styles': {
			'style': 'display:inline'
		},
		'allowed_attrs': ['x', 'y', 'width', 'height', 'xlink:href', 'preserveAspectRatio'],
		'element_tag': 'image'
	},
	'traces':{
		'default_styles': {
			'fill': 'none', 
			'stroke': '#ff0000', 
			'stroke-width': '1.25', 
			'stroke-linecap': 'round', 
			'stroke-linejoin': 'round', 
			'stroke-miterlimit': '4', 
			'stroke-dasharray': 'none', 
			'stroke-opacity': '1'
		},
		'allowed_attrs': ['d', 'transform', 'id'],
		'element_tag': 'path'
	},
	'zones':{
		'default_styles': {
			'opacity': '0.5', 
			'fill': '#00ffff', 
			'stroke': '#000000', 
			'stroke-width': '0.99999994px', 
			'stroke-linecap': 'butt', 
			'stroke-linejoin': 'miter', 
			'stroke-opacity': '1'
		},
		'allowed_attrs': ['d', 'id'],
		'element_tag': 'path'
	}
}

default_layer_attrs = { }

default_trace_style = {
	'fill': 'none', 
	'stroke': '#ff0000', 
	'stroke-width': '1.25', 
	'stroke-linecap': 'round', 
	'stroke-linejoin': 'round', 
	'stroke-miterlimit': '4', 
	'stroke-dasharray': 'none', 
	'stroke-opacity': '1'
}
default_zone_style = {
	'opacity': '0.5', 
	'fill': '#00ffff', 
	'stroke': '#000000', 
	'stroke-width': '0.99999994px', 
	'stroke-linecap': 'butt', 
	'stroke-linejoin': 'miter', 
	'stroke-opacity': '1'
}
default_image_style = {
	'style': 'display:inline'
}

def dict_to_style(dict):
	return ';'.join("{}:{}".format(key,val) for (key,val) in dict.items())

def sort_element_attr(element):
	attributes = element.attributes.items()

	# Remove attributes from element
	keys = list(element.attributes.keys()) if element.attributes else []
	for attribute in keys:
		element.removeAttribute(attribute)

	# Sort
	attributes.sort(key=lambda name: name[0])

	# Add attributes back
	for name, value in attributes:
		element.setAttribute(name, value)

def format_group_elements(xml, layer, new_layer, ruleset):
	elements = layer.getElementsByTagName(ruleset['element_tag'])

	for element in elements:
		new_element = xml.createElement(ruleset['element_tag'])

		# Recreate each allowed attribute in the newly created element
		for allowed_attr in ruleset['allowed_attrs']:
			# Check if field has a value
			if not element.getAttribute(allowed_attr):
				continue

			new_element.setAttribute(allowed_attr, element.getAttribute(allowed_attr))

		# Assign default trace style
		new_element.setAttribute('style', dict_to_style(default_trace_style))

		# Add UUID if needed
		if not new_element.getAttribute('id'):
			new_element.setAttribute('id', str(uuid.uuid4()))

		# Sort attributes
		sort_element_attr(new_element)

		new_layer.appendChild(new_element)

	# Sort elements
	new_layer.childNodes.sort(key=lambda x: x.getAttribute('id'))

def main(argv):
    # Load and parse SVG
	input_xml = minidom.parse(argv[0])
	input_svg = input_xml.getElementsByTagName('svg')[0]

	# Get 'layers' from SVG
	layers = []

	for element in input_xml.getElementsByTagName('g'):
		if not element.getAttribute('id'):
			print('WARNING: No id assigned to layer. Skipping layer', element.getAttribute('id'))
			#continue

		layers += [element]

	# Sort layers
	layers.sort(key=lambda x: x.getAttribute('id'))

	# Create our 'clean' SVG object
	clean_xml = minidom.Document()
	clean_svg = clean_xml.createElement('svg')

	# Recreate each allowed attribute
	svg_allowed_attrs = ['width', 'height', 'viewBox']
	for svg_allowed_attr in svg_allowed_attrs:
		# Check if field has a value
		if not input_svg.getAttribute(svg_allowed_attr):
			continue

		clean_svg.setAttribute(svg_allowed_attr, input_svg.getAttribute(svg_allowed_attr))

	# Set SVG default attributes
	for attribute, value in default_svg_attrs.items():
		clean_svg.setAttribute(attribute, value)

	# Sort attributes
	sort_element_attr(clean_svg)

	# Process each layer
	layer_allowed_attrs = ['id', 'transform']
	for layer in layers:
		print('Processsing layer:', layer.getAttribute('id'))

		# Create group element
		new_layer = clean_xml.createElement('g')

		# Set default attributes
		for layer_attr, value in default_layer_attrs.items():
			new_layer.setAttribute(layer_attr, value)

		# Recreate each allowed attribute in the newly created element
		for svg_allowed_attr in layer_allowed_attrs:
			# Check if field has a value
			if not layer.getAttribute(svg_allowed_attr):
				continue

			new_layer.setAttribute(svg_allowed_attr, layer.getAttribute(svg_allowed_attr))

		# Add ID if needed
		if not element.getAttribute('id'):
			element.setAttribute('id', str(uuid.uuid4()))

		# Sort attributes
		sort_element_attr(new_layer)

		# Sub elements of current layer
		layer_id = layer.getAttribute('id')
	
		if layer_id in ['bottom_board', 'top_board']:
			format_group_elements(clean_xml, layer, new_layer, element_group_format_rules['image'])
		elif layer_id in ['bottom_zones', 'top_zones']:
			format_group_elements(clean_xml, layer, new_layer, element_group_format_rules['zones'])
		elif layer_id in ['bottom_traces', 'top_traces']:
			format_group_elements(clean_xml, layer, new_layer, element_group_format_rules['traces'])

		#
		clean_svg.appendChild(new_layer)

	# Append SVG object to the document
	clean_xml.appendChild(clean_svg)

	# Write out simplified SVG
	open(argv[1], 'wb').write(clean_xml.toprettyxml('\t', '\n', 'UTF-8'))

if __name__ == '__main__':
	main(sys.argv[1:])
