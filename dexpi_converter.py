import os
import uuid
from datetime import datetime
from lxml import etree as ET
from ai_integration import PnIDAIAssistant  # Import the class
from ai_integration import SmartPnIDSuggestions
class DEXPIConverter:
    def __init__(self):
        self.root = None
        self.ai_logs = []
        self.ai = PnIDAIAssistant()  # Create an instance of the assistant

    def convert(self, dsl_data):
        NSMAP = {
            None: "http://www.dexpi.org/v1.3",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xs": "http://www.w3.org/2001/XMLSchema"
        }
        self.root = ET.Element("PlantModel", nsmap=NSMAP)

        self._add_header(dsl_data.get("metadata", {}))

        topology = ET.SubElement(self.root, "PlantTopology")
        equipment = ET.SubElement(topology, "Equipment")
        for component in dsl_data.get("components", []):
            self._add_equipment(equipment, component)

        piping = ET.SubElement(topology, "PipingNetwork")
        for connection in dsl_data.get("connections", []):
            self._add_piping(piping, connection)

        loops = ET.SubElement(topology, "InstrumentationLoops")
        for loop in dsl_data.get("control_loops", []):
            self._add_control_loop(loops, loop)

        return ET.tostring(self.root, pretty_print=True, xml_declaration=True, encoding="UTF-8").decode("utf-8")

    def _add_header(self, metadata):
        header = ET.SubElement(self.root, "Header")
        project = ET.SubElement(header, "Project")
        project.set("Name", metadata.get("project", "Unnamed Project"))
        project.set("ID", str(uuid.uuid4()))

        drawing = ET.SubElement(header, "Drawing")
        drawing.set("DrawingNumber", metadata.get("drawing_number", "PID-001"))
        drawing.set("Revision", metadata.get("revision", "00"))
        drawing.set("Date", metadata.get("date", datetime.now().isoformat()))

        company = ET.SubElement(header, "Company")
        company.set("Name", metadata.get("company", "Unknown"))

        exchange = ET.SubElement(header, "Exchange")
        exchange.set("ExportDate", datetime.now().isoformat())
        exchange.set("ExportingTool", "EPS P&ID Generator")
        exchange.set("ExportingToolVersion", "2.0")

    def _add_equipment(self, parent, component):
        comp_type = component.get("type", "Equipment")
        equip = ET.SubElement(parent, comp_type)
        equip.set("ID", component.get("id", str(uuid.uuid4())))
        equip.set("TagName", component.get("tag", component.get("id", "")))
        equip.set("ComponentClass", comp_type)
        equip.set("ComponentName", component.get("attributes", {}).get("name", ""))

        # Optional layout
        if "position" in component:
            layout = ET.SubElement(equip, "Layout")
            layout.set("x", str(component["position"].get("x", 0)))
            layout.set("y", str(component["position"].get("y", 0)))

        # Generic attributes
        attributes = ET.SubElement(equip, "GenericAttributes")
        for key, value in component.get("attributes", {}).items():
            if key != "name":
                attr = ET.SubElement(attributes, "GenericAttribute")
                attr.set("Name", key)
                attr.set("Value", str(value))

        # Add AI summary + optimization suggestions
        summary = self.ai.ai_generate_summary(component)  # Use class method
        rec = self.ai.ai_suggest_recommendations(summary, goal="efficiency")  # Use class method
        self.ai_logs.append((component["id"], summary, rec))

        rec_block = ET.SubElement(equip, "AISuggestions")
        rec_block.set("Summary", summary)
        rec_block.set("Recommendation", rec)

        # Nozzles/ports
        if component.get("ports"):
            nozzles = ET.SubElement(equip, "Nozzles")
            for port in component["ports"]:
                nozzle = ET.SubElement(nozzles, "Nozzle")
                nozzle.set("ID", f"{component['id']}-{port['name']}")
                nozzle.set("Name", port["name"])
                nozzle.set("Type", port.get("type", "process"))

    def _add_piping(self, parent, connection):
        pipe = ET.SubElement(parent, "PipingSegment")
        pipe.set("ID", connection["id"])

        from_conn = ET.SubElement(pipe, "FromNode")
        from_conn.set("ID", f"{connection['from']['component']}-{connection['from']['port']}")

        to_conn = ET.SubElement(pipe, "ToNode")
        to_conn.set("ID", f"{connection['to']['component']}-{connection['to']['port']}")

        # AI-enhanced attribute suggestion
        attributes = connection.get("attributes", {})
        prompt_base = f"pipeline between {connection['from']['component']} and {connection['to']['component']}"

        diameter = attributes.get("size") or self.ai.ai_suggest_attribute(f"Typical diameter for {prompt_base}", "100")
        material = attributes.get("material") or self.ai.ai_suggest_attribute(f"Best material for {prompt_base}", "CS")
        pressure = attributes.get("design_pressure") or self.ai.ai_suggest_attribute(f"Design pressure for {prompt_base}", "1.0")
        temperature = attributes.get("design_temperature") or self.ai.ai_suggest_attribute(f"Design temperature for {prompt_base}", "25")

        spec = ET.SubElement(pipe, "PipingSpecification")
        spec.set("NominalDiameter", str(diameter))
        spec.set("Material", str(material))
        spec.set("DesignPressure", str(pressure))
        spec.set("DesignTemperature", str(temperature))

        if attributes.get("line_number"):
            line_num = ET.SubElement(pipe, "LineNumber")
            line_num.text = attributes["line_number"]

    def _add_control_loop(self, parent, loop):
        control_loop = ET.SubElement(parent, "ControlLoop")
        control_loop.set("ID", loop["id"])
        control_loop.set("Type", loop["type"])

        components = ET.SubElement(control_loop, "LoopComponents")
        for comp_id in loop["components"]:
            comp_ref = ET.SubElement(components, "ComponentReference")
            comp_ref.set("ID", comp_id)

        if loop.get("setpoint"):
            setpoint = ET.SubElement(control_loop, "Setpoint")
            setpoint.set("Value", str(loop["setpoint"]))
