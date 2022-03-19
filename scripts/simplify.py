#!/usr/bin/env python3

import sys
import getopt
import uuid
from xml.dom import minidom

element_format_rules = {
	'svg': {
		'default_styles': { },
		'allowed_attrs': ['width', 'height', 'viewBox', 'xmlns:xlink', 'xmlns:svg'],
		'element_tag': 'image'
	},
	'groups': {
		'default_styles': {
			'style': 'display:inline'
		},
		'allowed_attrs': ['id', 'transform'],
		'element_tag': 'g'
	},
	'image': {
		'default_styles': {
			'style': 'display:inline'
		},
		'allowed_attrs': ['x', 'y', 'width', 'height', 'xlink:href', 'preserveAspectRatio', 'id'],
		'element_tag': 'image',
		'id_subfix': 'image_'
	},
	'traces':{
		'default_styles': {
			'fill': 'none',
			'stroke': '#ff0000',
			'stroke-width': '1.25px',
			'stroke-linecap': 'round',
			'stroke-linejoin': 'round',
			'stroke-miterlimit': '4',
			'stroke-dasharray': 'none',
			'stroke-opacity': '1'
		},
		'allowed_attrs': ['d', 'transform', 'id'],
		'element_tag': 'path',
		'id_subfix': 'trace_'
	},
	'zones':{
		'default_styles': {
			'opacity': '0.5',
			'fill': '#00ffff',
			'stroke': '#000000',
			'stroke-width': '1px',
			'stroke-linecap': 'butt',
			'stroke-linejoin': 'miter',
			'stroke-opacity': '1'
		},
		'allowed_attrs': ['d', 'id'],
		'element_tag': 'path',
		'id_subfix': 'zone_'
	}
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

def filter_allowed_attributes(element, allowed_attrs):
	attributes = element.attributes.items()

	# Check every attributes
	for [name, value] in attributes:
		if not name in allowed_attrs:
			print('\tRemoving attribute', name)
			element.removeAttribute(name)

def format_group_elements(xml, source, ruleset):
	elements = source.getElementsByTagName(ruleset['element_tag'])

	for element in elements:
		filter_allowed_attributes(element, ruleset['allowed_attrs'])

		# Assign default style
		element.setAttribute('style', dict_to_style(ruleset['default_styles']))

		# Check if we should apply a ID to this element
		if 'id_subfix' in ruleset:
			# Check if element already has an ID assigned by the script
			id_value = element.getAttribute('id') or ''

			if not id_value.startswith(ruleset['id_subfix']):
				print('\tAdding ID to element')
				element.setAttribute('id', ruleset['id_subfix'] + str(uuid.uuid4())[:8])

		# Sort attributes
		sort_element_attr(element)

	# Sort elements
	source.childNodes.sort(key=lambda x: x.getAttribute('id'))

def remove_none_element_nodes(child_nodes):
	for node in list(child_nodes):
		if not node.nodeType == node.ELEMENT_NODE:
			node.parentNode.removeChild(node)
		else:
			remove_none_element_nodes(node.childNodes)

def main(argv):
    # Load and parse SVG
	input_xml = minidom.parse(argv[0])
	input_svg = input_xml.getElementsByTagName('svg')[0]

	# Remove none element nodes
	remove_none_element_nodes(input_xml.childNodes)

	# Format SVG element
	print('Formatting SVG tag')
	filter_allowed_attributes(input_svg, element_format_rules['svg']['allowed_attrs'])
	sort_element_attr(input_svg)

	# Format groups
	print('Formatting groups')
	format_group_elements(input_xml, input_svg, element_format_rules['groups'])

	for element in list(input_svg.childNodes):
		element_id = element.getAttribute('id')

		print('Formatting SVG child elements:', element_id)

		if element_id in ['bottom_board', 'top_board']:
			format_group_elements(input_xml, element, element_format_rules['image'])
		elif element_id in ['bottom_zones', 'top_zones']:
			format_group_elements(input_xml, element, element_format_rules['zones'])
		elif element_id in ['bottom_traces', 'top_traces']:
			format_group_elements(input_xml, element, element_format_rules['traces'])
		else:
			print('\tWARNING: Removing unknown child element', element.tagName, element_id)
			element.parentNode.removeChild(element)

	# Write out simplified SVG
	open(argv[1], 'wb').write(input_xml.toprettyxml('\t', '\n', 'UTF-8'))

if __name__ == '__main__':
	main(sys.argv[1:])
