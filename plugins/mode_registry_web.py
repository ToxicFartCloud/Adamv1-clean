import requests
import json
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

def search_gguf_models(
    task: str = "text-generation",
    max_vram_gb: float = 10.0,
    quantizations: List[str] = None,
    limit: int = 20
) -> List[Dict]:
    """
    Search for GGUF models on HuggingFace Model Hub
    
    Args:
        task: Model task (e.g., 'text-generation', 'code')
        max_vram_gb: Maximum VRAM in GB
        quantizations: List of quantization formats (default: ['q4_k_m', 'q5_k_m'])
        limit: Maximum number of results to return
    
    Returns:
        List of model dictionaries with filtered/scored results
    """
    if quantizations is None:
        quantizations = ['q4_k_m', 'q5_k_m']
    
    url = "https://huggingface.co/api/models"
    params = {
        "search": "gguf",
        "filter": task,
        "sort": "downloads",
        "direction": -1,
        "limit": limit * 2  # Get more results to filter
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        models = response.json()
    except Exception as e:
        logger.error(f"API request failed: {e}")
        return []
    
    # Filter and enrich models
    filtered_models = []
    for model in models:
        try:
            # Check if it's a GGUF model
            if not is_gguf_model(model):
                continue
                
            # Get model files and filter by quantization
            files = get_model_files(model['id'])
            gguf_files = filter_gguf_files(files, quantizations)
            
            if not gguf_files:
                continue
                
            # Estimate VRAM requirements
            for file_info in gguf_files:
                vram_gb = estimate_vram_requirement(file_info)
                if vram_gb <= max_vram_gb:
                    enriched_model = {
                        **model,
                        'gguf_file': file_info,
                        'estimated_vram_gb': vram_gb,
                        'compatibility_score': calculate_compatibility_score(
                            model, file_info, max_vram_gb
                        )
                    }
                    filtered_models.append(enriched_model)
                    break  # Take first compatible file
        except Exception as e:
            logger.warning(f"Error processing model {model.get('id', 'unknown')}: {e}")
            continue
    
    # Sort by compatibility score and limit results
    filtered_models.sort(key=lambda x: x['compatibility_score'], reverse=True)
    return filtered_models[:limit]

def is_gguf_model(model: Dict) -> bool:
    """Check if model is GGUF format"""
    tags = model.get('tags', [])
    return 'gguf' in tags

def get_model_files(model_id: str) -> List[Dict]:
    """Get model files from HuggingFace API"""
    url = f"https://huggingface.co/api/models/{model_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('siblings', [])
    except Exception as e:
        logger.error(f"Failed to get files for {model_id}: {e}")
        return []

def filter_gguf_files(files: List[Dict], quantizations: List[str]) -> List[Dict]:
    """Filter GGUF files by quantization formats"""
    gguf_files = [
        f for f in files 
        if f.get('rfilename', '').endswith('.gguf')
    ]
    
    # Sort by preference (q5_k_m > q4_k_m)
    quant_order = {q: i for i, q in enumerate(reversed(quantizations))}
    
    def get_quant_priority(filename: str) -> int:
        for quant in quantizations:
            if quant.lower() in filename.lower():
                return quant_order[quant]
        return -1
    
    gguf_files.sort(
        key=lambda x: (
            get_quant_priority(x['rfilename']),
            -x.get('size', 0)  # Prefer larger files if same quant
        ),
        reverse=True
    )
    
    return gguf_files

def estimate_vram_requirement(file_info: Dict) -> float:
    """
    Estimate VRAM requirement based on file size
    Rough approximation: file_size * 1.2 (includes overhead)
    """
    size_bytes = file_info.get('size', 0)
    if size_bytes == 0:
        # Fallback estimation based on filename
        filename = file_info.get('rfilename', '')
        # Extract approximate parameter count from filename
        params_billion = extract_param_count(filename)
        # Rough estimate: 4 bytes per parameter for q4_k_m
        size_bytes = params_billion * 1e9 * 0.5
    
    # Convert to GB with 20% overhead
    return (size_bytes * 1.2) / (1024**3)

def extract_param_count(filename: str) -> float:
    """Extract approximate parameter count from filename"""
    import re
    # Match patterns like 7b, 13b, 30b, 65b, 70b
    match = re.search(r'(\d+\.?\d*)[bB]', filename)
    if match:
        return float(match.group(1))
    return 7.0  # Default to 7B parameters

def calculate_compatibility_score(
    model: Dict, 
    file_info: Dict, 
    max_vram_gb: float
) -> float:
    """
    Calculate compatibility score based on:
    1. Download count (popularity)
    2. VRAM efficiency
    3. Quantization preference
    4. Model recency
    """
    # Base score from downloads (logarithmic scale)
    downloads = model.get('downloads', 1)
    download_score = min(100, max(0, (math.log(downloads + 1) / math.log(100000)) * 100))
    
    # VRAM efficiency score (higher is better)
    vram_gb = estimate_vram_requirement(file_info)
    vram_efficiency = max(0, (max_vram_gb - vram_gb) / max_vram_gb) * 30
    
    # Quantization preference (q5 > q4)
    filename = file_info.get('rfilename', '')
    quant_bonus = 20 if 'q5' in filename.lower() else 10 if 'q4' in filename.lower() else 0
    
    # Recency bonus (newer models get preference)
    created_at = model.get('createdAt', '')
    recency_bonus = 0
    if created_at:
        try:
            from datetime import datetime
            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            days_old = (datetime.now(created_date.tzinfo) - created_date).days
            recency_bonus = max(0, (365 - days_old) / 365) * 10
        except Exception:
            pass
    
    return download_score + vram_efficiency + quant_bonus + recency_bonus

# Example usage
if __name__ == "__main__":
    import math
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Search for models
    models = search_gguf_models(
        task="text-generation",
        max_vram_gb=8.0,
        quantizations=['q4_k_m', 'q5_k_m'],
        limit=5
    )
    
    print(f"Found {len(models)} compatible models:")
    for i, model in enumerate(models, 1):
        print(f"\n{i}. {model['id']}")
        print(f"   Downloads: {model.get('downloads', 0):,}")
        print(f"   Estimated VRAM: {model['estimated_vram_gb']:.1f} GB")
        print(f"   File: {model['gguf_file']['rfilename']}")
        print(f"   Compatibility Score: {model['compatibility_score']:.1f}")
