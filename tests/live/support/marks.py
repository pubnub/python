"""compile_only(reason): marks a function that holds a docs sample which cannot run against the service. Its name does
not start with test_, so pytest never collects it. The marker lint and the manifest read the decorator statically
(mode compile-only) and the file is still imported, so the sample compiles."""


def compile_only(reason):
    if not isinstance(reason, str) or len(reason.strip()) < 10:
        raise ValueError('compile_only needs a reason')

    def deco(fn):
        fn.compile_only_reason = reason
        return fn

    return deco
