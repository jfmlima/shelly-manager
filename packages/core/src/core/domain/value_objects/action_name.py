"""An action addressed on a device component.

Shelly names actions ``Namespace.Method`` (``Switch.Toggle``, ``Shelly.Reboot``)
and reports the ones it accepts through ``Shelly.ListMethods``; Gen1 devices
report nothing and are addressed through the synthetic ``Legacy`` namespace.

Discovery hands out qualified names, so an execute call must accept them as
given rather than re-prefixing them. This value object is the seam both sides
cross: it qualifies a bare method, leaves an already qualified one alone, and
matches either back against what the device reported.
"""

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from .component_namespace import ComponentNamespace

LEGACY_NAMESPACE = "Legacy"


class ActionName(BaseModel):

    model_config = ConfigDict(frozen=True)

    namespace: str | None = None
    method: str

    @classmethod
    def parse(cls, raw: str) -> "ActionName | None":
        """Read a qualified name. Returns None when ``raw`` carries no namespace."""
        namespace, separator, method = raw.partition(".")
        if not separator or not namespace or not method:
            return None
        return cls(namespace=namespace, method=method)

    @classmethod
    def of(cls, action: str) -> "ActionName":
        """Read what the caller wrote, qualified or bare.

        Accepts both what discovery hands out (``Switch.Toggle``) and the bare
        method name (``Toggle``), so a name copied out of a listing can be pasted
        straight back into an execute call. A bare name keeps no namespace: which
        one it means is a question only the component can answer.
        """
        return cls.parse(action) or cls(method=action)

    @property
    def qualified(self) -> str | None:
        if self.namespace is None:
            return None
        return f"{self.namespace}.{self.method}"

    @property
    def is_legacy(self) -> bool:
        return self.namespace == LEGACY_NAMESPACE

    def resolve(
        self, component_key: str, available_methods: Sequence[str]
    ) -> str | None:
        """The method to send, in the device's own spelling.

        Only methods the component owns are reachable, so addressing one
        component is never a way to invoke another's action. Gen2+ firmware
        dispatches names case-insensitively and Shelly's own documentation
        disagrees with itself about the casing (``Wifi`` against ``WiFi``,
        ``Mqtt`` against ``MQTT``), so matching ignores case and the device's
        spelling wins.

        A namespace the caller wrote is honoured exactly or refused. Only a bare
        method is searched for, because guessing which namespace an explicit one
        meant would turn a request for a missing action into a different action.

        An empty ``available_methods`` means there was no list to check
        against. Returns None when the component owns no such method.
        """
        namespace = ComponentNamespace.for_component_type(
            _component_type_of(component_key)
        )

        if not available_methods:
            return self._unvalidated(namespace)

        owned = namespace.actions_in(available_methods)

        if self.qualified is not None:
            wanted = self.qualified.lower()
            return next((m for m in owned if m.lower() == wanted), None)

        for candidate in namespace.namespaces:
            wanted = f"{candidate}.{self.method}".lower()
            for method in owned:
                if method.lower() == wanted:
                    return method

        # Shelly.ZigbeeClear on zigbee: owned, but outside the component's own
        # namespaces, so the pass above cannot find it.
        bare = self.method.lower()
        return next(
            (m for m in owned if m.partition(".")[2].lower() == bare),
            None,
        )

    def _unvalidated(self, namespace: ComponentNamespace) -> str | None:
        """What to send when there is no method list to check against.

        A bare method is still qualified and sent, so a device too busy to
        answer ``Shelly.ListMethods`` stays usable. A written namespace the
        component does not own is refused rather than rewritten: an unanswered
        method list must not turn a request for one component's action into
        another component's action.
        """
        if self.qualified is None:
            return f"{namespace.qualifies_as}.{self.method}"
        if namespace.owns(self.qualified):
            return self.qualified
        return None


def _component_type_of(component_key: str) -> str:
    return component_key.split(":")[0]
