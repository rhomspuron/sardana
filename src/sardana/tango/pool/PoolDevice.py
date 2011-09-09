#!/usr/bin/env python

##############################################################################
##
## This file is part of Sardana
##
## http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
## 
## Sardana is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## Sardana is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
## 
## You should have received a copy of the GNU Lesser General Public License
## along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

"""Generic Tango Pool Device base classes"""

__all__ = ["PoolDevice", "PoolDeviceClass",
           "PoolElementDevice", "PoolElementDeviceClass",
           "PoolGroupDevice", "PoolGroupDeviceClass"]

__docformat__ = 'restructuredtext'

from PyTango import Util, DevVoid, DevLong, DevLong64, DevBoolean, DevString, \
    DevDouble, DevVarStringArray, DispLevel, DevState, SCALAR, SPECTRUM, \
    IMAGE, READ_WRITE, READ, AttReqType
    
from taurus.core.util import CaselessDict
#from taurus.core.util.log import DebugIt, InfoIt

from sardana.tango.core.SardanaDevice import SardanaDevice, SardanaDeviceClass
from sardana.tango.core.util import GenericScalarAttr, GenericSpectrumAttr, \
    GenericImageAttr, to_tango_type_format, to_tango_access
from sardana.pool import InvalidId, InvalidAxis

class PoolDevice(SardanaDevice):
    """Base Tango Pool Device class"""

    ExtremeErrorStates = DevState.FAULT, DevState.UNKNOWN
    BusyStates = DevState.MOVING, DevState.RUNNING

    def __init__(self, dclass, name):
        SardanaDevice.__init__(self, dclass, name)
    
    def init(self, name):
        SardanaDevice.init(self, name)
        util = Util.instance()
        self._pool_device = util.get_device_list_by_class("Pool")[0]
        self._element = None
        
    @property
    def pool_device(self):
        return self._pool_device

    @property
    def pool(self):
        return self.pool_device.pool
    
    def get_element(self):
        return self._element
    
    def set_element(self, element):
        self._element = element
    
    element = property(get_element, set_element)
    
    def set_change_events(self, evts_checked_by_tango, evts_not_checked_by_tango):
        for evt in evts_checked_by_tango:
            self.set_change_event(evt, True, True)
        for evt in evts_not_checked_by_tango:
            self.set_change_event(evt, True, False)
    
    def init_device(self):
        SardanaDevice.init_device(self)
    
    def delete_device(self):
        SardanaDevice.delete_device(self)
        self.pool.delete_element(self.element.get_name())
    
    def read_SimulationMode(self, attr):
        attr_SimulationMode_read = 1
        attr.set_value(attr_SimulationMode_read)
    
    def write_SimulationMode(self, attr):
        data=[]
        attr.get_write_value(data)
    
    def Abort(self):
        self.element.abort()
    
    def is_Abort_allowed(self):
        if self.get_state() in [DevState.UNKNOWN]:
            return False
        return True
    
    def _is_allowed(self, req_type):
        state = self.get_state()
        if state in self.ExtremeErrorStates:
            return False
        if req_type == AttReqType.WRITE_REQ:
            if state in self.BusyStates:
                return False
        return True

    def get_dynamic_attributes(self):
        return ()

    def initialize_dynamic_attributes(self):
        self._attributes = attrs = CaselessDict()
        
        dynamic_attributes = self.get_dynamic_attributes()
        
        self.remove_unwanted_dynamic_attributes()
        
        if dynamic_attributes is None or len(dynamic_attributes) == 0:
            return
        
        read = self.__class__._read_DynamicAttribute
        write = self.__class__._write_DynamicAttribute
        is_allowed = self.__class__._is_DynamicAttribute_allowed
        for k, data_info in dynamic_attributes.items():
            attr = self.add_dynamic_attribute(data_info, read, write, is_allowed)
            attrs[attr.get_name()] = None
    
    def remove_unwanted_dynamic_attributes(self):
        """Removes unwanted dynamic attributes from previous device creation"""
        
        dev_class, multi_attr = self.get_device_class(), self.get_device_attr()
        multi_class_attr = dev_class.get_class_attr()
        klass_attrs = [ attr_name.lower() for attr_name in dev_class.attr_list ]
        klass_attrs.extend(('state', 'status'))
        
        attribute_names = []
        for ind in range(multi_attr.get_attr_nb()):
            attribute_names.append(multi_attr.get_attr_by_ind(ind).get_name())
        
        for attribute_name in attribute_names:
            attribute_name_lower = attribute_name.lower()
            if attribute_name_lower in klass_attrs:
                continue
            try:
                self.remove_attribute(attribute_name)
            except Exception, e:
                self.warning("Error removing dynamic attribute %s (%s)",
                             attribute_name, e)
        
        attr_names = []
        attrs = multi_class_attr.get_attr_list()
        for ind in range(len(attrs)):
            attr_names.append(attrs[ind].get_name())
        
        for attr_name in attr_names:
            attr_name_lower = attr_name.lower()
            if attr_name_lower in klass_attrs:
                continue
            try:
                attr = multi_class_attr.get_attr(attr_name)
                multi_class_attr.remove_attr(attr_name, attr.get_cl_name())
            except Exception, e:
                self.warning("Error removing dynamic attribute %s from device "
                             "class (%s)",
                             attr_name, e)

    def add_dynamic_attribute(self, data_info, read, write, is_allowed):
        #self.info("adding dynamic attribute %s", data_info.name)
        tg_type, tg_format = to_tango_type_format(data_info.dtype,
                                                  data_info.dformat)
        tg_access = to_tango_access(data_info.access)

        if tg_access == READ:
            write = None
        klass = GenericScalarAttr
        if tg_format == SPECTRUM:
            klass = GenericSpectrumAttr
        elif tg_format == IMAGE:
            klass = GenericImageAttr
            
        attr = klass(data_info.name, tg_type, tg_access)
        if tg_access == READ_WRITE and tg_format == SCALAR:
            attr.set_memorized()
            attr.set_memorized_init(True)
        attr.set_disp_level(DispLevel.EXPERT)
        return self.add_attribute(attr, read, write, is_allowed)

    def read_DynamicAttribute(self, attr):
        raise NotImplementedError

    def write_DynamicAttribute(self, attr):
        raise NotImplementedError

    def is_DynamicAttribute_allowed(self, req_type):
        return self._is_allowed(req_type)
    
    def _read_DynamicAttribute(self, attr):
        name = attr.get_name()
        
        read_name = "read_" + name
        if hasattr(self, read_name):
            read = getattr(self, read_name)
            return read(attr)
        
        return self.read_DynamicAttribute(attr)
    
    def _write_DynamicAttribute(self, attr):
        name = attr.get_name()

        write_name = "write_" + name
        if hasattr(self, write_name):
            write = getattr(self, write_name)
            return write(attr)
        
        return self.write_DynamicAttribute(attr)

    def _is_DynamicAttribute_allowed(self, req_type):
        return self.is_DynamicAttribute_allowed(req_type)


