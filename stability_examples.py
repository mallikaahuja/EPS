"""
Example usage of both Stability AI API options

This file demonstrates how to use both the gRPC SDK (stability-sdk) and 
the REST API (stabilityai) packages for generating images.
"""

import os
from pathlib import Path

# ==========================================
# Option 1: Using stability-sdk (gRPC) - Current implementation
# ==========================================
def generate_with_grpc_sdk(prompt: str, component_name: str):
    """
    Generate image using the official gRPC SDK (current implementation)
    This is what the app.py currently uses
    """
    try:
        from stability_sdk import client
        
        STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
        if not STABILITY_API_KEY:
            raise ValueError("STABILITY_API_KEY environment variable not set")
        
        stability_client = client.StabilityInference(
            key=STABILITY_API_KEY,
            engine="stable-diffusion-xl-1024-v1-0",
            verbose=True,
        )
        
        answers = stability_client.generate(
            prompt=prompt,
            width=512,
            height=512,
            cfg_scale=7.0,
            steps=30,
            samples=1,
        )
        
        for resp in answers:
            for artifact in resp.artifacts:
                if artifact.finish_reason == 0:
                    continue
                if artifact.type == 1:
                    # Save to file
                    svg_path = Path("symbols") / f"{component_name}.png"
                    svg_path.parent.mkdir(exist_ok=True)
                    with open(svg_path, "wb") as f:
                        f.write(artifact.binary)
                    return str(svg_path)
        return None
        
    except ImportError:
        print("stability-sdk not installed. Run: pip install stability-sdk==0.6.1")
        return None
    except Exception as e:
        print(f"Error with gRPC SDK: {e}")
        return None

# ==========================================
# Option 2: Using stabilityai (REST API) - Modern alternative
# ==========================================
async def generate_with_rest_api(prompt: str, component_name: str):
    """
    Generate image using the modern REST API
    This is easier to use and more reliable
    """
    try:
        from stabilityai.client import AsyncStabilityClient
        from stabilityai.models import Sampler
        from PIL import Image
        
        STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
        if not STABILITY_API_KEY:
            raise ValueError("STABILITY_API_KEY environment variable not set")
        
        async with AsyncStabilityClient() as stability:
            results = await stability.text_to_image(
                text_prompt=prompt,
                width=512,
                height=512,
                cfg_scale=7.0,
                steps=30,
                sampler=Sampler.K_DPMPP_2M,
            )
            
            if results.artifacts:
                artifact = results.artifacts[0]
                
                # Save to file
                svg_path = Path("symbols") / f"{component_name}.png"
                svg_path.parent.mkdir(exist_ok=True)
                
                img = Image.open(artifact.file)
                img.save(svg_path)
                return str(svg_path)
        
        return None
        
    except ImportError:
        print("stabilityai not installed. Run: pip install stabilityai>=1.0.0")
        return None
    except Exception as e:
        print(f"Error with REST API: {e}")
        return None

# ==========================================
# Example usage in your app
# ==========================================
def generate_symbol_svg(component_name: str, prompt: str) -> str:
    """
    Updated version of the generate_symbol_svg function from app.py
    Try the modern REST API first, fallback to gRPC SDK
    """
    print(f"Generating symbol for: {component_name}")
    
    # Try REST API first (modern, easier to use)
    try:
        import asyncio
        result = asyncio.run(generate_with_rest_api(prompt, component_name))
        if result:
            print(f"Generated using REST API: {result}")
            return result
    except Exception as e:
        print(f"REST API failed: {e}")
    
    # Fallback to gRPC SDK (current implementation)
    try:
        result = generate_with_grpc_sdk(prompt, component_name)
        if result:
            print(f"Generated using gRPC SDK: {result}")
            return result
    except Exception as e:
        print(f"gRPC SDK failed: {e}")
    
    print("Both APIs failed")
    return None

if __name__ == "__main__":
    # Example usage
    import asyncio
    
    # Set your API key
    # os.environ["STABILITY_API_KEY"] = "your_api_key_here"
    
    # Test prompt
    test_prompt = "Simple black and white line drawing of a valve symbol for P&ID diagram"
    test_component = "test_valve"
    
    print("Testing Stability AI integration...")
    print("Note: Set STABILITY_API_KEY environment variable to test")
    
    # This would generate a symbol if API key is set
    result = generate_symbol_svg(test_component, test_prompt)
    if result:
        print(f"Success! Generated: {result}")
    else:
        print("Failed to generate symbol (API key may not be set)")