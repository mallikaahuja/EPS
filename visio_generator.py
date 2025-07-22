"""
Microsoft Visio P&ID Generator using lxml
Generates Visio diagrams from DEXPI XML with HITL support
"""

import os
import win32com.client
from lxml import etree as ET


class VisioP_IDGenerator:
    def __init__(self):
        try:
            self.visio = win32com.client.Dispatch("Visio.Application")
            self.visio.Visible = True
            self.doc = None
            self.page = None
            self.shape_map = {}

            self.stencil_paths = {
                "process": "PIDEQP_M.VSS",
                "piping": "PIDPIP_M.VSS",
                "instruments": "PIDINS_M.VSS",
                "valves": "PIDVAL_M.VSS"
            }
        except Exception as e:
            raise Exception(f"Failed to initialize Visio: {str(e)}")

    def create_new_drawing(self, template="BASICD_M.VST"):
        self.doc = self.visio.Documents.Add(template)
        self.page = self.doc.Pages(1)
        self.page.PageSheet.CellsU("PageWidth").FormulaU = "841 mm"
        self.page.PageSheet.CellsU("PageHeight").FormulaU = "594 mm"
        self._load_stencils()
        return self.doc

    def _load_stencils(self):
        stencil_folder = self._get_stencil_folder()
        for name, filename in self.stencil_paths.items():
            try:
                stencil_path = os.path.join(stencil_folder, filename)
                if os.path.exists(stencil_path):
                    self.visio.Documents.OpenEx(
                        stencil_path,
                        win32com.client.constants.visOpenDocked |
                        win32com.client.constants.visOpenRO
                    )
            except Exception as e:
                print(f"Warning: Could not load stencil {filename}: {str(e)}")

    def _get_stencil_folder(self):
        visio_paths = [
            r"C:\Program Files\Microsoft Office\root\Office16\Visio Content\1033",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\Visio Content\1033",
            os.path.join(os.environ.get("PROGRAMFILES", ""), "Microsoft Office", "root", "Office16", "Visio Content", "1033")
        ]
        for path in visio_paths:
            if os.path.exists(path):
                return path
        return os.getcwd()

    def import_from_dexpi(self, dexpi_file: str):
        parser = ET.XMLParser(remove_blank_text=True)
        tree = ET.parse(dexpi_file, parser)
        root = tree.getroot()
        ns = {'dexpi': 'http://www.dexpi.org/v1.3'}

        for equip in root.xpath('.//dexpi:Equipment/*', namespaces=ns):
            self._add_equipment(equip)

        for pipe in root.xpath('.//dexpi:PipingNetwork/dexpi:PipingSegment', namespaces=ns):
            self._add_pipe(pipe)

        for loop in root.xpath('.//dexpi:InstrumentationLoops/dexpi:ControlLoop', namespaces=ns):
            self._add_control_loop(loop)

        self._auto_layout()

    def _add_equipment(self, equip_elem: ET.ElementBase):
        equip_id = equip_elem.get('ID')
        equip_type = ET.QName(equip_elem.tag).localname
        tag_name = equip_elem.get('TagName', equip_id)

        shape_mapping = {
            'CentrifugalPump': 'Centrifugal pump',
            'Vessel': 'Vessel',
            'HeatExchanger': 'Heat exchanger 1',
            'Valve': 'Gate valve',
            'Filter': 'Filter',
            'Instrument': 'Indicator'
        }

        master_name = shape_mapping.get(equip_type, 'Process')

        try:
            master = self._find_master(master_name)
            if master:
                shape = self.page.Drop(master, 2, 2)
                shape.Text = tag_name
                self.shape_map[equip_id] = shape
                self._add_shape_properties(shape, equip_elem)
        except Exception as e:
            print(f"Error adding equipment {equip_id}: {str(e)}")

    def _add_pipe(self, pipe_elem: ET.ElementBase):
        pipe_id = pipe_elem.get('ID')
        from_node = pipe_elem.find('.//FromNode')
        to_node = pipe_elem.find('.//ToNode')

        if from_node is not None and to_node is not None:
            from_id = from_node.get('ID').split('-')[0]
            to_id = to_node.get('ID').split('-')[0]

            from_shape = self.shape_map.get(from_id)
            to_shape = self.shape_map.get(to_id)

            if from_shape and to_shape:
                connector = self.page.DrawLine(0, 0, 1, 1)
                connector.CellsU("LinePattern").FormulaU = "1"
                connector.CellsU("LineWeight").FormulaU = "2 pt"
                connector.CellsU("BeginX").GlueTo(from_shape.CellsU("PinX"))
                connector.CellsU("EndX").GlueTo(to_shape.CellsU("PinX"))
                line_num = pipe_elem.find('.//LineNumber')
                if line_num is not None and line_num.text:
                    connector.Text = line_num.text

    def _add_control_loop(self, loop_elem: ET.ElementBase):
        components = loop_elem.findall('.//ComponentReference')
        if len(components) >= 2:
            for i in range(len(components) - 1):
                from_id = components[i].get('ID')
                to_id = components[i + 1].get('ID')
                from_shape = self.shape_map.get(from_id)
                to_shape = self.shape_map.get(to_id)
                if from_shape and to_shape:
                    signal = self.page.DrawLine(0, 0, 1, 1)
                    signal.CellsU("LinePattern").FormulaU = "2"
                    signal.CellsU("LineColor").FormulaU = "RGB(0,0,255)"
                    signal.CellsU("BeginX").GlueTo(from_shape.CellsU("PinX"))
                    signal.CellsU("EndX").GlueTo(to_shape.CellsU("PinX"))

    def _find_master(self, master_name: str):
        for doc in self.visio.Documents:
            try:
                for master in doc.Masters:
                    if master_name.lower() in master.Name.lower():
                        return master
            except:
                continue
        return None

    def _add_shape_properties(self, shape, equip_elem: ET.ElementBase):
        attributes = equip_elem.find('.//GenericAttributes')
        if attributes is not None:
            for attr in attributes.findall('GenericAttribute'):
                name = attr.get('Name')
                value = attr.get('Value')
                try:
                    shape.AddNamedRow(243, name, 0)
                    shape.CellsU(f"Prop.{name}").FormulaU = f'"{value}"'
                except:
                    pass

    def _auto_layout(self):
        try:
            self.page.Layout()
            layout_options = self.page.PageSheet
            layout_options.CellsU("PlaceStyle").FormulaU = "6"
            layout_options.CellsU("RouteStyle").FormulaU = "1"
            self.page.Layout()
        except Exception as e:
            print(f"Auto-layout error: {str(e)}")

    def save_as(self, filename: str):
        self.doc.SaveAs(filename)

    def close(self):
        if self.doc:
            self.doc.Close()
        self.visio.Quit()
