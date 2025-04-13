from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os

class Memory:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        self.device_status_file = os.path.join(cache_dir, "device_status.json")
        self.conversation_file = os.path.join(cache_dir, "conversation.json")
        self._ensure_cache_dir()
        self._load_device_status()
        self._load_conversation()

    def _ensure_cache_dir(self):
        """Ensure the cache directory exists."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _load_device_status(self):
        """Load device status from cache file."""
        if os.path.exists(self.device_status_file):
            with open(self.device_status_file, 'r') as f:
                self.device_status = json.load(f)
        else:
            self.device_status = {}

    def _load_conversation(self):
        """Load conversation history from cache file."""
        if os.path.exists(self.conversation_file):
            with open(self.conversation_file, 'r') as f:
                self.conversation = json.load(f)
        else:
            self.conversation = []

    def save_device_status(self, device_name: str, status: Dict[str, Any]):
        """
        Save device status to memory.
        
        Args:
            device_name (str): Name of the device.
            status (Dict[str, Any]): Device status information.
        """
        self.device_status[device_name] = {
            "status": status,
            "last_updated": datetime.now().isoformat()
        }
        self._save_device_status()

    def get_device_status(self, device_name: str) -> Optional[Dict[str, Any]]:
        """
        Get device status from memory.
        
        Args:
            device_name (str): Name of the device.
            
        Returns:
            Optional[Dict[str, Any]]: Device status if found, None otherwise.
        """
        if device_name in self.device_status:
            return self.device_status[device_name]["status"]
        return None

    def add_conversation_entry(self, role: str, content: str):
        """
        Add a conversation entry to memory.
        
        Args:
            role (str): Role of the speaker (user/assistant).
            content (str): Content of the message.
        """
        self.conversation.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self._save_conversation()

    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """
        Get recent conversation history.
        
        Args:
            limit (int): Maximum number of entries to return.
            
        Returns:
            List[Dict[str, str]]: List of conversation entries.
        """
        return self.conversation[-limit:]

    def _save_device_status(self):
        """Save device status to cache file."""
        with open(self.device_status_file, 'w') as f:
            json.dump(self.device_status, f, indent=2)

    def _save_conversation(self):
        """Save conversation history to cache file."""
        with open(self.conversation_file, 'w') as f:
            json.dump(self.conversation, f, indent=2) 