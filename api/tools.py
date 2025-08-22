"""
This module implements the toolset for the GHC-DT agent.
Each function is a tool that the agent can execute.
"""
import json
from typing import Any, Dict, List

# The canonical list of tool definitions provided by the user.
TOOL_DEFINITIONS = [
  {
    "type": "function",
    "function": {
      "name": "status_get",
      "description": "Return cockpit snapshot: counts, last actions, pending approvals.",
      "parameters": { "type": "object", "properties": {}, "required": [] }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "vault_search",
      "description": "Search local knowledge vault for top-k results.",
      "parameters": {
        "type": "object",
        "properties": {
          "query": { "type": "string" },
          "k": { "type": "integer", "default": 5, "minimum": 1, "maximum": 10 }
        },
        "required": ["query"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "vault_ingest_request",
      "description": "Register an ingest request (never writes): normalize file/text for later approval.",
      "parameters": {
        "type": "object",
        "properties": {
          "source": { "type": "string", "description": "filename or 'inline-text'" },
          "note": { "type": "string" }
        },
        "required": ["source"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "approvals_add",
      "description": "Add a pending approval item.",
      "parameters": {
        "type": "object",
        "properties": {
          "title": { "type": "string" },
          "link": { "type": "string" }
        },
        "required": ["title"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "approvals_mark",
      "description": "Mark an approval item as Approved/Denied.",
      "parameters": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "status": { "type": "string", "enum": ["Approved", "Denied"] }
        },
        "required": ["id", "status"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "evidence_log",
      "description": "Append a structured evidence record (event, payload).",
      "parameters": {
        "type": "object",
        "properties": {
          "event": { "type": "string" },
          "payload": { "type": "object", "additionalProperties": True }
        },
        "required": ["event"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "codex_prompt_build",
      "description": "Return a pre‑filled Code Agent block for maintenance/upgrade or run/start.",
      "parameters": {
        "type": "object",
        "properties": {
          "goal": { "type": "string" },
          "action_notes": { "type": "string" },
          "run": { "type": "boolean", "default": True },
          "change_id": { "type": "string" }
        },
        "required": ["goal", "action_notes", "change_id"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "state_get",
      "description": "Read Session Anchors (phase, last_actions, pending_approvals, key_dates).",
      "parameters": { "type": "object", "properties": {}, "required": [] }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "state_update",
      "description": "Update Session Anchors fields.",
      "parameters": {
        "type": "object",
        "properties": {
          "phase": { "type": "string" },
          "key_dates": {
            "type": "object",
            "properties": {
              "zec_filing": { "type": "string" },
              "gmp_dossier": { "type": "string" },
              "cash_buffer_to": { "type": "string" }
            }
          }
        }
      }
    }
  }
]

# --- Tool Implementations (Stubs) ---

def status_get() -> Dict[str, Any]:
    return {"status": "not_implemented", "counts": {}, "last_actions": [], "pending_approvals": []}

def vault_search(query: str, k: int = 5) -> Dict[str, Any]:
    return {"status": "not_implemented", "query": query, "k": k, "results": []}

def vault_ingest_request(source: str, note: str = None) -> Dict[str, Any]:
    return {"status": "not_implemented", "source": source, "note": note}

def approvals_add(title: str, link: str = None) -> Dict[str, Any]:
    return {"status": "not_implemented", "title": title, "link": link}

def approvals_mark(id: str, status: str) -> Dict[str, Any]:
    return {"status": "not_implemented", "id": id, "marked_as": status}

def evidence_log(event: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    return {"status": "not_implemented", "event": event, "payload": payload}

def codex_prompt_build(goal: str, action_notes: str, change_id: str, run: bool = True) -> Dict[str, Any]:
    return {"status": "not_implemented", "goal": goal, "change_id": change_id}

def state_get() -> Dict[str, Any]:
    return {"status": "not_implemented", "phase": "unknown", "key_dates": {}}

def state_update(phase: str = None, key_dates: Dict[str, Any] = None) -> Dict[str, Any]:
    return {"status": "not_implemented", "updated_fields": list(filter(None, [phase, key_dates]))}

# --- Tool Dispatcher ---

# A mapping from tool names to their function implementations.
TOOL_IMPLEMENTATIONS = {
    "status_get": status_get,
    "vault_search": vault_search,
    "vault_ingest_request": vault_ingest_request,
    "approvals_add": approvals_add,
    "approvals_mark": approvals_mark,
    "evidence_log": evidence_log,
    "codex_prompt_build": codex_prompt_build,
    "state_get": state_get,
    "state_update": state_update,
}

def get_tool_definitions() -> List[Dict[str, Any]]:
    """Returns the list of all tool definitions."""
    return TOOL_DEFINITIONS

def execute_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes a tool by its name with the given arguments.
    """
    if name not in TOOL_IMPLEMENTATIONS:
        return {"error": f"Tool '{name}' not found."}
    
    tool_function = TOOL_IMPLEMENTATIONS[name]
    
    try:
        # This is a simplified approach. A robust implementation would
        # inspect function signature and handle missing/extra args.
        result = tool_function(**args)
        return {"tool_name": name, "result": result}
    except TypeError as e:
        return {"error": f"Invalid arguments for tool '{name}': {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred while executing tool '{name}': {e}"}