class PoolDeviceClass(SardanaDeviceClass):
    """Base Tango Pool Device Class class"""
    
    #    Class Properties
    class_property_list = SardanaDeviceClass.class_property_list

    #    Device Properties
    device_property_list = {
        'Id': [DevLong64, "Internal ID", [ InvalidId ] ],
    }
    device_property_list.update(SardanaDeviceClass.device_property_list)
    
    #    Command definitions
    cmd_list = {
        'Abort': [ [DevVoid, ""], [DevVoid, ""] ]
    }
    cmd_list.update(SardanaDeviceClass.cmd_list)

    #    Attribute definitions
    attr_list = {
        'SimulationMode': [ [DevBoolean, SCALAR, READ_WRITE],
                          { 'label'         : "Simulation mode" } ],
    }
    attr_list.update(SardanaDeviceClass.attr_list)


class PoolElementDevice(PoolDevice):
    """Base Tango Pool Element Device class"""
    
    def init_device(self):
        PoolDevice.init_device(self)
        self.instrument = None
        self.ctrl = None
        try:
            instrument_id = int(self.Instrument_id)
            if instrument_id != InvalidId:
                instrument = self.pool.get_element_by_id(instrument_id)
                self.instrument = instrument
        except ValueError:
            pass
        try:
            ctrl_id = int(self.Ctrl_id)
            if ctrl_id != InvalidId:
                ctrl = self.pool.get_element_by_id(ctrl_id)
                self.ctrl = ctrl
        except ValueError:
            pass
            
    def read_Instrument(self, attr):
        instrument = self.element.instrument
        if instrument is None:
            attr.set_value('')
        else:
            attr.set_value(instrument.full_name)
    
    def write_Instrument(self, attr):
        name = attr.get_write_value()
        instrument = None
        if name:
            instrument = self.pool.get_element(full_name=name)
            if instrument.get_type() != ElementType.Instrument:
                raise Exception("%s is not an instrument" % name)
        self.element.instrument = instrument
        db = PyTango.Util.instance().get_database()
        db.put_device_property(self.get_name(), { "Instrument_id" : instrument.id })
    
    def get_dynamic_attributes(self):
        ctrl = self.ctrl
        if ctrl is None:
            self.debug("no controller: dynamic attributes NOT created")
            return
        ctrl_info = ctrl.get_ctrl_info()
        if ctrl_info is None:
            self.debug("no controller info: dynamic attributes NOT created")
            return
        return ctrl_info.getAxisAttributes()

    def read_DynamicAttribute(self, attr):
        name = attr.get_name()
        ctrl = self.ctrl
        if ctrl is None:
            raise Exception("Cannot read %s. Controller not build!" % name)
        v = ctrl.get_axis_attr(self.element.axis, name)
        if v is None:
            raise Exception("Cannot read %s. Controller returns %s" % (name, v))
        attr.set_value(v)

    def write_DynamicAttribute(self, attr):
        name = attr.get_name()
        value = attr.get_write_value()
        self.info("writting dynamic attribute %s with value %s", name, value)
        ctrl = self.ctrl
        if ctrl is None:
            raise Exception("Cannot write %s. Controller not build!" % name)
        ctrl.set_axis_attr(self.element.axis, name, value)


