#!/usr/bin/env python3

import sys
import getopt
import shapely.geometry
from svg.path import parse_path as parse_svg_path
from svg.path import Path as SvgPath
from svg.path import Move as SvgMove
from svg.path import Line as SvgLine
from svg.path import Close as SvgClose
from svg.path import CubicBezier as SvgCubicBezier
from svg.path import Arc as SvgArc
from xml.dom import minidom

stroke_width = 1.25

#FIXME:
width="2222.5mm"
height="2470.1499mm"
viewBox="0 0 2222.5 2470.1499"

def get_svg_polygons(xml):
	polygons = {}

	# Process traces
	elements = xml.getElementsByTagName("path")
	for element in elements:
		element_id = element.getAttribute('id')

		print('Parsing SVG child elements:', element_id)

		element_d = element.getAttribute('d')
		element_d_segments = parse_svg_path(element_d)

		nodes = []
		for segment in element_d_segments:
			#print(segment)
			if isinstance(segment, SvgMove):
				nodes.append(segment.end)
			elif isinstance(segment, SvgLine) or isinstance(segment, SvgClose):
				nodes.append(segment.end)
			elif isinstance(segment, SvgCubicBezier):
				#FIXME: Warn especially if it's very straight?
				print("warning: %s uses bezier curve; should not be used!" % element_id)
				steps = 5
				for step in range(steps):
					t = (step + 1) / steps
					nodes.append(segment.point(t))
			elif isinstance(segment, SvgArc):
				print("Unsupported arc!")
				assert(False)
				nodes = []
				break
			else:
				assert(False)

		# Create a new SVG
		if len(nodes) >= 2:

			# Turn nodes into tuples
			nodes = [(node.real, node.imag) for node in nodes]

			line_string = shapely.geometry.LineString(nodes)
			line_string_polygon = line_string.buffer(stroke_width/2.0, resolution=4)

			polygons[element_id] = line_string_polygon

		else:
			print("Not enough nodes in path")

	return polygons

def append_svg_polygons(xml, parent, polygons, style):
	result = []
	for polygon_id, polygon in polygons.items():

		if isinstance(polygon, shapely.geometry.MultiPolygon):
			multi_polygon = polygon

			clean_paths = []
			for i, polygon in enumerate(multi_polygon):
				clean_path = append_svg_polygons(xml, parent, [{"%s[%d]" % (polygon_id, i): polygon}], style)
				assert(len(clean_path) == 1)
				clean_paths.append(clean_path[0])

			result.append(clean_paths)

			continue

		path = SvgPath()
		assert(len(polygon.interiors) == 0)
		for coord in polygon.exterior.coords:
			if len(path) == 0:
				path.append(SvgMove(complex(*coord)))
			else:
				path.append(SvgLine(path[-1].end, complex(*coord)))

		clean_path = xml.createElement("path")
		clean_path.setAttribute('id', polygon_id)
		clean_path.setAttribute('d', path.d())
		clean_path.setAttribute('style', style)
		parent.appendChild(clean_path)

		result.append([clean_path])

	return result

def find_group(xml, label):
	groups = xml.getElementsByTagName('g')
	for group in groups:
		if group.getAttribute('inkscape:label') == label:
			print("Found group '%s' (id: '%s')" % (label, group.getAttribute('id')))
			return group
	return None

