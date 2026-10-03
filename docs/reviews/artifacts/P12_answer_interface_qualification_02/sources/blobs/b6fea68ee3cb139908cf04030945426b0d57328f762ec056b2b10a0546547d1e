"""Pinned Qwen3 embedding adapter. No implicit network or truncation."""
from importlib.metadata import version

from .contracts import EncoderSettings, FailureCode, ProviderFailure

MODEL = 'Qwen/Qwen3-Embedding-0.6B'
REVISION = '97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3'


class QwenEncoder:
    def __init__(self, cache_dir, *, runtime_versions, device='cuda', load_model=True):
        import torch
        from transformers import AutoModel, AutoTokenizer
        from phi_jepa.models.context_projection import FrozenModule
        actual = {name: version(name) for name in ('torch', 'transformers', 'tokenizers', 'safetensors')}
        if actual != runtime_versions:
            raise ValueError('runtime does not match explicit dependency pins')
        self.settings = EncoderSettings(
            'local_transformers', MODEL, REVISION, REVISION,
            'qwen-p02b-v1:' + repr(sorted(actual.items())) + ':' + str(device),
            'last_nonpadding_token', 32768, 'bfloat16', 'l2_float32', 1024, 'local')
        self.device = torch.device(device)
        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL, revision=REVISION, cache_dir=cache_dir, padding_side='left',
            local_files_only=True, trust_remote_code=False)
        self.encoder = None
        if load_model:
            model = AutoModel.from_pretrained(
                MODEL, revision=REVISION, cache_dir=cache_dir, local_files_only=True,
                trust_remote_code=False, use_safetensors=True, torch_dtype=torch.bfloat16,
                attn_implementation='sdpa')
            if model.config.hidden_size != 1024 or model.config.max_position_embeddings < 32768:
                raise ValueError('unexpected selected encoder dimensions')
            self.encoder = FrozenModule(model.to(self.device))

    def tokenize(self, text):
        # Full canonical Q/C is treated as a document, without a retrieval-query
        # instruction, chat template, or model-generated summary.
        return tuple(self.tokenizer(text, add_special_tokens=True,
                                    truncation=False, padding=False)['input_ids'])

    def encode_tokens(self, tokens):
        import torch
        if self.encoder is None:
            raise ValueError('tokenizer-only adapter cannot encode')
        if not tokens or len(tokens) > self.settings.max_length:
            raise ProviderFailure(FailureCode.OVERLENGTH)
        ids = torch.tensor([tokens], dtype=torch.long, device=self.device)
        hidden = self.encoder(input_ids=ids, attention_mask=torch.ones_like(ids),
                              use_cache=False).last_hidden_state
        # Single unpadded input: the final index is the final nonpadding token.
        pooled = hidden[:, -1].float()
        normalized = torch.nn.functional.normalize(pooled, p=2, dim=1)
        return tuple(normalized[0].cpu().tolist())
