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

    @staticmethod
    def ai_suggest_attribute(component_type: str, context: dict) -> str:
        """
        Suggests an attribute or tag based on component type and process context.
        """
        component_type = component_type.lower()

        if component_type in ['pump', 'motor']:
            return "Consider energy-efficient models with VFD integration"
        elif component_type in ['heat_exchanger', 'condenser']:
            return "Optimize heat transfer by monitoring ΔT regularly"
        elif component_type in ['valve', 'control_valve']:
            return "Ensure compatibility with upstream control loops"
        elif component_type in ['transmitter', 'sensor']:
            return "Place away from vibration and heat zones"
        elif component_type in ['scrubber', 'filter']:
            return "Check for differential pressure to monitor fouling"
        elif component_type in ['vessel', 'tank']:
            return "Add level and pressure indicators for better control"
        else:
            return "No specific suggestion available"

    def __init__(self, openai_key=None, stability_key=None):
        # Prioritize passed-in keys, then fall back to environment variables
        self.openai_key = openai_key if openai_key is not None else os.getenv("OPENAI_API_KEY")
        self.stability_key = stability_key if stability_key is not None else os.getenv("STABILITY_API_KEY")

        # Set OpenAI API key globally if available
        if self.openai_key:
            openai.api_key = self.openai_key
        else:
            print("Warning: OpenAI API key not found. AI features may be limited.")

        if not self.stability_key:
            print("Warning: Stability AI API key not found. Symbol generation may not work.")

    def _check_openai_key(self):
        """Internal helper to check if OpenAI key is configured."""
        if not self.openai_key:
            print("Error: OpenAI API key not configured for PnIDAIAssistant.")
            return False
        return True

    def _check_stability_key(self):
        """Internal helper to check if Stability AI key is configured."""
        if not self.stability_key:
            print("Error: Stability AI API key not configured for PnIDAIAssistant.")
            return False
        return True

    def get_process_suggestions(self, equipment_df, pipeline_df, process_description=""):
        """Get AI suggestions for process improvements"""
        if not self._check_openai_key():
            return {"error": "OpenAI API key not configured."}

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
            response = openai.chat.completions.create(
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
        except json.JSONDecodeError:
            return {"error": f"Failed to parse AI response as JSON: {suggestions}"}
        except Exception as e:
            return {"error": f"Failed to get suggestions: {str(e)}"}

    def validate_process_flow(self, equipment_sequence, pipeline_connections):
        """Validate the process flow logic using AI"""
        if not self._check_openai_key():
            return {"valid": False, "issues": ["OpenAI API key not configured."]}

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
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a vacuum system design expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {"valid": False, "issues": ["Failed to parse AI response as JSON."], "error": f"AI response: {response.choices[0].message.content}"}
        except Exception as e:
            return {"valid": False, "issues": [f"Error during validation: {str(e)}"], "error": str(e)}

    def generate_missing_symbol(self, component_name, component_type, isa_standard=True):
        """Generate missing P&ID symbols using Stability AI"""
        if not self._check_stability_key():
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
        # Ensure 'symbols' directory exists
        symbols_dir = "symbols"
        os.makedirs(symbols_dir, exist_ok=True)

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
                print(f"Stability AI API error: {response.status_code} - {response.text}")
                return None

            data = response.json()
            if not data.get("artifacts"):
                print("Stability AI did not return any artifacts (images).")
                return None

            image_data = base64.b64decode(data["artifacts"][0]["base64"])

            # Process image to ensure it's suitable for P&ID
            img = Image.open(BytesIO(image_data))

            # Convert to black and white with transparency
            img = img.convert("RGBA")

            # Make near-white pixels transparent (more robust)
            datas = img.getdata()
            newData = []
            white_threshold = 240 # Pixels with R, G, B values above this will be made transparent
            for item in datas:
                if item[0] >= white_threshold and item[1] >= white_threshold and item[2] >= white_threshold:
                    newData.append((255, 255, 255, 0)) # Fully transparent white
                else:
                    newData.append(item)

            img.putdata(newData)

            # Resize to standard symbol size
            img = img.resize((100, 100), Image.Resampling.LANCZOS)

            # Save to symbols directory
            symbol_filename = f"{component_name.lower().replace(' ', '_').replace('/', '_')}.png"
            symbol_path = os.path.join(symbols_dir, symbol_filename)
            img.save(symbol_path, "PNG")

            return symbol_path

        except Exception as e:
            print(f"Failed to generate symbol: {str(e)}")
            return None

    def optimize_layout(self, positions, pipelines):
        """Use AI to suggest optimal equipment layout"""
        if not self._check_openai_key():
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
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a P&ID layout optimization expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )

            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse AI layout optimization response as JSON. Returning original positions. AI response: {response.choices[0].message.content}")
            return positions
        except Exception as e:
            print(f"Error optimizing layout with AI: {str(e)}. Returning original positions.")
            return positions

    def generate_equipment_datasheet(self, equipment_id, equipment_data):
        """Generate detailed equipment datasheet using AI"""
        if not self._check_openai_key():
            return {"error": "OpenAI API key not configured."}

        prompt = f"""
Generate a professional equipment datasheet for:
Equipment ID: {equipment_id}
Equipment Type: {equipment_data.get('type', 'N/A')}
Equipment Description: {equipment_data.get('Description', 'N/A')}
Manufacturer: {equipment_data.get('manufacturer', 'N/A')}
Cost: ${equipment_data.get('cost_usd', 'N/A'):,.0f}
Efficiency: {equipment_data.get('efficiency_pct', 'N/A')}%
Default Properties: {equipment_data.get('default_properties', 'N/A')}

Include:
1. Design conditions (pressure, temperature, flow rates)
2. Materials of construction
3. Key dimensions (length, width, height, connection sizes)
4. Performance parameters (capacity, power consumption, efficiency)
5. Utility requirements (power, cooling, heating, air)
6. Maintenance requirements (inspection frequency, typical spare parts)
7. Safety features (e.g., relief valves, interlocks)

Format as a comprehensive JSON object with proper engineering units and clear sections.
Ensure all relevant provided data is incorporated into the datasheet.
"""

        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a mechanical engineer and process equipment specialist tasked with creating detailed datasheets. Focus on providing accurate, structured technical information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )

            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {"error": f"Failed to parse AI datasheet response as JSON: {response.choices[0].message.content}"}
        except Exception as e:
            return {"error": str(e)}

    def check_compliance(self, pnid_data, standards=["ISA", "ISO", "ANSI"]):
        """Check P&ID compliance with industry standards"""
        if not self._check_openai_key():
            return {"compliant": False, "issues": ["OpenAI API key not configured."]}

        prompt = f"""
Check this P&ID data for compliance with {', '.join(standards)} standards, focusing on common industrial practices and potential safety/operational gaps:

Equipment: {pnid_data.get('equipment', [])}
Line sizing: {pnid_data.get('line_sizes', [])}
Instrumentation: {pnid_data.get('instruments', [])}
(Assume standard process flow from left to right for general P&ID conventions unless explicitly stated)

Specifically look for:
1. Proper symbol usage (e.g., specific instrument types, valves)
2. Correct tagging format (e.g., consistent numbering, function codes)
3. Line numbering conventions (e.g., size, material, service)
4. Adequate safety device requirements (e.g., relief valves on vessels, emergency shutdowns)
5. Instrumentation standards (e.g., local vs. board mounted, control loop completeness)
6. General P&ID completeness and clarity.

Return a comprehensive compliance report as a JSON object, including:
- "compliant": boolean (overall compliance)
- "issues": list of dictionaries, each with "type" (error/warning), "description", and "recommendation"
- "suggestions": list of general improvements
"""

        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a P&ID standards compliance expert and process safety analyst. Provide clear, actionable feedback."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )

            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {"compliant": False, "issues": [{"type": "error", "description": "Failed to parse AI compliance report as JSON."}], "error": f"AI response: {response.choices[0].message.content}"}
        except Exception as e:
            return {"compliant": False, "issues": [{"type": "error", "description": f"Error during compliance check: {str(e)}"}], "error": str(e)}


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
            },
            "distillation": {
                "safety": ["relief_valve", "emergency_vent"],
                "instrumentation": ["level_transmitter", "temperature_controller", "flow_controller"],
                "utilities": ["steam_supply", "condensate_return"],
                "environmental": ["flare_system"]
            },
            "reaction": {
                "safety": ["quench_system", "rupture_disc", "emergency_stop"],
                "instrumentation": ["pH_sensor", "temperature_reactor_control", "agitator_speed_control"],
                "utilities": ["cooling_jacket", "heating_coil"],
                "environmental": ["waste_treatment"]
            }
        }

        suggestions = []
        requirements = standard_requirements.get(process_type, {})

        existing_equipment_lower = [str(eq).lower() for eq in existing_equipment]

        for category, items in requirements.items():
            for item in items:
                if not any(item.replace('_', ' ') in eq for eq in existing_equipment_lower):
                    suggestions.append({
                        "category": category,
                        "component": item.replace('_', ' ').title(),
                        "priority": "high" if category == "safety" else "medium",
                        "reason": f"Standard {category} requirement for a {process_type.replace('_', ' ')}."
                    })

        if self.ai._check_openai_key() and existing_equipment:
            try:
                ai_prompt = f"""
Given a {process_type.replace('_', ' ')} system with the following main equipment: {', '.join(existing_equipment)}.
Suggest any other critical or commonly used P&ID components that might be missing for a robust, safe, and efficient design.
Consider:
- Additional control elements (valves, transmitters, controllers)
- Safety interlocks or relief systems
- Utility connections (steam, water, air, nitrogen)
- Environmental considerations (vents, scrubbers)
- Maintenance access points or special instruments

Format your response as a JSON array of objects, where each object has 'component', 'category' (e.g., 'safety', 'instrumentation', 'utilities', 'process'), 'priority' (high/medium/low), and 'reason'. Do not include components already listed in standard_requirements unless there's a specific, additional context.
If no further suggestions, return an empty array [].
"""
                ai_response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a P&ID design expert providing intelligent, context-aware suggestions."},
                        {"role": "user", "content": ai_prompt}
                    ],
                    temperature=0.5,
                    max_tokens=300
                )
                ai_suggestions_raw = ai_response.choices[0].message.content
                ai_parsed_suggestions = json.loads(ai_suggestions_raw)

                for ai_sugg in ai_parsed_suggestions:
                    sugg_name_lower = ai_sugg.get('component', '').lower().replace(' ', '_')
                    if not any(sugg_name_lower in s['component'].lower().replace(' ', '_') for s in suggestions):
                        suggestions.append(ai_sugg)

            except Exception as e:
                print(f"Warning: AI missing component suggestion failed: {e}")

        return suggestions

    def analyze_energy_efficiency(self, equipment_df, pipeline_df, process_type):
        """Analyze system for energy efficiency improvements"""

        suggestions = []

        pumps = equipment_df[equipment_df['type'].str.contains('pump', case=False)]
        for _, pump in pumps.iterrows():
            if 'vfd' not in str(pump.get('default_properties', '')).lower() and \
               'variable frequency drive' not in str(pump.get('Description', '')).lower():
                suggestions.append({
                    "equipment": pump['ID'],
                    "suggestion": "Consider adding a Variable Frequency Drive (VFD) to the pump for optimized energy consumption based on flow demand.",
                    "savings": "Estimated 15-30% energy reduction on pump operation.",
                    "cost": "Typically $5,000-$15,000 per pump installation (varies by size)."
                })

        condensers = equipment_df[equipment_df['type'].str.contains('condenser', case=False)]
        if len(condensers) > 1:
            suggestions.append({
                "system": "Condenser Heat Recovery",
                "suggestion": "Explore integrating heat recovery between multiple condensers or using waste heat from exhaust streams to preheat incoming process fluids.",
                "savings": "Potential 10-20% reduction in cooling water demand or pre-heating utility costs.",
                "cost": "Estimated $10,000-$25,000 (varies by system complexity)."
            })

        if not pipeline_df.empty:
            if not any('insulated' in str(row).lower() for _, row in pipeline_df.iterrows()) and \
               not any('insulation' in str(row).lower() for _, row in equipment_df[
                   equipment_df['type'].isin(['vessel', 'heat_exchanger', 'reactor'])
               ].iterrows()):
                suggestions.append({
                    "system": "Piping & Equipment Insulation",
                    "suggestion": "Ensure hot and cold process lines and equipment (vessels, heat exchangers) are adequately insulated to minimize heat loss/gain and improve energy efficiency.",
                    "savings": "Significant reduction in heating/cooling utility consumption (e.g., 5-15%).",
                    "cost": "Varies widely based on scope, from a few hundred to tens of thousands."
                })

        if self.ai._check_openai_key():
            try:
                ai_prompt = f"""
Analyze the provided equipment and pipeline data from a P&ID of a {process_type.replace('_', ' ')} system to identify further energy efficiency improvements.
Equipment: {equipment_df[['ID', 'type', 'Description', 'efficiency_pct']].to_dict(orient='records')}
Pipelines (sample connections): {[f"{p['Source_Equipment_ID']}->{p['Destination_Equipment_ID']}" for _,p in pipeline_df.head().iterrows()]}

Suggest:
- Opportunities for waste heat recovery (e.g., economizers, heat exchangers)
- Optimization of motor/pump/fan operations beyond VFDs
- Process integration opportunities (e.g., using exothermic reaction heat)
- Best practices for insulation or steam trapping
- Any other relevant energy-saving technologies.

Format your response as a JSON array of objects, each with 'equipment' (or 'system'), 'suggestion', 'savings' (estimated), and 'cost' (estimated).
If no further suggestions, return an empty array [].
"""
                ai_response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an energy efficiency consultant for industrial processes. Provide practical and impactful suggestions."},
                        {"role": "user", "content": ai_prompt}
                    ],
                    temperature=0.4,
                    max_tokens=500
                )
                ai_parsed_suggestions = json.loads(ai_response.choices[0].message.content)
                suggestions.extend(ai_parsed_suggestions)

            except Exception as e:
                print(f"Warning: AI energy efficiency suggestion failed: {e}")

        return suggestions

def generate_ai_safety_warnings(component):
    """
    Uses OpenAI to flag safety risks in components (e.g. missing relief, hazards).
    """
    prompt = f"""You are a P&ID safety reviewer. Assess this component:
Type: {component.get('type')}
Tag: {component.get('tag')}
Attributes: {component.get('attributes', {})}
Are there any safety issues or missing elements (e.g., pressure relief, emergency valves)?
Respond in 2 short sentences only."""

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=150
        )
        msg = response.choices[0].message.content.strip()
        return [{"message": msg, "severity": "Warning"}] if msg else []
    except Exception as e:
        return [{"message": f"AI safety check unavailable: {e}", "severity": "Warning"}]