def compare(old_polygons, new_polygons):

	duplicate = {} # Exact matches
	touching = {} # Small overlap
	conflict = {} # Large overlap
	added = [] # No overlap, exists only in new

	# Compare
	for new_element_id, new_polygon in new_polygons.items():
		print('Processing SVG child elements:', new_element_id)

		overlaps = {}

		polygon = new_polygon
		for old_element_id, old_polygon in old_polygons.items():

			if not new_polygon.intersects(old_polygon):
				#FIXME: Get distance to check if someone might have left an accidental gap, or moved too close
				pass
			else:
				# Reject, if this is the exact same shape
				if new_polygon.equals(old_polygon): #FIXME: almost_equals?
					print("warning: %s is a duplicate (equals existing %s)" % (new_element_id, old_element_id))
					duplicate[new_element_id] = old_element_id
					continue

				# Get overlap
				overlap_polygons = new_polygon.intersection(old_polygon)

				# Ensure this is a multipolygon
				if not isinstance(overlap_polygons, shapely.geometry.MultiPolygon):
					overlap_polygons = shapely.geometry.MultiPolygon([overlap_polygons])

				# Check each overlap separately
				for overlap_polygon in overlap_polygons:
					export_overlap = False

					if overlap_polygon.area > 0:
						if overlap_polygon.area <= (stroke_width*stroke_width * 2.0):
							#FIXME: Check if this is in a pad or via; if not in pad or via: error
							print("note: Small overlap, assuming connection")
							touching[new_element_id] = old_element_id
						else:
							print("error: Large overlap")
							conflict[new_element_id] = old_element_id
							export_overlap = True

					if export_overlap:
						overlaps[old_element_id] = overlaps.get(old_element_id, []).append(overlap_polygon)

		# Check if this was newly added to keep track of it
		if new_element_id not in conflict:
			if new_element_id not in duplicate:
				added.append(new_element_id)

		#FIXME: This exports the path and its overlap
		if len(overlaps) > 0:
			diff_xml = minidom.Document()
			diff_svg = diff_xml.createElement("svg")
			diff_svg.setAttribute("viewBox", viewBox)
			diff_xml.appendChild(diff_svg)

			append_svg_polygons(diff_xml, diff_svg, {new_element_id: new_polygon}, "fill:#008800;stroke:none")
			for overlap_id, overlap_polygons in overlaps.items():
				append_svg_polygons(diff_xml, diff_svg, {new_element_id + "-diff-%s-original" % overlap_id: old_polygons[overlap_id]}, "fill:#ff0000;stroke:none")
				for i, overlap_polygon in enumerate(overlap_polygons):
					append_svg_polygons(diff_xml, diff_svg, {new_element_id + "-diff-%s-overlap[%d]" % (overlap_id, i): overlap_polygon}, "fill:#ff8800;stroke:none")

			open("tmp/%s.svg" % new_element_id, 'wb').write(diff_xml.toprettyxml('\t', '\n', 'UTF-8'))

	return duplicate, touching, conflict, added

def dump_polygons_to_svg(path, polygons):
	xml = minidom.Document()
	svg = xml.createElement("svg")
	svg.setAttribute("width", width)
	svg.setAttribute("height", height)
	svg.setAttribute("viewBox", viewBox)
	xml.appendChild(svg)

	for polygon in polygons:
		append_svg_polygons(xml, svg, polygon[0], polygon[1])

	open(path, 'wb').write(xml.toprettyxml('\t', '\n', 'UTF-8'))


def main(argv):
	# Load and parse SVGs
	old_xml = minidom.parse(argv[0])
	old_polygons = get_svg_polygons(find_group(old_xml, "Top Traces"))
	new_xml = minidom.parse(argv[1])
	new_polygons = get_svg_polygons(find_group(new_xml, "Top Traces"))

	# Re-export as polygons
	dump_polygons_to_svg("tmp/old.svg", [(old_polygons, "fill:#000000;stroke:none")])
	dump_polygons_to_svg("tmp/new.svg", [(new_polygons, "fill:#000000;stroke:none")])

	duplicate, touching, conflict, added = compare(old_polygons, new_polygons)
	_, _, _, removed = compare(new_polygons, old_polygons)

	print("\n\n\n")

	print("Added:")
	for element_id in added:
		print(element_id)
	dump_polygons_to_svg("tmp/added.svg", [(old_polygons, "fill:#aaaaaa;stroke:none"), ({element_id:new_polygons[element_id] for element_id in added}, "fill:#008800;stroke:none")])

	print("\n\n\n")

	print("Removed:")
	for element_id in removed:
		print(element_id)
	dump_polygons_to_svg("tmp/removed.svg", [(new_polygons, "fill:#aaaaaa;stroke:none"), ({element_id:old_polygons[element_id] for element_id in removed}, "fill:#ff0000;stroke:none")])


if __name__ == '__main__':
	main(sys.argv[1:])
