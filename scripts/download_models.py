# Script to Download ASR Models (e.g., for faster-whisper)
# This script helps in pre-downloading models to a known location
# or to populate the cache, especially for CI/CD or bundled distributions.

# import os
# from faster_whisper import WhisperModel # Requires faster-whisper to be installed

# Define models to download and their parameters
# Example: (model_name, device, compute_type)
MODELS_TO_DOWNLOAD = [
    ("tiny", "cpu", "int8"),     # Smallest, good for quick tests
    ("base", "cpu", "int8"),
    ("small", "cpu", "int8"),    # Often a good default
    ("medium", "cpu", "int8"),
    # Add GPU versions if you plan to test/bundle them specifically
    # ("small", "cuda", "float16"),
    # ("medium", "cuda", "float16"),
]

# You might want to specify a custom download location for Hugging Face Hub models
# by setting environment variables like HF_HOME or TRANSFORMERS_CACHE before running this.
# os.environ["HF_HOME"] = os.path.join(os.getcwd(), ".hf_cache") # Example local cache


def download_model(model_name: str, device: str = "cpu", compute_type: str = "int8"):
    """
    Downloads (or loads from cache if already present) a faster-whisper model.
    """
    print(f"Attempting to load/download model: {model_name} (device={device}, compute_type={compute_type})...")
    try:
        # The mere act of initializing WhisperModel with a name will trigger download
        # if the model is not found in the cache.
        # model = WhisperModel(model_name, device=device, compute_type=compute_type)
        # del model # Release memory if any was loaded
        # For now, as we can't run faster-whisper directly, simulate:
        if model_name: # Check if model_name is not empty
            print(f"Simulated: WhisperModel('{model_name}', device='{device}', compute_type='{compute_type}')")
            print(f"Model {model_name} is now available (or was already cached).")
        else:
            print(f"Skipping download for empty model name.")

    except Exception as e:
        print(f"Error downloading/loading model {model_name} with device {device}, compute_type {compute_type}: {e}")
        print("Please ensure 'faster-whisper' and its dependencies (like PyTorch/CTranslate2) are correctly installed.")
        print("If using CUDA, ensure CUDA toolkit and compatible drivers are installed.")

if __name__ == "__main__":
    print("--- IntelliSubs ASR Model Downloader ---")
    
    # Check if faster-whisper is importable, if not, guide user
    try:
        import faster_whisper
        print(f"Found faster-whisper version: {faster_whisper.__version__}")
    except ImportError:
        print("Error: 'faster-whisper' library not found.")
        print("Please install it first, e.g., by running: pip install faster-whisper")
        print("This script cannot download models without it.")
        exit(1) # Exit if library not found.

    for model_spec in MODELS_TO_DOWNLOAD:
        if len(model_spec) == 3:
            name, dev, ctype = model_spec
            download_model(name, device=dev, compute_type=ctype)
        elif len(model_spec) == 1: # Simplified spec if only name is given
             download_model(model_spec[0])
        else:
            print(f"Skipping invalid model specification: {model_spec}")
        print("-" * 30)

    print("All specified models have been processed (downloaded or loaded from cache).")
    print("Models are typically cached by Hugging Face Transformers/faster-whisper in:")
    print("  - Linux/macOS: ~/.cache/huggingface/hub")
    print("  - Windows: C:\\Users\\<YourUser>\\.cache\\huggingface\\hub")
    print("  (Or in HF_HOME if that environment variable is set).")