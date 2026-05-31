'''
A tool that reads your YAML file and converts it into Python dictionaries
    1. Find and read rag_config.yaml file
    2. Converts YAML to Python dictionary
    3. Handles errors (file missing, invalid YAML)
    4. Makes config available to all other files 
'''

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dotenv import load_dotenv

# CUSTOM EXCEPTIONS
class ConfigError(Exception):
    '''Custom exception for configuration errors.'''
    
    pass

# CONFIGURATION LOADER CLASS
class ConfigLoader:
    '''
    Loads and provides access to configuration settings.
    Single place to manage all RAG service settings.
    '''
    
    #Initializes the loader
    def __init__(self, config_path: Optional[Union[str, Path]]=None):
        '''
        Initialize the configuration loader.
        
        ARGS:
            config_path: Path to YAML file (optional)
            If not provided, uses default location.
        
        RAISES:
            ConfigError: If config file not found or YAML is invalid
        '''
        
        # Load .env file
        env_path = Path(__file__).resolve().parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            print(f'Loaded .env from successfully: {env_path}')
        
        else:
            print(f'.env file not found: {env_path}')
        
        # Determine the config file path
        if config_path is None:
            base_dir = Path(__file__).resolve().parent.parent
            self.config_path = base_dir / 'config' / 'rag_config.yaml'
            
        else:
            # Use user-provided path
            self.config_path = Path(config_path)
            
        # Load the configuration
        try:
            self.config = self._load_config()
            print(f'Config loaded from: {self.config_path}')
            
        except ConfigError as e:
            raise ConfigError(f'Failed to load config: {e}')
        
        #Expand environment variables (API keys)
        self._expand_env_vars()
        
    # Load YAML file
    def _load_config(self) -> Dict[str, Any]:
        '''Load and parse the YAML configuration file.'''
        
        if not self.config_path.exists():
            raise ConfigError(
                f'Configuration file not found at: {self.config_path}\n'
                'Please ensure rag_config.yaml exists in the config folder.'
            )
            
        # Read and parse YAML
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file) # converts yaml text to dict

            # Check if YAML file is empty
            if config is None:
                raise ConfigError('Configuration file is empty')
            
            return config
        
        except Exception as e:
            raise ConfigError(f'Unexpected error loading config: {e}')

    def _expand_env_vars(self):
        '''
        Replace environment variable names with actual values.
        API keys come from .env file, not YAML.
        '''
        if 'openai' in self.config and 'api_key_env' in self.config['openai']:
            env_var = self.config['openai']['api_key_env']
            api_key = os.getenv(env_var, '')
            self.config['openai']['api_key'] = api_key
            
            if api_key:
                print('OpenAI API key found')
            else:
                print('OpenAI API key is missing (add to .env file)')
        
        if 'groq' in self.config and 'api_key_env' in self.config['groq']:
            env_var = self.config['groq']['api_key_env']
            api_key = os.getenv(env_var, '')
            self.config['groq']['api_key'] = api_key
            
            if api_key:
                print('Groq API key found')
            else:
                print('Groq API key is missing (add to .env file)')
    
config_loader = ConfigLoader()
config = config_loader.config

if __name__=='__main__':
    print('CONFIGURATION LOADER TEST')
    
    print('Config Access:')
    print(f"App name: {config['app']['name']}")
    print(f"App port: {config['app']['port']}")
    print(f"Default LLM: {config['llm']['default_provider']}")
    
    for lang in config['languages']['supported']:
        print(f"    - {lang['code']}: {lang['name']}")