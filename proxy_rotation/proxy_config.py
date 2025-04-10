import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from colorama import Fore, Style

@dataclass
class ProxyConfig:
    """
    Configuration class for proxy settings.
    """
    ip: str
    port: str
    username: str
    password: str
    rotate_url: str
    name: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    isp: Optional[str] = None
    last_rotation_time: int = 0
    current_ip: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProxyConfig':
        """
        Create a ProxyConfig instance from a dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary containing proxy configuration
            
        Returns:
            ProxyConfig: A new ProxyConfig instance
        """
        return cls(
            ip=data.get('ip', ''),
            port=data.get('port', ''),
            username=data.get('username', ''),
            password=data.get('password', ''),
            rotate_url=data.get('rotate_url', ''),
            name=data.get('name'),
            country=data.get('country'),
            city=data.get('city'),
            isp=data.get('isp'),
            last_rotation_time=data.get('last_rotation_time', 0),
            current_ip=data.get('current_ip'),
            metadata=data.get('metadata', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the ProxyConfig instance to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the proxy configuration
        """
        return {
            'ip': self.ip,
            'port': self.port,
            'username': self.username,
            'password': self.password,
            'rotate_url': self.rotate_url,
            'name': self.name,
            'country': self.country,
            'city': self.city,
            'isp': self.isp,
            'last_rotation_time': self.last_rotation_time,
            'current_ip': self.current_ip,
            'metadata': self.metadata
        }
    
    def get_proxy_string(self) -> str:
        """
        Get the proxy string in the format username:password@ip:port.
        
        Returns:
            str: Formatted proxy string
        """
        return f"{self.username}:{self.password}@{self.ip}:{self.port}"
    
    def get_proxy_dict(self) -> Dict[str, str]:
        """
        Get the proxy configuration as a dictionary for requests library.
        
        Returns:
            Dict[str, str]: Proxy configuration for requests
        """
        proxy_string = self.get_proxy_string()
        return {
            'http': f'http://{proxy_string}',
            'https': f'http://{proxy_string}'
        }
    
    def __str__(self) -> str:
        """
        Get a string representation of the proxy configuration.
        
        Returns:
            str: String representation
        """
        location = []
        if self.country:
            location.append(self.country)
        if self.city:
            location.append(self.city)
        location_str = f" ({', '.join(location)})" if location else ""
        
        name_str = f" [{self.name}]" if self.name else ""
        
        return f"{self.ip}:{self.port}{location_str}{name_str}"


class ProxyConfigManager:
    """
    Manager class for handling proxy configurations.
    """
    
    def __init__(self, config_file: str = "proxy_config.json"):
        """
        Initialize the ProxyConfigManager.
        
        Args:
            config_file (str): Path to the proxy configuration file
        """
        self.config_file = config_file
        self.proxies: List[ProxyConfig] = []
        self.load_config()
    
    def load_config(self) -> None:
        """
        Load proxy configurations from the config file.
        """
        try:
            if not os.path.exists(self.config_file):
                print(f"{Fore.YELLOW}⚠️ Proxy config file not found: {self.config_file}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Creating sample proxy config file...{Style.RESET_ALL}")
                
                # Create a sample proxy config file
                sample_proxies = [
                    {
                        "ip": "45.79.156.193",
                        "port": "8527",
                        "username": "81QRQ8B9TNXA",
                        "password": "jQKBfOZC0v",
                        "rotate_url": "https://api.mountproxies.com/api/proxy/67f3afc999e9e63742ed5658/rotate_ip?api_key=a4f667e14ef53ce1f5bb0a39a42a2d3a&_gl=1*hsie7f*_gcl_au*MjE0NzQwMTg3Ni4xNzQyNzI5OTgz",
                        "name": "Sample Proxy",
                        "country": "US",
                        "city": "New York"
                    }
                ]
                
                with open(self.config_file, 'w') as f:
                    json.dump(sample_proxies, f, indent=2)
                
                print(f"{Fore.GREEN}✅ Created sample proxy config file: {self.config_file}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}⚠️ Please edit the file with your actual proxy information before running.{Style.RESET_ALL}")
                return
            
            with open(self.config_file, 'r') as f:
                proxy_data = json.load(f)
            
            self.proxies = [ProxyConfig.from_dict(data) for data in proxy_data]
            print(f"{Fore.GREEN}✅ Loaded {len(self.proxies)} proxies from {self.config_file}{Style.RESET_ALL}")
        
        except Exception as e:
            print(f"{Fore.RED}❌ Error loading proxy config: {str(e)}{Style.RESET_ALL}")
    
    def save_config(self) -> None:
        """
        Save proxy configurations to the config file.
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump([proxy.to_dict() for proxy in self.proxies], f, indent=2)
            
            print(f"{Fore.GREEN}✅ Saved {len(self.proxies)} proxies to {self.config_file}{Style.RESET_ALL}")
        
        except Exception as e:
            print(f"{Fore.RED}❌ Error saving proxy config: {str(e)}{Style.RESET_ALL}")
    
    def add_proxy(self, proxy: ProxyConfig) -> None:
        """
        Add a new proxy configuration.
        
        Args:
            proxy (ProxyConfig): The proxy configuration to add
        """
        self.proxies.append(proxy)
        self.save_config()
    
    def remove_proxy(self, proxy: ProxyConfig) -> None:
        """
        Remove a proxy configuration.
        
        Args:
            proxy (ProxyConfig): The proxy configuration to remove
        """
        self.proxies = [p for p in self.proxies if p.ip != proxy.ip or p.port != proxy.port]
        self.save_config()
    
    def get_proxy(self, index: int) -> Optional[ProxyConfig]:
        """
        Get a proxy configuration by index.
        
        Args:
            index (int): Index of the proxy configuration
            
        Returns:
            Optional[ProxyConfig]: The proxy configuration or None if not found
        """
        if 0 <= index < len(self.proxies):
            return self.proxies[index]
        return None
    
    def get_proxies(self) -> List[ProxyConfig]:
        """
        Get all proxy configurations.
        
        Returns:
            List[ProxyConfig]: List of all proxy configurations
        """
        return self.proxies
    
    def get_proxy_count(self) -> int:
        """
        Get the number of proxy configurations.
        
        Returns:
            int: Number of proxy configurations
        """
        return len(self.proxies) 