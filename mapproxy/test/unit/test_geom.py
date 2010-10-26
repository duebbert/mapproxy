# This file is part of the MapProxy project.
# Copyright (C) 2010 Omniscale <http://omniscale.de>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division, with_statement
import os
import tempfile

from mapproxy.srs import SRS
from mapproxy.util.geom import load_polygons, transform_geometry, geom_support
from mapproxy.test.helper import TempFile

if not geom_support:
    from nose.plugins.skip import SkipTest
    raise SkipTest('requires Shapely')

import shapely

from nose.tools import eq_, raises

VALID_POLYGON1 = """POLYGON ((953296.704552185838111 7265916.626927595585585,
944916.907243740395643 7266183.505430161952972,
943803.712335807620548 7266450.200959664769471,
935361.798751499853097 7269866.750814219936728,
934743.530299633974209 7270560.353549793362617,
934743.530299633974209 7271628.176921582780778,
935794.720251194899902 7274619.979839355684817,
936567.834114754223265 7275849.767033117823303,
937959.439069160842337 7277078.402297221124172,
940062.041611264110543 7278254.31110474281013,
941948.350382756092586 7278948.856433514505625,
950513.717282353783958 7279590.533784243278205,
951905.099597778869793 7279323.193848768249154,
953976.97796042333357 7278628.807455806992948,
955337.636096389498562 7277987.20964437816292,
955646.770322322496213 7277612.74426197167486,
955894.122230865177698 7277238.489366835914552,
956759.965230255154893 7273070.375410236418247,
956790.912048695725389 7272483.464432151056826,
954255.388006897410378 7266929.622660100460052,
953760.684189812047407 7266129.1298723295331,
953296.704552185838111 7265916.626927595585585))""".replace('\n',' ')

VALID_POLYGON2 = """POLYGON ((929919.722805089084432 7252212.673410807736218, 
929393.960850072442554 7252372.056830812245607, 
928651.905124444281682 7252957.449742536991835, 
927507.763398071052507 7254289.325379111804068, 
923735.145855087204836 7261007.430086207576096, 
923394.953491222811863 7261914.35770049970597, 
923333.171173832495697 7262554.628265766426921, 
923580.523082375293598 7263621.350993251428008, 
924786.558445629663765 7266503.041579172946513, 
925281.262262714910321 7267303.380754604935646, 
928713.687441834714264 7270453.271698194555938, 
929486.801305394037627 7271041.567251891829073, 
929950.558304038597271 7271201.337567078880966, 
930414.426622174330987 7270987.157654598355293, 
935083.722663498250768 7255089.941797585226595, 
931527.621530107106082 7252531.635323006659746, 
931125.535529361688532 7252317.969672014936805, 
929919.722805089084432 7252212.673410807736218))""".replace('\n',' ')


class TestPolygonLoading(object):
    def test_loading_polygon(self):
        with TempFile() as fname:
            with open(fname, 'w') as f:
                f.write(VALID_POLYGON1)
            bbox, polygon = load_polygons(fname)
            eq_(polygon.type, 'Polygon')

    def test_loading_multipolygon(self):
        with TempFile() as fname:
            with open(fname, 'w') as f:
                f.write(VALID_POLYGON1)
                f.write('\n')
                f.write(VALID_POLYGON2)
            bbox, polygon = load_polygons(fname)
            eq_(polygon.type, 'MultiPolygon')
    
    @raises(shapely.geos.ReadingError)
    def test_loading_broken(self):
        with TempFile() as fname:
            with open(fname, 'w') as f:
                f.write("POLYGON((")
            bbox, polygon = load_polygons(fname)
    
    def test_loading_skip_non_polygon(self):
        with TempFile() as fname:
            with open(fname, 'w') as f:
                f.write("POINT(0 0)\n")
                f.write(VALID_POLYGON1)
            bbox, polygon = load_polygons(fname)
            eq_(polygon.type, 'Polygon')

class TestTransform(object):
    def test_polygon_transf(self):
        p1 = shapely.geometry.Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        
        p2 = transform_geometry(SRS(4326), SRS(900913), p1)
        assert p2.contains(shapely.geometry.Point((1000000, 1000000)))
        p3 = transform_geometry(SRS(900913), SRS(4326), p2)
        
        assert p3.symmetric_difference(p1).area < 0.00001
    
    def test_multipolygon_transf(self):
        p1 = shapely.geometry.Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        p2 = shapely.geometry.Polygon([(20, 20), (30, 20), (30, 30), (20, 30)])
        mp1 = shapely.geometry.MultiPolygon([p1, p2])
        
        mp2 = transform_geometry(SRS(4326), SRS(900913), mp1)
        assert mp2.contains(shapely.geometry.Point((1000000, 1000000)))
        assert not mp2.contains(shapely.geometry.Point((2000000, 2000000)))
        assert mp2.contains(shapely.geometry.Point((3000000, 3000000)))
        
        mp3 = transform_geometry(SRS(900913), SRS(4326), mp2)
        
        assert mp3.symmetric_difference(mp1).area < 0.00001
    
    @raises(ValueError)
    def test_invalid_transf(self):
        p = shapely.geometry.Point((0, 0))
        transform_geometry(SRS(4326), SRS(900913), p)
    
class BBOXPolygon(object):
    def test_bbox_polygon(self):
        p = bbox_polygon([5, 53, 6, 54])
        eq_(p.type, 'Polygon')
        