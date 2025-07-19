"""
AI Integration Module for P&ID Generator
Includes OpenAI suggestions and Stability AI symbol generation
"""

import os
import openai
import requests
import base64
from PIL import Image
from io import BytesIO
import json

class PnIDAIAssistant:
    """AI-powered assistant for P&ID improvements and suggestions"""

    def __init__(self, openai_key=None, stability_key=None):
        self.openai_key = openai_key or os.getenv("OPENAI_API_KEY")
        self.stability_key = stability_key or os.getenv("STABILITY_API_KEY")
        
        if self.openai_key:
            openai.api_key = self.openai_key

    def get_process_suggestions(self, equipment_df, pipeline_df, process_description=""):
        """Get AI suggestions for process improvements"""
        if not self.openai_key:
            return {"error": "OpenAI API key not configured"}
        
        # Build context from current P&ID
        equipment_list = equipment_df['Description'].tolist()
        equipment_types = equipment_df['type'].tolist()
        
        prompt = f"""
As a process engineering expert, analyze this P&ID configuration and provide improvement suggestions:

Current Equipment: {', '.join(equipment_list)}
Equipment Types: {', '.join(equipment_types)}
Process Description: {process_description}

Please provide:
1. Safety improvements or missing safety devices
2. Efficiency optimization suggestions
3. Missing instrumentation or control loops
4. Environmental compliance recommendations
5. Cost-saving opportunities

Format your response as a JSON object with categories as keys.
"""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert process engineer specializing in vacuum systems and P&ID design."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            suggestions = response.choices[0].message.content
            return json.loads(suggestions)
        except Exception as e:
            return {"error": f"Failed to get suggestions: {str(e)}"}

    def validate_process_flow(self, equipment_sequence, pipeline_connections):
        """Validate the process flow logic using AI"""
        if not self.openai_key:
            return {"valid": True, "issues": []}
        
        prompt = f"""
Validate this vacuum system process flow sequence:

Equipment sequence: {equipment_sequence}
Connections: {pipeline_connections}

Check for:
1. Logical flow sequence
2. Missing components
3. Safety concerns
4. Efficiency issues

Return a JSON object with:
- valid: boolean
- issues: list of issues found
- recommendations: list of improvements
"""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a vacuum system design expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"valid": True, "issues": [], "error": str(e)}

    def generate_missing_symbol(self, component_name, component_type, isa_standard=True):
        """Generate missing P&ID symbols using Stability AI"""
        if not self.stability_key:
            return None
        
        # Build prompt for symbol generation
        prompt = f"""
Create a professional P&ID symbol for: {component_name}
Type: {component_type}
Style: ISA standard industrial symbol, black and white line drawing
Requirements:
- Simple line art, no shading
- Clear geometric shapes
- Standard P&ID conventions
- Transparent background
- Square aspect ratio
"""
        
        try:
            response = requests.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self.stability_key}"
                },
                json={
                    "text_prompts": [
                        {
                            "text": prompt,
                            "weight": 1
                        }
                    ],
                    "cfg_scale": 7,
                    "height": 512,
                    "width": 512,
                    "samples": 1,
                    "steps": 30,
                    "style_preset": "line-art"
                }
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            image_data = base64.b64decode(data["artifacts"][0]["base64"])
            
            # Process image to ensure it's suitable for P&ID
            img = Image.open(BytesIO(image_data))
            
            # Convert to black and white with transparency
            img = img.convert("RGBA")
            
            # Make white pixels transparent
            datas = img.getdata()
            newData = []
            for item in datas:
                if item[0] > 200 and item[1] > 200 and item[2] > 200:
                    newData.append((255, 255, 255, 0))
                else:
                    newData.append(item)
            
            img.putdata(newData)
            
            # Resize to standard symbol size
            img = img.resize((100, 100), Image.Resampling.LANCZOS)
            
            # Save to symbols directory
            symbol_path = f"symbols/{component_type.lower().replace(' ', '_')}.png"
            img.save(symbol_path, "PNG")
            
            return symbol_path
            
        except Exception as e:
            print(f"Failed to generate symbol: {str(e)}")
            return None

    def optimize_layout(self, positions, pipelines):
        """Use AI to suggest optimal equipment layout"""
        if not self.openai_key:
            return positions
        
        prompt = f"""
Optimize this P&ID equipment layout for:
1. Minimal pipe crossings
2. Logical flow direction (left to right)
3. Grouped by function
4. Safety separation distances

Current positions: {json.dumps(positions)}

Return optimized positions as JSON maintaining the same format.
"""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a P&ID layout optimization expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            return json.loads(response.choices[0].message.content)
        except:
            return positions

    def generate_equipment_datasheet(self, equipment_id, equipment_data):
        """Generate detailed equipment datasheet using AI"""
        if not self.openai_key:
            return {}
        
        prompt = f"""
Generate a professional equipment datasheet for:
Equipment: {equipment_data.get('name')}
Type: {equipment_data.get('type')}
Service: Vacuum system application

Include:
1. Design conditions (pressure, temperature)
2. Materials of construction
3. Key dimensions
4. Performance parameters
5. Utility requirements
6. Maintenance requirements

Format as JSON with proper engineering units.
"""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a mechanical engineer creating equipment datasheets."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"error": str(e)}

    def check_compliance(self, pnid_data, standards=["ISA", "ISO", "ANSI"]):
        """Check P&ID compliance with industry standards"""
        if not self.openai_key:
            return {"compliant": True, "issues": []}
        
        prompt = f"""
Check this P&ID data for compliance with {', '.join(standards)} standards:

Equipment: {pnid_data.get('equipment', [])}
Line sizing: {pnid_data.get('line_sizes', [])}
Instrumentation: {pnid_data.get('instruments', [])}

Check for:
1. Proper symbol usage
2. Correct tagging format
3. Line numbering conventions
4. Safety device requirements
5. Instrumentation standards

Return compliance report as JSON.
"""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a P&ID standards compliance expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=600
            )
            
            return json.loads(response.choices[0].message.content)
        except:
            return {"compliant": True, "issues": []}