class PoolElementDeviceClass(PoolDeviceClass):
    """Base Tango Pool Element Device Class class"""
    
    #    Class Properties
    class_property_list = PoolDeviceClass.class_property_list

    #    Device Properties
    device_property_list = {
        "Axis"          : [ DevLong64, "Axis in the controller", [ InvalidAxis ] ],
        "Ctrl_id"       : [ DevLong64, "Controller ID", [ InvalidId ] ],
        "Instrument_id" : [ DevLong64, "Controller ID", [ InvalidId ] ],
    }
    device_property_list.update(PoolDeviceClass.device_property_list)
    
    #    Attribute definitions
    attr_list = {
        'Instrument' :    [ [DevString, SCALAR, READ_WRITE],
                          { 'label'         : "Instrument",
                            'Display level' : DispLevel.EXPERT } ],
    }
    attr_list.update(PoolDeviceClass.attr_list)

    standard_attr_list = {}
    
    def get_standard_attr_info(self, attr):
        return self.standard_attr_list[attr]
    

class PoolGroupDevice(PoolDevice):
    """Base Tango Pool Group Device class"""
    
    def read_ElementList(self, attr):
        attr.set_value(self.get_element_names())

    def get_element_names(self):
        elements = self.element.get_user_elements()
        return [ element.name for element in elements ]
    
    def elements_changed(self, evt_src, evt_type, evt_value):
        self.push_change_event("ElementList", self.get_element_names())
    

class PoolGroupDeviceClass(PoolDeviceClass):
    """Base Tango Pool Group Device Class class"""
    
    #    Class Properties
    class_property_list = {
    }

    #    Device Properties
    device_property_list = {
        "Elements" :    [ DevVarStringArray, "elements in the group", [ ] ],
    }
    device_property_list.update(PoolDeviceClass.device_property_list)

    #    Command definitions
    cmd_list = {
    }
    cmd_list.update(PoolDeviceClass.cmd_list)

    #    Attribute definitions
    attr_list = {
        'ElementList'  : [ [ DevString, SPECTRUM, READ, 4096] ],
    }
    attr_list.update(PoolDeviceClass.attr_list)

    def __init__(self, name):
        PoolDeviceClass.__init__(self, name)
        self.set_type(name)

    def init_device(self):
        PoolDevice.init_device(self)