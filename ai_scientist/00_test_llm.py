"""
Test script for DeepSeek models (deepseek-chat and deepseek-reasoner) in AI Scientist
"""

import os
import sys
import json
import time
from typing import Dict, Any

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from ai_scientist.llm import (
        create_client,
        get_response_from_llm,
        get_batch_responses_from_llm,
        extract_json_between_markers,
        AVAILABLE_LLMS
    )
except ImportError as e:
    print(f"Error importing AI Scientist modules: {e}")
    print("Make sure you're running from the AI Scientist root directory")
    sys.exit(1)


class DeepSeekTester:
    def __init__(self):
        self.models_to_test = ["deepseek-chat", "deepseek-reasoner"]
        self.test_results = {}
        
    def check_prerequisites(self) -> bool:
        """Check if DEEPSEEK_API_KEY is available"""
        print("=" * 60)
        print("Checking Prerequisites")
        print("=" * 60)
        
        if "DEEPSEEK_API_KEY" not in os.environ:
            print("✗ DEEPSEEK_API_KEY environment variable not found")
            print("Please set your DeepSeek API key:")
            print("export DEEPSEEK_API_KEY=your_api_key_here")
            return False
        
        api_key = os.environ["DEEPSEEK_API_KEY"]
        if not api_key or len(api_key) < 10:
            print("✗ DEEPSEEK_API_KEY appears to be invalid")
            return False
            
        print("✓ DEEPSEEK_API_KEY found")
        
        # Check if models are in AVAILABLE_LLMS
        missing_models = []
        for model in self.models_to_test:
            if model not in AVAILABLE_LLMS:
                missing_models.append(model)
        
        if missing_models:
            print(f"✗ Models not in AVAILABLE_LLMS: {missing_models}")
            return False
        
        print("✓ All test models found in AVAILABLE_LLMS")
        return True
    
    def test_client_creation(self) -> bool:
        """Test client creation for DeepSeek models"""
        print("\n" + "=" * 60)
        print("Testing Client Creation")
        print("=" * 60)
        
        success = True
        for model in self.models_to_test:
            print(f"\nTesting client creation for {model}...")
            try:
                client, client_model = create_client(model)
                print(f"✓ Client created successfully for {model}")
                print(f"  - Client type: {type(client)}")
                print(f"  - Client model: {client_model}")
                
                # Store client for later tests
                if model not in self.test_results:
                    self.test_results[model] = {}
                self.test_results[model]["client"] = client
                self.test_results[model]["client_model"] = client_model
                self.test_results[model]["client_creation"] = True
                
            except Exception as e:
                print(f"✗ Failed to create client for {model}: {e}")
                success = False
                if model not in self.test_results:
                    self.test_results[model] = {}
                self.test_results[model]["client_creation"] = False
                self.test_results[model]["error"] = str(e)
        
        return success
    
    def test_simple_completion(self) -> bool:
        """Test simple text completion"""
        print("\n" + "=" * 60)
        print("Testing Simple Completion")
        print("=" * 60)
        
        test_prompt = "What is 2 + 2? Please answer concisely."
        system_message = "You are a helpful assistant. Provide brief, accurate answers."
        
        success = True
        for model in self.models_to_test:
            if not self.test_results.get(model, {}).get("client_creation", False):
                print(f"Skipping {model} - client creation failed")
                continue
                
            print(f"\nTesting simple completion for {model}...")
            try:
                client = self.test_results[model]["client"]
                
                start_time = time.time()
                response, msg_history = get_response_from_llm(
                    prompt=test_prompt,
                    client=client,
                    model=model,
                    system_message=system_message,
                    temperature=0.3
                )
                end_time = time.time()
                
                print(f"✓ Response received for {model}")
                print(f"  - Response time: {end_time - start_time:.2f} seconds")
                print(f"  - Response length: {len(response)} characters")
                print(f"  - Response preview: {response[:100]}...")
                print(f"  - Message history length: {len(msg_history)}")
                
                self.test_results[model]["simple_completion"] = True
                self.test_results[model]["response"] = response
                self.test_results[model]["response_time"] = end_time - start_time
                
            except Exception as e:
                print(f"✗ Simple completion failed for {model}: {e}")
                success = False
                self.test_results[model]["simple_completion"] = False
                self.test_results[model]["completion_error"] = str(e)
        
        return success
    
    def test_json_response(self) -> bool:
        """Test JSON-structured response"""
        print("\n" + "=" * 60)
        print("Testing JSON Response")
        print("=" * 60)
        
        test_prompt = """Please provide information about Python programming in the following JSON format:

```json
{
    "language": "Python",
    "version": "3.x",
    "features": ["easy to learn", "versatile", "large ecosystem"],
    "use_cases": ["web development", "data science", "automation"]
}
```

Make sure to follow the exact JSON format."""
        
        system_message = "You are a programming expert. Always respond with valid JSON when requested."
        
        success = True
        for model in self.models_to_test:
            if not self.test_results.get(model, {}).get("client_creation", False):
                print(f"Skipping {model} - client creation failed")
                continue
                
            print(f"\nTesting JSON response for {model}...")
            try:
                client = self.test_results[model]["client"]
                
                response, msg_history = get_response_from_llm(
                    prompt=test_prompt,
                    client=client,
                    model=model,
                    system_message=system_message,
                    temperature=0.1
                )
                
                # Try to extract JSON
                json_data = extract_json_between_markers(response)
                
                if json_data is not None:
                    print(f"✓ Valid JSON extracted for {model}")
                    print(f"  - JSON keys: {list(json_data.keys())}")
                    print(f"  - JSON data: {json.dumps(json_data, indent=2)}")
                    self.test_results[model]["json_response"] = True
                    self.test_results[model]["json_data"] = json_data
                else:
                    print(f"⚠ JSON extraction failed for {model}")
                    print(f"  - Raw response: {response[:200]}...")
                    self.test_results[model]["json_response"] = False
                
            except Exception as e:
                print(f"✗ JSON response test failed for {model}: {e}")
                success = False
                self.test_results[model]["json_response"] = False
                self.test_results[model]["json_error"] = str(e)
        
        return success
    
    def test_batch_responses(self) -> bool:
        """Test batch responses"""
        print("\n" + "=" * 60)
        print("Testing Batch Responses")
        print("=" * 60)
        
        test_prompt = "Name a color. Just one word."
        system_message = "You are a helpful assistant."
        n_responses = 3
        
        success = True
        for model in self.models_to_test:
            if not self.test_results.get(model, {}).get("client_creation", False):
                print(f"Skipping {model} - client creation failed")
                continue
                
            print(f"\nTesting batch responses for {model}...")
            try:
                client = self.test_results[model]["client"]
                
                responses, msg_histories = get_batch_responses_from_llm(
                    prompt=test_prompt,
                    client=client,
                    model=model,
                    system_message=system_message,
                    temperature=0.8,
                    n_responses=n_responses
                )
                
                print(f"✓ Batch responses received for {model}")
                print(f"  - Number of responses: {len(responses)}")
                print(f"  - Number of message histories: {len(msg_histories)}")
                
                for i, response in enumerate(responses):
                    print(f"  - Response {i+1}: {response.strip()[:50]}...")
                
                self.test_results[model]["batch_responses"] = True
                self.test_results[model]["batch_count"] = len(responses)
                
            except Exception as e:
                print(f"✗ Batch response test failed for {model}: {e}")
                success = False
                self.test_results[model]["batch_responses"] = False
                self.test_results[model]["batch_error"] = str(e)
        
        return success
    
    def test_reasoning_capability(self) -> bool:
        """Test reasoning capability (especially for deepseek-reasoner)"""
        print("\n" + "=" * 60)
        print("Testing Reasoning Capability")
        print("=" * 60)
        
        test_prompt = """Solve this step by step:
        
A farmer has 17 sheep. All but 9 die. How many sheep are left?

Please show your reasoning process."""
        
        system_message = "You are a logical reasoning expert. Always show your step-by-step thinking."
        
        success = True
        for model in self.models_to_test:
            if not self.test_results.get(model, {}).get("client_creation", False):
                print(f"Skipping {model} - client creation failed")
                continue
                
            print(f"\nTesting reasoning for {model}...")
            try:
                client = self.test_results[model]["client"]
                
                start_time = time.time()
                response, msg_history = get_response_from_llm(
                    prompt=test_prompt,
                    client=client,
                    model=model,
                    system_message=system_message,
                    temperature=0.1
                )
                end_time = time.time()
                
                print(f"✓ Reasoning response received for {model}")
                print(f"  - Response time: {end_time - start_time:.2f} seconds")
                print(f"  - Response length: {len(response)} characters")
                
                # Check if the answer contains "9" (correct answer)
                if "9" in response and ("left" in response.lower() or "remain" in response.lower()):
                    print(f"  - ✓ Appears to contain correct answer")
                else:
                    print(f"  - ⚠ May not contain correct answer")
                
                print(f"  - Response preview: {response[:300]}...")
                
                self.test_results[model]["reasoning"] = True
                self.test_results[model]["reasoning_response"] = response
                
            except Exception as e:
                print(f"✗ Reasoning test failed for {model}: {e}")
                success = False
                self.test_results[model]["reasoning"] = False
                self.test_results[model]["reasoning_error"] = str(e)
        
        return success
    
    def generate_report(self):
        """Generate a summary report"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY REPORT")
        print("=" * 60)
        
        for model in self.models_to_test:
            print(f"\n{model.upper()}:")
            print("-" * 40)
            
            if model not in self.test_results:
                print("  No test results available")
                continue
            
            results = self.test_results[model]
            
            # Test results
            tests = [
                ("Client Creation", "client_creation"),
                ("Simple Completion", "simple_completion"),
                ("JSON Response", "json_response"),
                ("Batch Responses", "batch_responses"),
                ("Reasoning", "reasoning")
            ]
            
            passed_tests = 0
            total_tests = len(tests)
            
            for test_name, test_key in tests:
                if test_key in results:
                    status = "✓ PASS" if results[test_key] else "✗ FAIL"
                    print(f"  {test_name:20}: {status}")
                    if results[test_key]:
                        passed_tests += 1
                else:
                    print(f"  {test_name:20}: - NOT RUN")
            
            print(f"\n  Overall: {passed_tests}/{total_tests} tests passed")
            
            # Performance metrics
            if "response_time" in results:
                print(f"  Response time: {results['response_time']:.2f}s")
        
        # Save detailed results to file
        report_file = "deepseek_test_results.json"
        try:
            with open(report_file, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            print(f"\nDetailed results saved to: {report_file}")
        except Exception as e:
            print(f"Failed to save results: {e}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("DeepSeek Model Testing Suite")
        print("Testing models:", self.models_to_test)
        print()
        
        if not self.check_prerequisites():
            print("\nPrerequisite check failed. Exiting.")
            return False
        
        test_methods = [
            self.test_client_creation,
            self.test_simple_completion,
            self.test_json_response,
            self.test_batch_responses,
            self.test_reasoning_capability,
        ]
        
        all_passed = True
        for test_method in test_methods:
            try:
                if not test_method():
                    all_passed = False
            except Exception as e:
                print(f"Test method {test_method.__name__} failed with exception: {e}")
                all_passed = False
        
        self.generate_report()
        
        if all_passed:
            print(f"\n🎉 All tests completed successfully!")
        else:
            print(f"\n⚠️  Some tests failed. Check the report above.")
        
        return all_passed


def main():
    """Main function"""
    tester = DeepSeekTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()