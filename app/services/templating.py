from jinja2 import Environment, StrictUndefined

def render_mapping(mapping, form, envvars, ctx):
    jenv = Environment(undefined=StrictUndefined)
    out = {}
    for k, tpl in mapping.items():
        out[k] = jenv.from_string(tpl).render(form=form, env=envvars, ctx=ctx)
    return out

def deep_get(obj, path, default=None):
    cur = obj
    for p in path.split("."):
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return default
    return cur
