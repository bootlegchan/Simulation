import uvicorn
from pathlib import Path
from src.core.path_utils import get_default_data_dir
from src.simulation.engine import SimulationEngine
from src.simulation.runner import SimulationRunner
from src.api.router import create_app

class APIServer:
    """Helper server manager for launching Uvicorn ASGI server."""

    def __init__(self, data_dir: Path = None, host: str = "127.0.0.1", port: int = 8000, target_tps: float = 10.0):
        self.data_dir = data_dir or get_default_data_dir()
        self.host = host
        self.port = port
        self.engine = SimulationEngine(self.data_dir)
        self.engine.initialize(seed=42)
        self.runner = SimulationRunner(self.engine, target_tps=target_tps)
        self.app = create_app(self.engine, self.runner)

    def run(self):
        self.runner.start_live_runner()
        print(f"Starting Social Simulation API Server at http://{self.host}:{self.port} ...")
        uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")

if __name__ == "__main__":
    server = APIServer()
    server.run()
