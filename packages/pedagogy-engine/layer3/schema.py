"""
Pydantic models for Layer 3: Scene Specification Schema
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SceneObject(BaseModel):
    """
    An object that exists in the scene.
    """
    id: str
    type: str = Field(..., description="Abstract visual primitive (surface, point, vector_field, text, axis, etc)")
    role: Optional[str] = Field(None, description="Pedagogical role (landscape, parameter_state, mechanism, etc)")
    properties: Dict[str, Any] = Field(default_factory=dict)


class SceneAction(BaseModel):
    """
    An action or animation that occurs in the scene.
    """
    action: str = Field(..., description="Primitive action (create, move, transform, loop, fade, highlight, etc)")
    target: Optional[str] = Field(None, description="Object id this action applies to")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    steps: Optional[List["SceneAction"]] = None  # for compound actions like loops


class SceneSpec(BaseModel):
    """
    A fully specified visual scene derived from a storyboard beat.
    """
    scene_id: str
    pedagogical_purpose: str
    conceptual_goal: str

    objects: List[SceneObject]
    actions: List[SceneAction]

    camera: Optional[Dict[str, Any]] = None
    narration: Optional[str] = None  # optional bridge to voice/text later


class SceneSpecMetadata(BaseModel):
    generator_version: str = "0.1.0"
    source_storyboard_topic: str
    generation_timestamp: str
    source_layer2_id: Optional[str] = None


class SceneSpecWithMetadata(BaseModel):
    scenes: List[SceneSpec]
    metadata: SceneSpecMetadata

    def model_dump_json_formatted(self) -> str:
        import json
        return json.dumps(self.model_dump(), indent=2)
