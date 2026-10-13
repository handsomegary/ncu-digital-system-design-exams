"""Run Verilog testbenches in temporary directories, using Icarus Verilog."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def simulate(sources, bench, top='tb', timeout=60):
    compiler = os.environ.get('IVERILOG', 'iverilog')
    runtime = os.environ.get('VVP', 'vvp')
    if not shutil.which(compiler) or not shutil.which(runtime):
        raise RuntimeError('Install Icarus Verilog (iverilog and vvp); GitHub CI installs it automatically.')
    with tempfile.TemporaryDirectory(prefix='dsd_sim_') as name:
        folder = Path(name)
        source = folder / 'generated_tb.v'
        source.write_text(bench, encoding='utf-8')
        executable = folder / 'simulation.vvp'
        result = subprocess.run([compiler, '-g2012', '-Wall', '-s', top, '-o', str(executable),
                                 *[str(ROOT / path) for path in sources], str(source)],
                                text=True, capture_output=True, timeout=timeout)
        assert result.returncode == 0, result.stdout + result.stderr
        result = subprocess.run([runtime, str(executable)], text=True, capture_output=True, cwd=folder, timeout=timeout)
        assert result.returncode == 0, result.stdout + result.stderr
        assert 'PASS' in result.stdout, result.stdout + result.stderr
        return result.stdout.strip()
