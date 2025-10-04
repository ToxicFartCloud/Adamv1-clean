#!/usr/bin/env bash
set -e

echo "🚀 Running Adam Plugin Integration Tests..."
echo "==========================================="

run_test () {
    local plugin=$1
    local args=$2
    echo -n "➤ Testing $plugin ... "
    if output=$(python run_adam.py --plugin "$plugin" --args "$args" 2>&1); then
        echo "✅ PASS"
        echo "   → Sample output: $(echo "$output" | head -n 1)"
    else
        echo "❌ FAIL"
        echo "   → Error: $output"
    fi
}

# 🔹 Agent tests
run_test agent_coder      '{"prompt":"Write a Python function that returns 42."}'
run_test agent_critic     '{"prompt":"def add(a,b): return a+b", "style":"pep8"}'
run_test agent_researcher '{"prompt":"Compare transformers vs RNNs", "depth":"summary"}'
run_test agent_tester     '{"prompt":"def add(a,b): return a+b", "framework":"pytest"}'
run_test creative_cortex  '{"prompt":"Write a short sci-fi story about a time-traveling cat."}'

echo "==========================================="
echo "🏁 All plugin integration tests completed."
