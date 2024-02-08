from pubnub.event_engine.models import invocations
from pubnub.event_engine import effects


class Dispatcher:
    _pubnub = None
    _effects_factory = None

    def __init__(self, event_engine) -> None:
        self._event_engine = event_engine
        self._managed_effects = {}
        self._effect_emitter = effects.EmitEffect()

    def set_pn(self, pubnub_instance):
        self._pubnub = pubnub_instance
        self._effect_emitter.set_pn(pubnub_instance)

    def dispatch_effect(self, invocation: invocations.PNInvocation):
        if not self._effects_factory:
            self._effects_factory = effects.EffectFactory(self._pubnub, self._event_engine)

        if isinstance(invocation, invocations.PNEmittableInvocation):
            self.emit_effect(invocation)

        elif isinstance(invocation, invocations.PNManageableInvocation):
            self.dispatch_managed_effect(invocation)

        elif isinstance(invocation, invocations.PNCancelInvocation):
            self.dispatch_cancel_effect(invocation)

    def emit_effect(self, effect: invocations.PNInvocation):
        self._effect_emitter.emit(effect)

    def dispatch_managed_effect(self, invocation: invocations.PNInvocation):
        effect = self._effects_factory.create(invocation)
        effect.run()
        self._managed_effects[invocation.__class__.__name__] = effect

    def dispatch_cancel_effect(self, invocation: invocations.PNInvocation):
        if invocation.cancel_effect in self._managed_effects:
            self._managed_effects[invocation.cancel_effect].stop()
            del self._managed_effects[invocation.cancel_effect]
