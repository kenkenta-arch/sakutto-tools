import sys, json
from huggingface_hub import hf_hub_download
from style_bert_vits2.nlp import bert_models
from style_bert_vits2.constants import Languages
from style_bert_vits2.tts_model import TTSModel
import soundfile as sf
_bm = bert_models.load_model(Languages.JP, "ku-nlp/deberta-v2-large-japanese-char-wwm"); _bm.float()
bert_models.load_tokenizer(Languages.JP, "ku-nlp/deberta-v2-large-japanese-char-wwm")
MODELS = {"F1":"jvnv-F1-jp/jvnv-F1-jp_e160_s14000.safetensors","F2":"jvnv-F2-jp/jvnv-F2_e166_s20000.safetensors","M1":"jvnv-M1-jp/jvnv-M1-jp_e158_s14000.safetensors","M2":"jvnv-M2-jp/jvnv-M2-jp_e159_s17000.safetensors"}
def get(k):
    mf = MODELS[k]; d = mf.split('/')[0]
    m = hf_hub_download("litagin/style_bert_vits2_jvnv", mf)
    c = hf_hub_download("litagin/style_bert_vits2_jvnv", f"{d}/config.json")
    s = hf_hub_download("litagin/style_bert_vits2_jvnv", f"{d}/style_vectors.npy")
    t = TTSModel(model_path=m, config_path=c, style_vec_path=s, device="cpu"); t.load()
    t._TTSModel__net_g.float()
    return t
if __name__ == "__main__":
    jobs = json.loads(sys.argv[1])  # [{"voice":"F1","text":"..","out":"x.wav","style":"Neutral","length":1.0}]
    cache = {}
    for j in jobs:
        t = cache.setdefault(j["voice"], get(j["voice"]))
        sr, a = t.infer(text=j["text"], style=j.get("style", "Neutral"), length=j.get("length", 1.0), sdp_ratio=j.get("sdp", 0.3))
        sf.write(j["out"], a, sr); print("ok", j["out"], round(len(a)/sr, 2))
