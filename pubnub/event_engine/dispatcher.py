from pubnub.event_engine import effects


class Dispatcher:
    def __init__(self) -> None:
        self._managed_effects = {}
        self._effect_emitter = effects.EmitEffect()

    def dispatch_effect(self, effect: effects.PNEffect):
        if isinstance(effect, effects.PNEmittableEffect):
            self._effect_emitter.emit(effect)

        if isinstance(effect, effects.PNManageableEffect):
            managed_effect = effects.ManagedEffect(effect)
            managed_effect.run()
            self._managed_effects[effect.__class__.__name__] = managed_effect

        if isinstance(effect, effects.PNCancelEffect):
            if effect.cancel_effect in self._managed_effects:
                self._managed_effects[effect.cancel_effect].stop()
                del self._managed_effects[effect.cancel_effect]
