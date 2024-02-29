# From:
# https://www.youtube.com/watch?v=Coj72EzmX20

# Install ubuntu22.04
# Install conda
# https://thesecmaster.com/step-by-step-guide-to-install-conda-on-ubuntu-linux/Z

sudo apt install -y build-essential

export PIP_EXTRA_INDEX_URL="https://download.pytorch.org/whl/cu121 https://huggingface.github.io/autogptq-index/whl/cu121"

git clone https://github.com/h2oai/h2ogpt.git
cd h2ogpt
pip install -r requirements.txt
pip install -r reqs_optional/requirements_optional_langchain.txt

# default uses cu121, for cu118, comment out cu121 and comment in similar cu118 wheels
# for no avx, comment-out avx wheels and choose ones without avx
# for AMD ROC, comment-out all except the correct ROC wheel
pip install -r reqs_optional/requirements_optional_gpt4all.txt

pip install -r reqs_optional/requirements_optional_langchain.urls.txt
# GPL, only run next line if that is ok:
# pip install -r reqs_optional/requirements_optional_langchain.gpllike.txt

# python generate.py --base_model=TheBloke/zephyr-7B-beta-GGUF --prompt_type=zephyr --max_seq_len=4096

python generate.py --base_model=h2oai/h2ogpt-gm-oasst1-en-2048-falcon-7b-v3 --score_model=None --prompt_type=human_bot --cli=True --load_8bit=True


# Using this middle model
# https://huggingface.co/h2oai/h2ogpt-gm-oasst1-en-2048-falcon-7b-v3
# Used this one for another : https://huggingface.co/TheBloke/Llama-2-7b-Chat-GGUF/resolve/main/llama-2-7b-chat.Q6_K.gguf
