V3.2 CLOSED-LOOP REPAIR EXPERIMENT

Purpose:
Run ONE LLM repair request on the verified B/closed-loop syntax failure from V3.1,
then run the SAME 8 behavioral tests locally.

IMPORTANT:
- Maximum LLM requests: 1
- The script stops if the API call fails.
- No other treatments are rerun.
- No new migration generation is performed.
- The existing V3.1 result is included in input.
- OPENROUTER_API_KEY is required.
- OPENROUTER_MODEL defaults to the model used previously.

PowerShell:
1. Open PowerShell in this folder.
2. Verify Flask:
   python -c "import flask; print('Flask:', flask.__version__)"
3. Set API key:
   $env:OPENROUTER_API_KEY="sk-or-v1-YOUR_KEY"
4. Optional model:
   $env:OPENROUTER_MODEL="openai/gpt-oss-20b:free"
5. Run ONCE:
   python runner\run_v32_repair.py

Output:
results\v32_closed_loop_repair_result.json

Upload that JSON here.

DO NOT run the old full benchmark.
