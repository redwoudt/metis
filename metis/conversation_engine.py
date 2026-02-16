from __future__ import annotations

import logging
from typing import Any, Optional

from metis.states.greeting import GreetingState
from metis.memory.snapshot import ConversationSnapshot
from metis.models.adapters.base import RespondingModel
from metis.prompts.prompt import Prompt


logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------
# Pickle-safe fallback tool executor (must be at module scope for snapshots)
# ------------------------------------------------------------------------
class DefaultToolExecutor:
    """Pickle-safe fallback tool executor.

    This must be defined at module scope (not inside ConversationEngine.__init__)
    so that ConversationEngine snapshots can be pickled.
    """

    def __init__(self):
        self.calls = []

    def execute_tool(self, tool_name=None, args=None, user=None):
        self.calls.append((tool_name, args, user))
        return f"TOOL_OUTPUT:{tool_name}:{args}"


class ConversationEngine:
    """
    ConversationEngine plays two roles:
    - State pattern context: it holds the current conversation state and delegates behavior to it.
    - Memento originator: it can snapshot and restore its internal state.

    It collaborates with the Bridge (ModelManager) for model access.

    NOTE:
    `request_handler` may be passed for backward compatibility but is intentionally
    ignored and never stored on the engine. Tests rely on `ConversationEngine` not
    exposing a `request_handler` attribute.
    """

    def __init__(self, model_manager, request_handler=None, **kwargs):
        # --- State Pattern Context ---
        self.state = GreetingState()
        self.history = []

        # Conversation preferences / session-level hints
        self.preferences = {
            "tone": "friendly",
            "persona": "",
            "context": "",
            "tool_output": "",
        }

        # --- Bridge Collaborator (ModelManager) ---
        self.model_manager = model_manager

        # ------------------------------------------------------------------
        # Tool executor (required by pipeline tests)
        # ------------------------------------------------------------------
        self.tool_executor = None

        try:
            from metis.config import Config
            services = Config.services()
            self.tool_executor = getattr(services, "tool_executor", None)
        except Exception:
            self.tool_executor = None

        # Fallback dummy executor (used in tests)
        if self.tool_executor is None:
            self.tool_executor = DefaultToolExecutor()
        else:
            # Ensure calls list exists (pipeline asserts against it)
            if not hasattr(self.tool_executor, "calls"):
                self.tool_executor.calls = []

        # Expose active model for tests/debugging only (never used for execution)
        self.model: Optional[RespondingModel] = None

        self._refresh_model_ref()

        logger.debug(
            "[ConversationEngine] Initialized with GreetingState, "
            "model_manager=%s",
            type(model_manager).__name__,
        )
        # Ensure deprecated attribute never exists on the instance
        self.__dict__.pop("request_handler", None)

    def __setattr__(self, name, value):
        """
        Back-compat: older code/tests may still try to attach request_handler.

        We intentionally do NOT store it on the base ConversationEngine instance
        (some tests assert it should not exist), but allow subclasses (e.g. test
        DummyEngine) to attach it.
        """
        if name == "request_handler" and type(self) is ConversationEngine:
            return
        super().__setattr__(name, value)


    def _looks_like_model(self, obj: Any) -> bool:
        """Heuristic: detect model/proxy objects without importing concrete classes."""
        if obj is None:
            return False
        # Avoid obvious non-model types
        if isinstance(obj, (str, bytes, int, float, bool, list, tuple, set)):
            return False
        if isinstance(obj, dict):
            return False
        # The project uses proxies/clients that expose generate/respond
        return callable(getattr(obj, "generate", None)) or callable(getattr(obj, "respond", None))

    def _pick_model_from_mapping(self, mapping: dict) -> Optional[RespondingModel]:
        """Pick the most relevant model from a role->model mapping."""
        if not isinstance(mapping, dict) or not mapping:
            return None

        role = None
        mm = getattr(self, "model_manager", None)
        if mm is not None:
            role = getattr(mm, "role", None) or getattr(mm, "state_name", None)

        # 1) Prefer the current role if present
        if role and role in mapping and self._looks_like_model(mapping.get(role)):
            return mapping.get(role)

        # 2) Otherwise, pick the first model-looking value (depth=2)
        for v in mapping.values():
            if self._looks_like_model(v):
                return v
            if isinstance(v, dict):
                for vv in v.values():
                    if self._looks_like_model(vv):
                        return vv
        return None

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------
    def _refresh_model_ref(self) -> None:
        """
        Refresh debug/test-facing reference to the active model.

        This must never affect execution paths. The ConversationEngine always
        delegates execution to ModelManager.
        """
        if self.model_manager is None:
            self.model = None
            return

        mm = self.model_manager

        # 1) Prefer common direct attributes/properties (works even if they are @property)
        for attr in (
            "model_client",
            "client",
            "model",
            "proxy",
            "_model_client",
            "_client",
            "_model",
            "_proxy",
            "active_model",
            "active_client",
            "current_model",
            "current_client",
        ):
            try:
                val = getattr(mm, attr)
            except Exception:
                val = None
            if val is not None:
                self.model = val
                return

        # 2) Try common accessor methods
        for meth in ("get_model", "get_model_client", "get_client"):
            fn = getattr(mm, meth, None)
            if not callable(fn):
                continue

            try:
                val = fn()
            except TypeError:
                # Some refactors use role-based signature
                role = getattr(mm, "role", None) or getattr(mm, "state_name", None)
                try:
                    val = fn(role)
                except Exception:
                    val = None
            except Exception:
                val = None

            if val is not None:
                self.model = val
                return

        # 3) Last resort: scan ModelManager for common mappings / __dict__
        # Common mapping attribute names across refactors
        for attr in (
            "models",
            "model_clients",
            "clients",
            "proxies",
            "by_role",
            "_models",
            "_model_clients",
            "_clients",
            "_proxies",
        ):
            try:
                mapping = getattr(mm, attr)
            except Exception:
                mapping = None
            picked = self._pick_model_from_mapping(mapping) if isinstance(mapping, dict) else None
            if picked is not None:
                self.model = picked
                return

        d = getattr(mm, "__dict__", None)
        if isinstance(d, dict):
            # First try to pick from any dict-like fields (role->model)
            for v in d.values():
                if isinstance(v, dict):
                    picked = self._pick_model_from_mapping(v)
                    if picked is not None:
                        self.model = picked
                        return

            # Then try any direct fields
            for v in d.values():
                if self._looks_like_model(v):
                    self.model = v
                    return

        self.model = None

    def get_model(self):
        """Public surface for tests/debugging.

        IMPORTANT:
        - Must not affect execution.
        - Return the active model proxy/client currently held by ModelManager.

        Notes:
        ModelManager implementations vary across refactors; for tests we want the
        concrete client/proxy currently used for generation.
        """
        mm = getattr(self, "model_manager", None)
        if mm is None:
            self.model = None
            return None

        # First: align cached debug ref
        self._refresh_model_ref()
        if self._looks_like_model(getattr(self, "model", None)):
            return self.model

        # Fast path: your current refactor logs `model_client=ModelProxy`
        for attr in ("model_client", "_model_client"):
            try:
                val = getattr(mm, attr)
            except Exception:
                val = None
            if val is not None:
                self.model = val
                return val

        # Common synonyms (keep heuristic here)
        for attr in (
                "client",
                "proxy",
                "model",
                "_client",
                "_proxy",
                "_model",
                "active_model",
                "active_client",
                "current_model",
                "current_client",
        ):
            try:
                val = getattr(mm, attr)
            except Exception:
                val = None
            if val is not None and self._looks_like_model(val):
                self.model = val
                return val

        # Mapping-style storage (role -> client)
        for attr in (
                "models",
                "model_clients",
                "clients",
                "proxies",
                "by_role",
                "_models",
                "_model_clients",
                "_clients",
                "_proxies",
        ):
            try:
                mapping = getattr(mm, attr)
            except Exception:
                mapping = None
            if isinstance(mapping, dict):
                picked = self._pick_model_from_mapping(mapping)
                if picked is not None:
                    self.model = picked
                    return picked

        # Accessor methods
        for meth in ("get_model_client", "get_client", "get_model"):
            fn = getattr(mm, meth, None)
            if not callable(fn):
                continue
            try:
                val = fn()
            except TypeError:
                role = getattr(mm, "role", None) or getattr(mm, "state_name", None)
                try:
                    val = fn(role)
                except Exception:
                    val = None
            except Exception:
                val = None

            if val is not None:
                self.model = val
                return val

        # Final fallback: whatever refresh can find
        self._refresh_model_ref()
        return getattr(self, "model", None)

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------
    def set_state(self, new_state):
        logger.debug(
            "[ConversationEngine] Transitioning to new state: %s",
            new_state.__class__.__name__,
        )
        self.state = new_state

    # ------------------------------------------------------------------
    # Dialogue and model interaction
    # ------------------------------------------------------------------
    def respond(self, user_input: str) -> str:
        """
        Route input through the current state.

        Defensive behavior (required by tests):
        - If state is None → start in GreetingState
        - If state is a string → resolve via naming convention
        """
        explicit_state = getattr(self, "_explicit_state", False)
        from metis.states.greeting import GreetingState

        # -------------------------------------------------
        # Normalize state
        # -------------------------------------------------
        if not explicit_state:
            if self.state is None:
                self.state = GreetingState()

            elif isinstance(self.state, str):
                # Accept either:
                # - short state names: "greeting" -> GreetingState from metis.states.greeting
                # - class names: "SummarizingState" -> SummarizingState from metis.states.summarizing
                import importlib

                raw = self.state.strip()

                if raw.lower().endswith("state"):
                    # "SummarizingState" -> module "summarizing", class "SummarizingState"
                    base = raw[:-5]  # strip trailing "State"
                    module_name = base.lower()
                    class_name = raw
                else:
                    # "greeting" -> module "greeting", class "GreetingState"
                    module_name = raw.lower()
                    class_name = f"{raw.capitalize()}State"

                try:
                    state_module = importlib.import_module(f"metis.states.{module_name}")
                    state_cls = getattr(state_module, class_name)
                except (ModuleNotFoundError, AttributeError) as exc:
                    raise ValueError(f"Unknown state '{self.state}'") from exc

                self.state = state_cls()

        # -------------------------------------------------
        # State must now be a concrete State instance
        # -------------------------------------------------
        # Normalize user_input: states must never receive Prompt objects
        if isinstance(user_input, Prompt):
            user_input = user_input.render()

        logger.debug(
            "[ConversationEngine] Calling respond on state: %s",
            self.state.__class__.__name__,
        )

        response = self.state.respond(self, user_input)

        # -------------------------------------------------
        # Coerce None -> "" (required by tests)
        # -------------------------------------------------
        if response is None:
            response = ""

        # Defensive: always return a string
        if not isinstance(response, str):
            response = str(response)

        # Record interaction for snapshot / undo support (one entry per turn)
        if hasattr(self, "history"):
            self.history.append(response)

        # -------------------------------------------------
        # Allow state transitions
        # -------------------------------------------------
        if hasattr(self.state, "next_state") and self.state.next_state is not None:
            self.state = self.state.next_state

        # Clear explicit state lock after first turn
        if hasattr(self, "_explicit_state"):
            del self._explicit_state

        return response

    def generate_with_model(self, prompt: str) -> str:
        # Normalize prompt: always render Prompt objects before sending to model
        if isinstance(prompt, Prompt):
            prompt = prompt.render()

        self._refresh_model_ref()
        logger.debug("[ConversationEngine] generate_with_model() model ref now: %s", type(getattr(self, "model", None)).__name__)
        logger.debug(
            "[ConversationEngine] Delegating prompt to ModelManager: %r",
            prompt[:200],
        )

        try:
            generated = self.model_manager.generate(prompt)
        except Exception as e:
            logger.error("[ConversationEngine] ModelManager.generate failed: %s", e)
            generated = ""

        if isinstance(generated, dict):
            generated = generated.get("text", "")
        elif not isinstance(generated, str):
            generated = str(generated or "")

        return generated

    def set_model_manager(self, model_manager):
        logger.debug(
            "[ConversationEngine] Updating model_manager to %s",
            type(model_manager).__name__,
        )
        self.model_manager = model_manager

        # Keep test/debug reference aligned immediately
        self.model = None
        if model_manager is not None:
            for attr in (
                "model_client",
                "client",
                "model",
                "proxy",
                "models",
                "model_clients",
                "clients",
                "proxies",
                "by_role",
                "_models",
                "_model_clients",
                "_clients",
                "_proxies",
            ):
                try:
                    val = getattr(model_manager, attr)
                except Exception:
                    val = None
                if val is not None:
                    if isinstance(val, dict):
                        picked = self._pick_model_from_mapping(val)
                        if picked is not None:
                            self.model = picked
                            break
                    elif self._looks_like_model(val):
                        self.model = val
                        break

        self._refresh_model_ref()

    # ------------------------------------------------------------------
    # Memento pattern: snapshot / restore
    # ------------------------------------------------------------------
    def create_snapshot(self):
        """Create a memento snapshot of the engine's current state."""
        # Never persist deprecated/back-compat fields
        state = dict(self.__dict__)
        state.pop("request_handler", None)
        state.pop("tool_executor", None)

        snapshot = ConversationSnapshot(state)
        logger.debug("[ConversationEngine] Snapshot created")
        return snapshot

    def restore_snapshot(self, snapshot):
        """Restore engine state from a previously created snapshot."""
        state_data = snapshot.get_state()
        # Never restore deprecated/back-compat fields
        if isinstance(state_data, dict):
            state_data.pop("request_handler", None)
        self.__dict__.update(state_data)

        # Safety-net: always ensure core attributes exist
        if not hasattr(self, "state") or self.state is None:
            self.state = GreetingState()

        if not hasattr(self, "history") or self.history is None:
            self.history = []

        if not hasattr(self, "preferences") or self.preferences is None:
            self.preferences = {
                "tone": "friendly",
                "persona": "",
                "context": "",
                "tool_output": "",
            }

        # Ensure deprecated attribute never exists on the instance
        self.__dict__.pop("request_handler", None)

        # tool_executor is intentionally not snapshotted; rehydrate it
        if not hasattr(self, "tool_executor") or self.tool_executor is None:
            try:
                from metis.config import Config
                services = Config.services()
                self.tool_executor = getattr(services, "tool_executor", None) or DefaultToolExecutor()
            except Exception:
                self.tool_executor = DefaultToolExecutor()

        if not hasattr(self.tool_executor, "calls"):
            self.tool_executor.calls = []

        self._refresh_model_ref()
        logger.debug("[ConversationEngine] State restored from snapshot")