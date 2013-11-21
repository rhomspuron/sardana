#!/usr/bin/env python

#############################################################################
##
## This file is part of Taurus, a Tango User Interface Library
## 
## http://www.tango-controls.org/static/taurus/latest/doc/html/index.html
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
## 
## Taurus is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## Taurus is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
## 
## You should have received a copy of the GNU Lesser General Public License
## along with Taurus.  If not, see <http://www.gnu.org/licenses/>.
##
#############################################################################

"""
guiqwt widgets plugins for Qt Designer
"""

try:
    from guiqwt.qtdesigner import create_qtdesigner_plugin
    PlotPlugin = create_qtdesigner_plugin("guiqwt", "guiqwt.plot", "CurveWidget",
                                      icon="curve.png")

    ImagePlotPlugin = create_qtdesigner_plugin("guiqwt", "guiqwt.plot", "ImageWidget",
                                      icon="image.png")
except ImportError:
    from taurus.core.util.log import debug
    debug("failed to load guiqwt designer plugin")