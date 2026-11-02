# Run Offline Comparative Evaluation Benchmark Experiments
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Executing Offline Comparative Benchmark Evaluation       " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"

Set-Location $BackendDir

python -c @"
import json
from app.services.experiment_runner import experiment_runner

print('[Experiment] Running benchmark across 15 labeled queries...')
report = experiment_runner.run_benchmark_experiment(threshold=0.55, top_k=3)

print('\n================ EXPERIMENT SUMMARY ================')
print(f'Total Queries: {report[\"num_queries\"]}')
print('\n[1] Baseline Method (Fixed Top-K=3):')
print(f'  Mean Precision: {report[\"baseline_top_k\"][\"mean_precision\"]:.2%}')
print(f'  Mean Recall:    {report[\"baseline_top_k\"][\"mean_recall\"]:.2%}')
print(f'  Mean F1 Score:  {report[\"baseline_top_k\"][\"mean_f1\"]:.4f}')
print(f'  Total Cases:    {report[\"baseline_top_k\"][\"total_retrieved\"]}')
print(f'  Irrelevant:     {report[\"baseline_top_k\"][\"total_irrelevant\"]}')

print('\n[2] Proposed Method (Adaptive Threshold theta=0.55):')
print(f'  Mean Precision: {report[\"adaptive_threshold\"][\"mean_precision\"]:.2%}')
print(f'  Mean Recall:    {report[\"adaptive_threshold\"][\"mean_recall\"]:.2%}')
print(f'  Mean F1 Score:  {report[\"adaptive_threshold\"][\"mean_f1\"]:.4f}')
print(f'  Total Cases:    {report[\"adaptive_threshold\"][\"total_retrieved\"]}')
print(f'  Irrelevant:     {report[\"adaptive_threshold\"][\"total_irrelevant\"]}')

print(f'\n[3] Noise Reduction: {report[\"irrelevant_noise_reduction_pct\"]}% fewer irrelevant cases injected!')
print(f'Detailed reports saved to: data/last_experiment_results.json and data/last_experiment_results.csv')
print('====================================================\n')
"@
