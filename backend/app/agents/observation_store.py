from dataclasses import dataclass, field
from typing import Dict, Any, List
import time

@dataclass
class EnvironmentObservation:
    observation_id: str
    agent_id: str
    step_number: int
    source_tool: str
    raw_payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

class ObservationStore:
    """
    Observation Store recording raw environment inputs, perception events, and tool outputs.
    """
    def __init__(self):
        self._observations: List[EnvironmentObservation] = []

    def record(self, agent_id: str, step_number: int, source_tool: str, raw_payload: Dict[str, Any]) -> str:
        obs_id = f"obs_{len(self._observations) + 1}_{int(time.time())}"
        obs = EnvironmentObservation(
            observation_id=obs_id,
            agent_id=agent_id,
            step_number=step_number,
            source_tool=source_tool,
            raw_payload=raw_payload
        )
        self._observations.append(obs)
        return obs_id

    def get_by_agent(self, agent_id: str) -> List[EnvironmentObservation]:
        return [o for o in self._observations if o.agent_id == agent_id]

observation_store = ObservationStore()
