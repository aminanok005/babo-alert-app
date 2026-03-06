# metrics/tracking.py

from typing import Dict, Any, Optional, List
from datetime import datetime


class IslamicContentMetrics:
    """ติดตามประสิทธิภาพเนื้อหา"""
    
    def __init__(self):
        self.content_history: List[Dict[str, Any]] = []
    
    def track_video_performance(self, video_id: str):
        """ติดตาม performance ของวิดีโอ"""
        metrics = {
            "video_id": video_id,
            "views": 0,
            "watch_time": 0,
            "engagement_rate": 0,
            "conversion_to_prayer": 0,  # วัดจาก CTA
            "shares": 0,
            "likes": 0,
            "comments": 0,
            "avg_watch_percentage": 0,
            "tracked_at": datetime.now().isoformat()
        }
        return metrics
    
    def analyze_content_effectiveness(
        self, 
        topic: str,
        character: str,
        metrics: dict
    ) -> Dict[str, Any]:
        """
        วิเคราะห์ว่าตัวละคร + หัวข้อได้ผลดีที่สุด
        
        Args:
            topic: หัวข้อของเนื้อหา
            character: ชื่อตัวละครที่ใช้
            metrics: dict ของ metrics จาก track_video_performance
            
        Returns:
            dict: ผลการวิเคราะห์ รวมถึง effectiveness score
        """
        
        # Calculate weighted effectiveness score
        weights = {
            "views": 0.2,
            "engagement_rate": 0.25,
            "shares": 0.2,
            "avg_watch_percentage": 0.25,
            "conversion_to_prayer": 0.1
        }
        
        # Get metric values with defaults
        views = metrics.get("views", 0)
        engagement_rate = metrics.get("engagement_rate", 0)
        shares = metrics.get("shares", 0)
        watch_pct = metrics.get("avg_watch_percentage", 0)
        conversion = metrics.get("conversion_to_prayer", 0)
        
        # Normalize views to 0-100 scale (assuming 10K views = max)
        normalized_views = min((views / 10000) * 100, 100)
        
        # Calculate weighted score
        effectiveness_score = (
            normalized_views * weights["views"] +
            engagement_rate * weights["engagement_rate"] +
            shares * 2 * weights["shares"] +  # Shares weighted higher
            watch_pct * weights["avg_watch_percentage"] +
            conversion * weights["conversion_to_prayer"]
        )
        
        # Determine effectiveness level
        if effectiveness_score >= 75:
            effectiveness_level = "excellent"
        elif effectiveness_score >= 50:
            effectiveness_level = "good"
        elif effectiveness_score >= 25:
            effectiveness_level = "fair"
        else:
            effectiveness_level = "needs_improvement"
        
        return {
            "topic": topic,
            "character": character,
            "effectiveness_score": effectiveness_score,
            "effectiveness_level": effectiveness_level,
            "component_scores": {
                "views_score": normalized_views * weights["views"],
                "engagement_score": engagement_rate * weights["engagement_rate"],
                "shares_score": shares * 2 * weights["shares"],
                "watch_time_score": watch_pct * weights["avg_watch_percentage"],
                "conversion_score": conversion * weights["conversion_to_prayer"]
            }
        }
