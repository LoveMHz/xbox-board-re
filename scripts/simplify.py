#!/usr/bin/python3

import sys
import getopt
import uuid
from xml.dom import minidom

default_svg_attrs = {
	'xmlns:cc': 'http://creativecommons.org/ns#',
	'xmlns:dc': 'http://purl.org/dc/elements/1.1/',
	'xmlns:inkscape': 'http://www.inkscape.org/namespaces/inkscape',
	'xmlns:pcbre': 'https://github.com/LoveMHz/xbox-board-re/namespaces/inkscape',
	'xmlns:rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
	'xmlns:sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd',
	'xmlns:svg': 'http://www.w3.org/2000/svg',
	'xmlns:xlink': 'http://www.w3.org/1999/xlink'
}
default_layer_attrs = {
	'inkscape:groupmode': 'layer',
	'sodipodi': 'true', # Force layer locked by default
}

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

default_zone_label = 'Copper Fill'

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

def process_image_layer(xml, layer, new_layer):
	images = layer.getElementsByTagName('image')

	image_allowed_attrs = ['x', 'y', 'width', 'height', 'xlink:href', 'preserveAspectRatio']
	for image in images:
		new_image = xml.createElement('image')

		# Recreate each allowed attribute in the newly created element
		for allowed_attr in image_allowed_attrs:
			# Check if field has a value
			if not image.getAttribute(allowed_attr):
				continue

			new_image.setAttribute(allowed_attr, image.getAttribute(allowed_attr))

		# Assign default image style
		new_image.setAttribute('style', dict_to_style(default_image_style))

		# Add UUID if needed
		if not new_image.getAttribute('pcbre:uuid'):
			new_image.setAttribute('pcbre:uuid', str(uuid.uuid4()))

		# Sort attributes
		sort_element_attr(new_image)

		new_layer.appendChild(new_image)

	# Sort elements
	new_layer.childNodes.sort(key=lambda x: x.getAttribute('pcbre:uuid'))

def process_zones_layer(xml, layer, new_layer):
	zones = layer.getElementsByTagName('path')

	trace_allowed_attrs = ['d', 'transform', 'inkscape:connector-curvature', 'inkscape:label', 'pcbre:uuid']
	for zone in zones:
		new_zone = xml.createElement('path')

		# Recreate each allowed attribute in the newly created element
		for allowed_attr in trace_allowed_attrs:
			# Check if field has a value
			if not zone.getAttribute(allowed_attr):
				continue

			new_zone.setAttribute(allowed_attr, zone.getAttribute(allowed_attr))

		# TODO: Remove transforms

		# Assign default zone style
		new_zone.setAttribute('style', dict_to_style(default_zone_style))

		# Assign default zone label
		if not new_zone.getAttribute('inkscape:label'):
			new_zone.setAttribute('inkscape:label', default_zone_label)

		# Add UUID if needed
		if not new_zone.getAttribute('pcbre:uuid'):
			new_zone.setAttribute('pcbre:uuid', str(uuid.uuid4()))

		# Sort attributes
		sort_element_attr(new_zone)

		new_layer.appendChild(new_zone)

	# Sort elements
	new_layer.childNodes.sort(key=lambda x: x.getAttribute('pcbre:uuid'))

def process_traces_layer(xml, layer, new_layer):
	traces = layer.getElementsByTagName('path')

	trace_allowed_attrs = ['d', 'inkscape:connector-curvature', 'pcbre:uuid']
	for trace in traces:
		new_trace = xml.createElement('path')

		# Recreate each allowed attribute in the newly created element
		for allowed_attr in trace_allowed_attrs:
			# Check if field has a value
			if not trace.getAttribute(allowed_attr):
				continue

			new_trace.setAttribute(allowed_attr, trace.getAttribute(allowed_attr))

		# Assign default trace style
		new_trace.setAttribute('style', dict_to_style(default_trace_style))

		# Add UUID if needed
		if not new_trace.getAttribute('pcbre:uuid'):
			new_trace.setAttribute('pcbre:uuid', str(uuid.uuid4()))

		# Sort attributes
		sort_element_attr(new_trace)

		new_layer.appendChild(new_trace)

	# Sort elements
	new_layer.childNodes.sort(key=lambda x: x.getAttribute('pcbre:uuid'))

def main(argv):
    # Load and parse SVG
	input_xml = minidom.parse(argv[0])
	input_svg = input_xml.getElementsByTagName('svg')[0]

	# Get 'layers' from SVG
	layers = []

	for element in input_xml.getElementsByTagName('g'):
		# Sanity check
		if element.getAttribute('inkscape:groupmode') != 'layer':
			raise Exception('None layer groups are not supported at this time!')

		if not element.getAttribute('pcbre:uuid'):
			print('WARNING: No UUID assigned to layer. Skipping layer', element.getAttribute('inkscape:label'))
			continue

		layers += [element]

	# Sort layers
	layers.sort(key=lambda x: x.getAttribute('pcbre:uuid'))

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
	layer_allowed_attrs = ['inkscape:label', 'transform', 'pcbre:uuid']
	for layer in layers:
		print('Processsing layer:', layer.getAttribute('inkscape:label'))

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

		# Add UUID if needed
		if not element.getAttribute('pcbre:uuid'):
			element.setAttribute('pcbre:uuid', str(uuid.uuid4()))

		# Sort attributes
		sort_element_attr(new_layer)

		# Sub elements of current layer
		if layer.getAttribute('inkscape:label') in ['Board Bottom', 'Board Top']:
			process_image_layer(clean_xml, layer, new_layer)
		elif layer.getAttribute('inkscape:label') in ['Bottom Zones', 'Top Zones']:
			process_zones_layer(clean_xml, layer, new_layer)
		elif layer.getAttribute('inkscape:label') in ['Top Traces', 'Bottom Traces']:
			process_traces_layer(clean_xml, layer, new_layer)

		#
		clean_svg.appendChild(new_layer)

	# Append SVG object to the document
	clean_xml.appendChild(clean_svg)

	# Write out simplified SVG
	open(argv[0], 'wb').write(clean_xml.toprettyxml('\t', '\n', 'UTF-8'))

if __name__ == '__main__':
	main(sys.argv[1:])
