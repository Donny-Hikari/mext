from autocode.libs.mext import Mext

class ContextManager(Mext):
  def __init__(self, cfg):
    Mext.__init__(self)

    self.profile = self._load_template(cfg.prompts.profile)
    self.cfg = cfg
    self.set_params(
      profile=self.profile,
      ai=cfg.ai,
      prompts=cfg.prompt,
    )

  def _load_template(self, template_fn):
    return self._load_prompt(f"{self.cfg.dirs.prompt}/{template_fn}")
