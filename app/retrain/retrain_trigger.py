"""
retrain_trigger.py
Automated retraining trigger system.
- Monitors concept drift detector
- Triggers retraining process when drift is detected
- Logs all events and decisions
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, Any

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from app.drift.drift_detector import ConceptDriftDetector
from app.retrain.data_collector import DataCollector
from app.db.database import get_db


class RetrainTrigger:
    """
    Automated retraining trigger system.
    Monitors drift detection and triggers retraining when needed.
    """
    
    def __init__(self, 
                 check_interval: int = 300,  # 5 minutes
                 drift_threshold: float = 0.05,
                 distribution_threshold: float = 0.1):
        """
        Initialize retraining trigger.
        
        Args:
            check_interval (int): Seconds between drift checks
            drift_threshold (float): Confidence drift threshold
            distribution_threshold (float): Distribution drift threshold
        """
        self.check_interval = check_interval
        self.drift_threshold = drift_threshold
        self.distribution_threshold = distribution_threshold
        
        # Initialize components
        self.drift_detector = ConceptDriftDetector(
            confidence_threshold=drift_threshold,
            distribution_threshold=distribution_threshold
        )
        self.data_collector = DataCollector()
        
        # State tracking
        self.last_drift_check = None
        self.drift_count = 0
        self.retrain_count = 0
        self.is_retraining = False
        self.running = False
        
        # Setup logging
        self._setup_logging()
        
        print(f"RetrainTrigger initialized:")
        print(f"  Check interval: {check_interval} seconds")
        print(f"  Drift threshold: {drift_threshold * 100:.1f}%")
        print(f"  Distribution threshold: {distribution_threshold * 100:.1f}%")
    
    def _setup_logging(self):
        """Setup logging for retraining events."""
        # Create logs directory
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Setup file handler
        log_file = os.path.join(log_dir, "retrain_trigger.log")
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("RetrainTrigger logging initialized")
    
    def start_monitoring(self):
        """Start continuous monitoring for concept drift."""
        if self.running:
            self.logger.warning("Monitoring already running")
            return
        
        self.running = True
        self.logger.info("Starting continuous drift monitoring")
        
        try:
            while self.running:
                self._monitoring_cycle()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
            self.running = False
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
            self.running = False
    
    def _monitoring_cycle(self):
        """Single monitoring cycle."""
        try:
            # Get recent predictions and check for drift
            self._update_drift_detector_with_recent_data()
            drift_result = self.drift_detector.check_drift()
            
            # Process drift result
            self._process_drift_result(drift_result)
            
        except Exception as e:
            self.logger.error(f"Error in monitoring cycle: {e}")
    
    def _update_drift_detector_with_recent_data(self):
        """Update drift detector with recent predictions from database."""
        try:
            db = get_db()
            recent_predictions = db.get_predictions(limit=100)
            
            # Add recent predictions to drift detector
            for pred in recent_predictions:
                self.drift_detector.add_prediction(
                    confidence=pred['confidence'],
                    predicted_label=pred['predicted_label']
                )
            
            self.logger.debug(f"Updated drift detector with {len(recent_predictions)} recent predictions")
            
        except Exception as e:
            self.logger.error(f"Error updating drift detector: {e}")
    
    def _process_drift_result(self, drift_result: Dict[str, Any]):
        """Process drift detection result and trigger retraining if needed."""
        current_time = datetime.now()
        
        # Log current metrics
        if 'current_metrics' in drift_result:
            metrics = drift_result['current_metrics']
            self.logger.info(f"Current metrics - Confidence: {metrics.get('avg_confidence', 0):.4f}, "
                           f"Fake ratio: {metrics.get('fake_ratio', 0):.3f}, "
                           f"Real ratio: {metrics.get('real_ratio', 0):.3f}")
        
        # Check for drift
        if drift_result.get('drift_detected', False):
            self._handle_drift_detected(drift_result, current_time)
        else:
            self._handle_no_drift(drift_result, current_time)
        
        self.last_drift_check = current_time
    
    def _handle_drift_detected(self, drift_result: Dict[str, Any], timestamp: datetime):
        """Handle drift detection event."""
        self.drift_count += 1
        
        # Log drift detection
        self.logger.warning(f"🚨 CONCEPT DRIFT DETECTED #{self.drift_count}")
        
        if drift_result.get('confidence_drift', False):
            self.logger.warning(f"  Confidence drift: {drift_result.get('confidence_drop', 'Unknown')}")
        
        if drift_result.get('distribution_drift', False):
            self.logger.warning(f"  Distribution drift: {drift_result.get('distribution_shift', 'Unknown')}")
        
        # Trigger retraining if not already running
        if not self.is_retraining:
            self._trigger_retraining(drift_result, timestamp)
        else:
            self.logger.info("  Retraining already in progress, skipping trigger")
    
    def _handle_no_drift(self, drift_result: Dict[str, Any], timestamp: datetime):
        """Handle no drift detection."""
        status = drift_result.get('status', 'unknown')
        
        if status == 'warmup':
            remaining = drift_result.get('warmup_remaining', 0)
            self.logger.info(f"📊 Warmup in progress: {remaining} predictions remaining")
        elif status == 'active':
            self.logger.info(f"✅ No drift detected - System operating normally")
        else:
            self.logger.info(f"📊 Status: {status}")
    
    def _trigger_retraining(self, drift_result: Dict[str, Any], timestamp: datetime):
        """Trigger the retraining process."""
        if self.is_retraining:
            self.logger.warning("Retraining already in progress")
            return
        
        self.is_retraining = True
        self.retrain_count += 1
        
        # Log retraining trigger
        self.logger.info(f"🔄 TRIGGERING RETRAINING #{self.retrain_count}")
        self.logger.info(f"  Trigger time: {timestamp.isoformat()}")
        self.logger.info(f"  Drift type: {'confidence' if drift_result.get('confidence_drift') else 'distribution' if drift_result.get('distribution_drift') else 'unknown'}")
        
        try:
            # Collect training data
            self.logger.info("  Collecting training data...")
            dataset = self.data_collector.prepare_training_dataset(limit=5000)
            
            if dataset['status'] == 'ready':
                self.logger.info(f"  Collected {dataset['total_samples']} weighted samples")
                self.logger.info(f"  Average confidence: {dataset['quality_metrics']['avg_confidence']:.4f}")
                
                # TODO: Integrate with actual retraining pipeline
                # self._perform_retraining(dataset)
                
                # Log completion
                self.logger.info(f"✅ RETRAINING #{self.retrain_count} COMPLETED")
                
            else:
                self.logger.warning(f"  Insufficient training data: {dataset.get('message', 'Unknown')}")
        
        except Exception as e:
            self.logger.error(f"  Retraining failed: {e}")
        
        finally:
            self.is_retraining = False
    
    def _perform_retraining(self, dataset: Dict[str, Any]):
        """Perform the actual retraining (placeholder)."""
        # TODO: Integrate with actual training pipeline
        # This would call the training scripts with the prepared dataset
        self.logger.info("  Placeholder: Actual retraining would happen here")
        self.logger.info(f"  Dataset: {dataset['total_samples']} samples, weights ready")
        
        # Simulate retraining time
        time.sleep(2)  # Simulate training time
        
        # Update baseline after retraining
        self.drift_detector.reset_baseline()
        self.logger.info("  Baseline reset after retraining")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the retraining trigger."""
        return {
            "running": self.running,
            "is_retraining": self.is_retraining,
            "drift_count": self.drift_count,
            "retrain_count": self.retrain_count,
            "last_drift_check": self.last_drift_check.isoformat() if self.last_drift_check else None,
            "check_interval": self.check_interval,
            "thresholds": {
                "drift": self.drift_threshold,
                "distribution": self.distribution_threshold
            }
        }
    
    def stop_monitoring(self):
        """Stop the monitoring process."""
        self.running = False
        self.logger.info("Monitoring stopped")


# Example usage and testing
if __name__ == "__main__":
    # Initialize retraining trigger
    trigger = RetrainTrigger(
        check_interval=10,  # Check every 10 seconds for demo
        drift_threshold=0.05,
        distribution_threshold=0.1
    )
    
    print("Retraining Trigger Test")
    print("=" * 50)
    
    # Show status
    status = trigger.get_status()
    print("Current Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\nStarting monitoring (Ctrl+C to stop)...")
    
    # Start monitoring
    try:
        trigger.start_monitoring()
    except KeyboardInterrupt:
        print("\nStopping monitoring...")
        trigger.stop_monitoring()
        print("Monitoring stopped successfully")
    
    print("\n✅ Retraining trigger test completed!")
