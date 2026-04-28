#!/usr/bin/env python3
"""Verify CUDA availability in the backend environment."""
import sys

def main():
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA device count: {torch.cuda.device_count()}")
            print(f"CUDA device name: {torch.cuda.get_device_name(0)}")
            props = torch.cuda.get_device_properties(0)
            print(f"CUDA total memory: {props.total_memory / 1e9:.2f} GB")
            print(f"CUDA compute capability: {props.major}.{props.minor}")
            return 0
        else:
            print("ERROR: CUDA not available")
            return 1
    except ImportError as e:
        print(f"ERROR: PyTorch not installed: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())