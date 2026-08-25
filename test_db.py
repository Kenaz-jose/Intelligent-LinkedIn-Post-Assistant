from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

# This will print the exact strings NVIDIA expects you to use
print(NVIDIAEmbeddings().available_models)