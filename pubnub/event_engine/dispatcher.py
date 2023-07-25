from pubnub.event_engine.models import effects
from pubnub.event_engine import manage_effects


class Dispatcher:
    _pubnub = None
    _managed_effects_factory = None

    def __init__(self, event_engine) -> None:
        self._event_engine = event_engine
        self._managed_effects = {}
        self._effect_emitter = manage_effects.EmitEffect()

    def set_pn(self, pubnub_instance):
        self._pubnub = pubnub_instance
        self._effect_emitter.set_pn(pubnub_instance)

    def dispatch_effect(self, effect: effects.PNEffect):
        if not self._managed_effects_factory:
            self._managed_effects_factory = manage_effects.ManagedEffectFactory(self._pubnub, self._event_engine)

        if isinstance(effect, effects.PNEmittableEffect):
            self.emit_effect(effect)

        elif isinstance(effect, effects.PNManageableEffect):
            self.dispatch_managed_effect(effect)

        elif isinstance(effect, effects.PNCancelEffect):
            self.dispatch_cancel_effect(effect)

    def emit_effect(self, effect: effects.PNEffect):
        self._effect_emitter.emit(effect)

    def dispatch_managed_effect(self, effect: effects.PNEffect):
        managed_effect = self._managed_effects_factory.create(effect)
        managed_effect.run()
        self._managed_effects[effect.__class__.__name__] = managed_effect

    def dispatch_cancel_effect(self, effect: effects.PNEffect):
        if effect.cancel_effect in self._managed_effects:
            self._managed_effects[effect.cancel_effect].stop()
            del self._managed_effects[effect.cancel_effect]
