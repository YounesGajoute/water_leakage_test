"""
Data persistence and management
"""
import json
import os
import shutil
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

class DataManager:
    def __init__(self, settings_file: str = 'settings.json'):
        """
        Initialize data manager
        
        Args:
            settings_file: Path to settings file
        """
        self.settings_file = settings_file
        self.settings = {}
        self.test_results = []
        
        # Create data directories
        self._create_directories()
        
        # Load existing data
        self.load_settings()
        self.load_test_results()
    
    def _create_directories(self):
        """Create necessary directories"""
        try:
            os.makedirs('data/test_results', exist_ok=True)
            os.makedirs('data/backups', exist_ok=True)
            os.makedirs('logs', exist_ok=True)
        except Exception as e:
            print(f"Error creating directories: {e}")
    
    def load_settings(self) -> bool:
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    
                    # Ensure required structure
                    if 'references' not in loaded_settings:
                        loaded_settings['references'] = {}
                    if 'last_reference' not in loaded_settings:
                        loaded_settings['last_reference'] = None
                    if 'system_config' not in loaded_settings:
                        loaded_settings['system_config'] = {}
                        
                    self.settings = loaded_settings
                    print(f"Settings loaded from {self.settings_file}")
                    return True
            else:
                # Create default settings
                self.settings = self._get_default_settings()
                self.save_settings()
                print(f"Created new settings file at {self.settings_file}")
                return True
                
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.settings = self._get_default_settings()
            return False
    
    def save_settings(self) -> bool:
        """Save settings to file with backup"""
        try:
            # Create backup of existing file
            if os.path.exists(self.settings_file):
                backup_name = f"{self.settings_file}.backup_{int(time.time())}"
                shutil.copy2(self.settings_file, backup_name)
                
                # Keep only last 5 backups
                self._cleanup_backups()
            
            # Write settings with pretty formatting
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4, sort_keys=True)
            
            # Set proper permissions
            os.chmod(self.settings_file, 0o666)
            print(f"Settings saved to {self.settings_file}")
            return True
            
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def _get_default_settings(self) -> Dict:
        """Get default settings structure"""
        return {
            'references': {},
            'last_reference': None,
            'system_config': {
                'default_pressure_range': [0, 4.5],
                'default_position_range': [65, 200],
                'default_time_range': [0, 120],
                'motor_speed': 1000,
                'pressure_calibration': {
                    'offset': -0.579,
                    'multiplier': 1.286
                }
            },
            'ui_config': {
                'theme': 'default',
                'fullscreen': True,
                'auto_save': True
            }
        }
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set a setting value"""
        try:
            self.settings[key] = value
            return self.save_settings()
        except Exception as e:
            print(f"Error setting {key}: {e}")
            return False
    
    def get_references(self) -> Dict[str, Dict]:
        """Get all references"""
        return self.settings.get('references', {})
    
    def add_reference(self, ref_id: str, ref_data: Dict) -> bool:
        """Add a new reference"""
        try:
            if 'references' not in self.settings:
                self.settings['references'] = {}
            
            # Add timestamp
            ref_data['created_at'] = datetime.now().isoformat()
            ref_data['updated_at'] = datetime.now().isoformat()
            
            self.settings['references'][ref_id] = ref_data
            self.settings['last_reference'] = ref_id
            
            return self.save_settings()
            
        except Exception as e:
            print(f"Error adding reference {ref_id}: {e}")
            return False
    
    def update_reference(self, ref_id: str, ref_data: Dict) -> bool:
        """Update existing reference"""
        try:
            if ref_id not in self.settings.get('references', {}):
                return False
            
            # Preserve created_at, update updated_at
            if 'created_at' in self.settings['references'][ref_id]:
                ref_data['created_at'] = self.settings['references'][ref_id]['created_at']
            ref_data['updated_at'] = datetime.now().isoformat()
            
            self.settings['references'][ref_id] = ref_data
            return self.save_settings()
            
        except Exception as e:
            print(f"Error updating reference {ref_id}: {e}")
            return False
    
    def delete_reference(self, ref_id: str) -> bool:
        """Delete a reference"""
        try:
            if ref_id in self.settings.get('references', {}):
                del self.settings['references'][ref_id]
                
                # Clear last_reference if it was deleted
                if self.settings.get('last_reference') == ref_id:
                    self.settings['last_reference'] = None
                
                return self.save_settings()
            return False
            
        except Exception as e:
            print(f"Error deleting reference {ref_id}: {e}")
            return False
    
    def save_test_result(self, test_data: Dict) -> bool:
        """Save test result to file"""
        try:
            # Add timestamp and ID
            test_data['test_id'] = f"test_{int(time.time())}"
            test_data['saved_at'] = datetime.now().isoformat()
            
            # Save to daily file
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"data/test_results/results_{date_str}.json"
            
            # Load existing results for the day
            daily_results = []
            if os.path.exists(filename):
                try:
                    with open(filename, 'r') as f:
                        daily_results = json.load(f)
                except:
                    daily_results = []
            
            # Add new result
            daily_results.append(test_data)
            
            # Save updated results
            with open(filename, 'w') as f:
                json.dump(daily_results, f, indent=4)
            
            # Add to memory cache
            self.test_results.append(test_data)
            
            # Keep only last 100 results in memory
            if len(self.test_results) > 100:
                self.test_results = self.test_results[-100:]
            
            print(f"Test result saved: {test_data['test_id']}")
            return True
            
        except Exception as e:
            print(f"Error saving test result: {e}")
            return False
    
    def load_test_results(self, days: int = 7) -> List[Dict]:
        """Load recent test results"""
        try:
            results = []
            
            # Load results from last N days
            for i in range(days):
                date = datetime.now()
                date = date.replace(day=date.day - i)
                date_str = date.strftime("%Y-%m-%d")
                filename = f"data/test_results/results_{date_str}.json"
                
                if os.path.exists(filename):
                    try:
                        with open(filename, 'r') as f:
                            daily_results = json.load(f)
                            results.extend(daily_results)
                    except Exception as e:
                        print(f"Error loading {filename}: {e}")
            
            # Sort by timestamp (newest first)
            results.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
            self.test_results = results[:100]  # Keep last 100
            return self.test_results
            
        except Exception as e:
            print(f"Error loading test results: {e}")
            return []
    
    def get_test_statistics(self) -> Dict[str, Any]:
        """Get test statistics"""
        try:
            if not self.test_results:
                return {}
            
            completed_tests = [t for t in self.test_results if t.get('completed', False)]
            failed_tests = [t for t in self.test_results if not t.get('completed', True)]
            
            stats = {
                'total_tests': len(self.test_results),
                'completed_tests': len(completed_tests),
                'failed_tests': len(failed_tests),
                'success_rate': len(completed_tests) / len(self.test_results) * 100 if self.test_results else 0
            }
            
            if completed_tests:
                durations = [t.get('duration', 0) for t in completed_tests]
                pressures = [t.get('final_pressure', 0) for t in completed_tests]
                
                stats.update({
                    'avg_duration': sum(durations) / len(durations),
                    'avg_pressure': sum(pressures) / len(pressures),
                    'min_duration': min(durations),
                    'max_duration': max(durations)
                })
            
            return stats
            
        except Exception as e:
            print(f"Error calculating statistics: {e}")
            return {}
    
    def export_data(self, export_path: str) -> bool:
        """Export all data to specified path"""
        try:
            export_data = {
                'settings': self.settings,
                'test_results': self.test_results,
                'statistics': self.get_test_statistics(),
                'export_timestamp': datetime.now().isoformat()
            }
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=4)
            
            print(f"Data exported to {export_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting data: {e}")
            return False
    
    def _cleanup_backups(self):
        """Keep only the 5 most recent backup files"""
        try:
            import glob
            backup_files = glob.glob(f"{self.settings_file}.backup_*")
            if len(backup_files) > 5:
                # Sort by modification time and remove oldest
                backup_files.sort(key=os.path.getmtime)
                for old_backup in backup_files[:-5]:
                    os.remove(old_backup)
                    
        except Exception as e:
            print(f"Error cleaning up backups: {e}")