class SmartPnIDSuggestions:
    """Context-aware suggestions for P&ID improvements"""

    def __init__(self, ai_assistant):
        self.ai = ai_assistant
        
    def suggest_missing_components(self, process_type, existing_equipment):
        """Suggest missing components based on process type"""
        
        standard_requirements = {
            "vacuum_system": {
                "safety": ["pressure_relief_valve", "flame_arrestor", "rupture_disk"],
                "instrumentation": ["pressure_transmitter", "temperature_gauge", "flow_meter"],
                "utilities": ["cooling_water", "nitrogen_purge", "drain_system"],
                "environmental": ["scrubber", "condenser", "vapor_recovery"]
            }
        }
        
        suggestions = []
        requirements = standard_requirements.get(process_type, {})
        
        for category, items in requirements.items():
            for item in items:
                # Check if item exists in current equipment
                if not any(item in str(eq).lower() for eq in existing_equipment):
                    suggestions.append({
                        "category": category,
                        "component": item,
                        "priority": "high" if category == "safety" else "medium",
                        "reason": f"Standard {category} requirement for {process_type}"
                    })
        
        return suggestions

    def analyze_energy_efficiency(self, equipment_df, pipeline_df):
        """Analyze system for energy efficiency improvements"""
        
        suggestions = []
        
        # Check for VFD on pumps
        pumps = equipment_df[equipment_df['type'].str.contains('pump', case=False)]
        for _, pump in pumps.iterrows():
            if 'vfd' not in str(pump.get('default_properties', '')).lower():
                suggestions.append({
                    "equipment": pump['ID'],
                    "suggestion": "Add Variable Frequency Drive (VFD)",
                    "savings": "15-30% energy reduction",
                    "cost": "$5,000-$15,000"
                })
        
        # Check for heat recovery
        condensers = equipment_df[equipment_df['type'].str.contains('condenser', case=False)]
        if len(condensers) > 1:
            suggestions.append({
                "system": "Heat Recovery",
                "suggestion": "Integrate heat recovery between condensers",
                "savings": "10-20% cooling water reduction",
                "cost": "$10,000-$25,000"
            })
        
        return suggestions
