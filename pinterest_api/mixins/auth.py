import urllib.parse
import hmac
import hashlib
from typing import Tuple, Optional, Dict

class AuthMixin:
    SECRET_KEY = "492124fd20e80e0f678f7a03344875f9b6234e2b"
    CLIENT_ID = "1431602"
    
    @staticmethod
    def custom_encode(s: str) -> str:
        """Mimic the Pinterest app's custom URL encoding."""
        encoded = urllib.parse.quote_plus(s, safe='')
        encoded = encoded.replace('+', '%20')
        encoded = encoded.replace('*', '%2A')
        encoded = encoded.replace('{', '%7B')
        encoded = encoded.replace('}', '%7D')
        encoded = encoded.replace('%7E', '~')
        return encoded

    @staticmethod
    def parse_raw_params(raw: Optional[str]) -> list:
        """Parse raw parameters into (key, value) tuples."""
        pairs = []
        if raw:
            for pair in raw.split('&'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    pairs.append((key, value))
                else:
                    pairs.append((pair, ''))
        return pairs

    def generate_login_signature(
        self, 
        method: str, 
        url: str, 
        raw_form_data: Optional[str] = None
    ) -> Tuple[str, str]:
        """Generate OAuth signature specifically for login endpoint."""
        parsed = urllib.parse.urlparse(url)
        raw_base_url = url.split('?')[0]
        encoded_base_url = urllib.parse.quote_plus(raw_base_url, safe='')
        
        raw_query = parsed.query
        query_pairs = self.parse_raw_params(raw_query)
        form_pairs = self.parse_raw_params(raw_form_data) if raw_form_data else []
        
        all_pairs = query_pairs + form_pairs
        sorted_pairs = sorted(all_pairs, key=lambda x: (x[0], x[1]))
        
        param_parts = []
        for key, value in sorted_pairs:
            param_parts.append(f"{key}={self.custom_encode(value)}")
        param_string = "&".join(param_parts)
        
        base_string = f"{method}&{encoded_base_url}&{param_string}"
        
        mac = hmac.new(
            self.SECRET_KEY.encode('utf-8'),
            base_string.encode('utf-8'),
            hashlib.sha256
        )
        signature = mac.hexdigest()
        
        for ch in [' ', '<', '>']:
            signature = signature.replace(ch, "")
            
        return signature, base_string

    def generate_email_check_signature(
        self,
        method: str,
        url: str
    ) -> Tuple[str, str]:
        """Generate OAuth signature specifically for email check endpoint."""
        parsed = urllib.parse.urlparse(url)
        
        # Use full URL (scheme + host + path) for base URL
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        encoded_base_url = urllib.parse.quote(base_url, safe='')

        # Extract and sort query parameters
        query_params = urllib.parse.parse_qs(parsed.query)
        sorted_keys = sorted(query_params.keys())
        
        param_parts = []
        for key in sorted_keys:
            for value in query_params[key]:
                encoded_key = urllib.parse.quote(key, safe='')
                encoded_value = urllib.parse.quote(value, safe='')
                param_parts.append(f"{encoded_key}={encoded_value}")
        
        param_string = "&".join(param_parts)
        base_string = f"{method}&{encoded_base_url}&{param_string}"
        
        signature = hmac.new(
            self.SECRET_KEY.encode('utf-8'),
            base_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature, base_string 