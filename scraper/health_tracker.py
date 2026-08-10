"""
Source Health Tracker — Tracks success and 403 blocks per source.
"""

import os
import json
from scraper.logger import get_logger

class SourceHealthTracker:
    def __init__(self, log_dir: str = "knowledge_base/logs"):
        self.log_dir = log_dir
        self.file_path = os.path.join(log_dir, "source_health.json")
        self.health = {}
        self._load()
        
    def _load(self):
        os.makedirs(self.log_dir, exist_ok=True)
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.health = json.load(f)
            except Exception:
                self.health = {}
                
    def _save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.health, f, indent=2)
        except Exception as e:
            get_logger().error("Could not save source_health.json: %s", str(e))
            
    def record_403(self, source_key: str):
        if source_key not in self.health:
            self.health[source_key] = {"403": 0, "success": 0, "disabled": False}
        self.health[source_key]["403"] = self.health[source_key].get("403", 0) + 1
        
        if self.health[source_key]["403"] >= 30:
            if not self.health[source_key].get("disabled", False):
                self.health[source_key]["disabled"] = True
                get_logger().warning("Source %s has reached 30 403s and is now DISABLED.", source_key)
                
        self._save()
        
    def record_success(self, source_key: str):
        if source_key not in self.health:
            self.health[source_key] = {"403": 0, "success": 0, "disabled": False}
        self.health[source_key]["success"] = self.health[source_key].get("success", 0) + 1
        self._save()
        
    def is_disabled(self, source_key: str) -> bool:
        if source_key not in self.health:
            return False
        return self.health[source_key].get("disabled", False)
