"""Human-in-the-Loop (HITL) Validation with AI Insight and Safety Agents"""

import streamlit as st
import pandas as pd
import json
import re
import openai
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


# ========== ENUMS & MODELS ==========

class ValidationStatus(Enum):
    PENDING = "Pending Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    MODIFIED = "Modified"

class ValidationCategory(Enum):
    CONNECTIVITY = "Connectivity"
    STANDARDS = "Standards Compliance"
    SAFETY = "Safety Requirements"
    COMPLETENESS = "Completeness"
    CONSISTENCY = "Consistency"

@dataclass
class ValidationItem:
    id: str
    element_id: str
    element_type: str
    category: ValidationCategory
    description: str
    severity: str
    status: ValidationStatus = ValidationStatus.PENDING
    reviewer_notes: str = ""
    timestamp: Optional[datetime] = None
    reviewed_by: Optional[str] = None

@dataclass
class HITLSession:
    session_id: str
    project_id: str
    created_at: datetime
    validation_items: List[ValidationItem] = field(default_factory=list)
    reviewer_name: str = ""
    completion_percentage: float = 0.0


# ========== AI INSIGHT + SAFETY AGENTS ==========

def generate_ai_insights_for_component(component, category):
    prompt = f"""You are a process design expert reviewing a {component.get('type')} with tag {component.get('tag')}.
Category: {category}.
Attributes: {component.get('attributes', {})}.
Provide 2 short, practical suggestions to improve efficiency, sustainability, or connectivity."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        suggestions = response['choices'][0]['message']['content'].split('\n')
        return [{"message": s.strip("- ").strip(), "severity": "Info"} for s in suggestions if s.strip()]
    except Exception as e:
        return [{"message": f"AI insight unavailable: {e}", "severity": "Info"}]

def generate_ai_safety_warnings(component):
    prompt = f"""You are a P&ID safety reviewer. Assess this component:
Type: {component.get('type')}
Tag: {component.get('tag')}
Attributes: {component.get('attributes', {})}
Are there any safety issues or missing elements (e.g., pressure relief, emergency valves)?
Respond in 2 short sentences only."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=150
        )
        msg = response['choices'][0]['message']['content'].strip()
        return [{"message": msg, "severity": "Warning"}] if msg else []
    except Exception as e:
        return [{"message": f"AI safety check unavailable: {e}", "severity": "Warning"}]


# ========== HITL VALIDATOR ==========

class HITLValidator:
    def __init__(self):
        self.session: Optional[HITLSession] = None
        self.dsl_data = None
        self.validation_rules = self._load_validation_rules()

    def _load_validation_rules(self) -> Dict:
        return {
            "connectivity": [{"rule": "all_equipment_connected", "severity": "Error"}],
            "standards": [{"rule": "isa_tag_format", "severity": "Warning"}],
            "safety": [{"rule": "pressure_relief_required", "severity": "Error"}],
            "completeness": [{"rule": "all_tags_assigned", "severity": "Warning"}]
        }

    def create_session(self, project_id: str, dsl_data: Dict) -> HITLSession:
        self.dsl_data = dsl_data
        self.session = HITLSession(
            session_id=f"HITL-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            project_id=project_id,
            created_at=datetime.now()
        )
        self._run_automated_checks()
        return self.session

    def _run_automated_checks(self):
        self._check_connectivity()
        self._check_standards()
        self._check_safety()
        self._check_completeness()
        self._update_completion()

    def _check_connectivity(self):
        components = {c['id']: c for c in self.dsl_data.get('components', [])}
        connections = self.dsl_data.get('connections', [])
        connected = set()
        for conn in connections:
            connected.add(conn['from']['component'])
            connected.add(conn['to']['component'])
        for comp_id, comp in components.items():
            if comp_id not in connected:
                self.session.validation_items.append(
                    ValidationItem(
                        id=f"CONN-{len(self.session.validation_items)+1:03d}",
                        element_id=comp_id,
                        element_type=comp['type'],
                        category=ValidationCategory.CONNECTIVITY,
                        description=f"Component {comp['tag']} has no connections",
                        severity="Error"
                    )
                )
        for comp in self.dsl_data.get('components', []):
            for insight in generate_ai_insights_for_component(comp, "connectivity"):
                self.session.validation_items.append(
                    ValidationItem(
                        id=f"AI-CONN-{comp['id']}-{len(self.session.validation_items)+1:02d}",
                        element_id=comp['id'],
                        element_type=comp['type'],
                        category=ValidationCategory.CONNECTIVITY,
                        description=insight['message'],
                        severity=insight['severity']
                    )
                )

    def _check_standards(self):
        tag_pattern = re.compile(r'^[A-Z]{1,4}-\d{3,4}[A-Z]?$')
        for comp in self.dsl_data.get('components', []):
            tag = comp.get('tag', '')
            if not tag_pattern.match(tag):
                self.session.validation_items.append(
                    ValidationItem(
                        id=f"STD-{len(self.session.validation_items)+1:03d}",
                        element_id=comp['id'],
                        element_type=comp['type'],
                        category=ValidationCategory.STANDARDS,
                        description=f"Tag '{tag}' does not follow ISA format",
                        severity="Warning"
                    )
                )

    def _check_safety(self):
        for comp in self.dsl_data.get('components', []):
            for warn in generate_ai_safety_warnings(comp):
                self.session.validation_items.append(
                    ValidationItem(
                        id=f"AI-SAF-{comp['id']}-{len(self.session.validation_items)+1:02d}",
                        element_id=comp['id'],
                        element_type=comp['type'],
                        category=ValidationCategory.SAFETY,
                        description=warn['message'],
                        severity=warn['severity']
                    )
                )

    def _check_completeness(self):
        for comp in self.dsl_data.get('components', []):
            missing = [k for k in ['tag', 'name', 'type'] if not comp.get(k)]
            if missing:
                self.session.validation_items.append(
                    ValidationItem(
                        id=f"CMP-{len(self.session.validation_items)+1:03d}",
                        element_id=comp['id'],
                        element_type=comp['type'],
                        category=ValidationCategory.COMPLETENESS,
                        description=f"Missing attributes: {', '.join(missing)}",
                        severity="Warning"
                    )
                )

    def _update_completion(self):
        total = len(self.session.validation_items)
        reviewed = sum(1 for i in self.session.validation_items if i.status != ValidationStatus.PENDING)
        self.session.completion_percentage = (reviewed / total) * 100 if total else 100.0

    def update_validation_item(self, item_id, status, notes, reviewer):
        for i in self.session.validation_items:
            if i.id == item_id:
                i.status = status
                i.reviewer_notes = notes
                i.reviewed_by = reviewer
                i.timestamp = datetime.now()
        self._update_completion()

    def export_validation_report(self):
        s = self.session
        return {
            "session_id": s.session_id,
            "project_id": s.project_id,
            "created_at": s.created_at.isoformat(),
            "reviewer": s.reviewer_name,
            "completion": s.completion_percentage,
            "items": [vars(i) for i in s.validation_items]
        }
